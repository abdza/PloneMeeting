## Controller Python Script "copy_items"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=Copy object from a folder to the clipboard
##

from Products.CMFPlone.utils import transaction_note
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _
from OFS.CopySupport import CopyError
from AccessControl import Unauthorized

REQUEST = context.REQUEST

mtool = getToolByName(context, 'portal_membership')
if not mtool.checkPermission('Copy or Move', context):
    msg = _(u'Permission denied to copy ${title}.',
            mapping={u'title' : context.title_or_id()})
    raise Unauthorized, msg

parent = context.aq_inner.aq_parent
try:
    parent.manage_copyObjects(context.getId(), REQUEST)
except CopyError:
    message = _(u'${title} is not copyable.',
                mapping={u'title' : context.title_or_id()})
    context.plone_utils.addPortalMessage(message)
    return state.set(status = 'failure')

message = _(u'${title} copied.',
            mapping={u'title' : context.title_or_id()})
transaction_note('Copied object %s' % context.absolute_url())

context.plone_utils.addPortalMessage(message)
return state.set(status = 'success')
