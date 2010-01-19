## Python Script "delete_givenuid.py"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=selected_uid
##title=Deletes an object

rq = context.REQUEST
# Get the logger
import logging
from AccessControl import Unauthorized

logger = logging.getLogger('PloneMeeting')
user = context.portal_membership.getAuthenticatedMember()

# Get the object to delete
obj = context.uid_catalog(UID=selected_uid)[0].getObject()
objectUrl = obj.absolute_url()
parent = obj.getParentNode()
grandParent = None

# Determine if the object can be deleted or not
if obj.meta_type == 'MeetingFile':
    item = obj.getItem()
    mayDelete = True
    if item:
        mayDelete = item.wfConditions().mayDeleteAnnex(obj)
else:
    try:
        mayDelete = obj.wfConditions().mayDelete()
    except AttributeError, ae:
        mayDelete = True

# Delete the object if allowed
removeParent = False
if mayDelete:
    msg = 'object_deleted'
    logMsg = '"%s" object entitled "%s" was deleted by user "%s"' % \
             (obj.meta_type, obj.Title(), user.id)
    # In the case of a meeting item, delete annexes & advices, too.
    if obj.meta_type == 'MeetingItem':
        obj.removeAllAnnexes()
        obj.removeAllAdvices()
    elif obj.meta_type == 'MeetingFile':
        item = obj.getItem()
        if item:
            item.updateAnnexIndex(obj, removeAnnex=True)
            item.updateHistory(
                'delete', obj, decisionRelated=obj.isDecisionRelated())
    elif obj.meta_type == 'MeetingAdvice':
        item = obj.getMeetingItem()
        if item:
            item.updateAdviceIndex(obj, removeAdvice=True)
    elif obj.meta_type == 'Meeting':
        if rq.get('wholeMeeting', None):
            # Delete all items in the meeting
            for item in obj.getItems():
                logger.info('Removing item "%s"...' % item.id)
                obj.removeGivenObject(item)
            for item in obj.getLateItems():
                logger.info('Removing item "%s"...' % item.id)
                obj.removeGivenObject(item)
            if obj.getParentNode().id == obj.id:
                # We are on an archive site, and the meeting is in a folder
                # that we must remove, too.
                removeParent = True
                grandParent = parent.getParentNode()

    # Do a final check before calling a Manager proxy roled script
    # this is done because we want to workaround a Plone design strange
    # behaviour where a user needs to have the 'Delete objects' permission
    # on the object AND on his container to be able to remove the object.
    # if we check that we can really remove it, call a script to do the
    # work. This just to be sure that we have "Delete objects" on the container.
    if user.has_permission("Delete objects", obj):
        try:
            context.removeGivenObject(obj)
            logger.info(logMsg)
            if removeParent: context.removeGivenObject(parent)
        except Exception, e:
            # Catch here Exception like BeforeDeleteException
            msg = e
    else:
        raise Unauthorized
else:
    msg = 'cant_delete_object'

# Redirect the user to the correct page and display the correct message.
refererUrl = rq['HTTP_REFERER']
if not refererUrl.startswith(objectUrl):
    urlBack = refererUrl
else:
    # We can't come back to where we came from, because it was deleted. So we
    # come back to:
    # - the PloneMeeting folder view as defined in the meeting config
    # - or the containing folder if the deleted object was an item created in
    #   portal_plonemeeting
    if 'portal_plonemeeting' in refererUrl:
        urlBack = parent.absolute_url()
    else:
        if grandParent:
            urlBack = grandParent.meeting_folder_view(grandParent)
        else:
            urlBack = parent.meeting_folder_view(parent)

# Remove previous message if one was there
i = urlBack.find('portal_status_message')
if i != -1:
    urlBack = urlBack[:i].strip('?&')

# Add the message to the urlBack
sep = '/?'
if urlBack.find('?') != -1:
    sep = '&'
urlBack = '%s%sportal_status_message=%s' % (urlBack, sep, msg)

return rq.RESPONSE.redirect(urlBack)
