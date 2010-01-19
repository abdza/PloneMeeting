# -*- coding: utf-8 -*-
#
# Copyright (c) 2007 by PloneGov
#
# GNU General Public License (GPL)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#

import os, re, urlparse, os.path, socket
from appy.shared.xml_parser import XmlMarshaller
from DateTime import DateTime
from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName
from Products.MailHost.MailHost import MailHostError
from Products.Archetypes.Marshall import Marshaller
from Products.CMFCore.permissions import View, AccessContentsInformation, \
     ModifyPortalContent, ReviewPortalContent, DeleteObjects
import Products.PloneMeeting
from Products.PloneMeeting.config import *
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.interfaces import *
import logging
logger = logging.getLogger('PloneMeeting')

# PloneMeetingError-related constants ------------------------------------------
WRONG_INTERFACE_NAME = 'Wrong interface name "%s". You must specify the full ' \
                       'interface package name.'
WRONG_INTERFACE_PACKAGE = 'Could not find package "%s".'
WRONG_INTERFACE = 'Interface "%s" not found in package "%s".'

# ------------------------------------------------------------------------------
monthsIds = {1:  'month_jan', 2:  'month_feb', 3:  'month_mar', 4:  'month_apr',
             5:  'month_may', 6:  'month_jun', 7:  'month_jul', 8:  'month_aug',
             9:  'month_sep', 10: 'month_oct', 11: 'month_nov', 12: 'month_dec'}

weekdaysIds = {0: 'weekday_sun', 1: 'weekday_mon', 2: 'weekday_tue',
               3: 'weekday_wed', 4: 'weekday_thu', 5: 'weekday_fri',
               6:'weekday_sat'}

adaptables = {
    'MeetingItem' : {'method':'getItem', 'interface':IMeetingItemCustom},
    'Meeting' : {'method':'getMeeting', 'interface':IMeetingCustom},
    'MeetingAdvice' : {'method':'getAdvice', 'interface':IMeetingAdviceCustom},
    # No (condition or action) workflow-related adapters are defined for the
    # following content types; only a Custom adapter.
    'MeetingCategory': {'method':None, 'interface':IMeetingCategoryCustom},
    'ExternalApplication':
        {'method':None, 'interface':IExternalApplicationCustom},
    'MeetingAdviceAgreementLevel':
        {'method':None, 'interface':IMeetingAdviceAgreementLevelCustom},
    'MeetingConfig': {'method':None, 'interface':IMeetingConfigCustom},
    'MeetingFile': {'method':None, 'interface':IMeetingFileCustom},
    'MeetingFileType': {'method':None, 'interface':IMeetingFileTypeCustom},
    'MeetingGroup': {'method':None, 'interface':IMeetingGroupCustom},
    'PodTemplate': {'method':None, 'interface':IPodTemplateCustom},
    'ToolPloneMeeting': {'method':None, 'interface':IToolPloneMeetingCustom},
    'MeetingUser': {'method':None, 'interface':IMeetingUserCustom},
}

def getInterface(interfaceName):
    '''Gets the interface named p_interfaceName.'''
    elems = interfaceName.split('.')
    if len(elems) < 2:
        raise PloneMeetingError(WRONG_INTERFACE_NAME % interfaceName)
    interfaceName = elems[len(elems)-1]
    packageName = ''
    for elem in elems[:-1]:
        if not packageName:
            point = ''
        else:
            point = '.'
        packageName += '%s%s' % (point, elem)
    try:
        exec 'import %s' % packageName
        exec 'res = %s.%s' % (packageName, interfaceName)
        return res
    except ImportError:
        raise PloneMeetingError(WRONG_INTERFACE_PACKAGE % packageName)
    except AttributeError:
        raise PloneMeetingError(WRONG_INTERFACE % (interfaceName, packageName))

def getWorkflowAdapter(obj, conditions):
    '''Gets the adapter, for a PloneMeeting object that proposes methods that
       may be used as workflow conditions (if p_conditions is True) or actions
       (if p_condition is False).'''
    tool = getToolByName(obj, TOOL_ID)
    meetingConfig = tool.getMeetingConfig(obj)
    interfaceMethod = adaptables[obj.meta_type]['method']
    if conditions:
        interfaceMethod += 'Conditions'
    else:
        interfaceMethod += 'Actions'
    exec 'interfaceLongName = meetingConfig.%sInterface()' % interfaceMethod
    return getInterface(interfaceLongName)(obj)

def getCustomAdapter(obj):
    '''Tries to get the custom adapter for a PloneMeeting object. If no adapter
       is defined, returns the object.'''
    res = obj
    theInterface = adaptables[obj.meta_type]['interface']
    try:
        res = theInterface(obj)
    except TypeError:
        pass
    return res

def getCurrentMeetingObject(context):
    '''What is the object currently published by Plone ?'''
    obj = context.REQUEST.get('PUBLISHED')
    className = obj.__class__.__name__
    if not (className in ('Meeting', 'MeetingItem')):
        if className in ('FSPythonScript', 'FSControllerPythonScript'):
            # We are changing the state of an element. We must then check the
            # referer
            refererUrl = context.REQUEST.get('HTTP_REFERER')
            referer = urlparse.urlparse(refererUrl)[2]
            if referer.endswith('_view') or referer.endswith('_edit'):
                referer = os.path.dirname(referer)
            # We add the portal path if necessary
            # (in case Apache rewrites the uri for example)
            portal_path = context.portal_url.getPortalPath()
            if not referer.startswith(portal_path):
                # The rewrite rule has modified the URL. First, remove any
                # added URL prefix.
                if referer.find('/Members/') != -1:
                    referer = referer[referer.index('/Members/'):]
                # Then, add the real portal as URL prefix.
                referer = portal_path + referer
            res = context.portal_catalog(path=referer)
            if res:
                obj = res[0].getObject()
        else:
            # Check the parent (if it has sense)
            if hasattr(obj, 'getParentNode'):
                obj = obj.getParentNode()
                if not (obj.__class__.__name__ in ('Meeting', 'MeetingItem')):
                    obj = None
            else:
                # It can be a method with attribute im_class
                obj = None
    return obj

def getOsTempFolder():
    tmp = '/tmp'
    if os.path.exists(tmp) and os.path.isdir(tmp):
        res = tmp
    elif os.environ.has_key('TMP'):
        res = os.environ['TMP']
    elif os.environ.has_key('TEMP'):
        res = os.environ['TEMP']
    else:
        raise "Sorry, I can't find a temp folder on your machine."
    return res

# How to know if a Kupu field is "empty" ---------------------------------------
KUPU_EMPTY_VALUES = ('<p></p>', '<p><br /></p>', '<p><br/></p>', '<br/>',
                     '<br />', '<p/>', '<p />')

def kupuFieldIsEmpty(kupuContent):
    res = False
    if (not kupuContent) or (kupuContent.strip() in KUPU_EMPTY_VALUES):
        res = True
    return res

def kupuEquals(fieldContent, valueFromDomParsing):
    '''Is the content of Kupu field p_fieldContent equal to
       p_valueFromDomString? The latter is not a str but unicode;
       differences like <br/> and <br />  and some whitespace are
       ignored.'''
    v1 = fieldContent.strip().replace('<br />', '<br/>')
    v2 = valueFromDomParsing.encode('utf-8')
    if (v1 == '<p></p>') and (v2 == '<p/>'):
        res = True
    else:
        res = (v1 == v2)
    return res

def checkPermission(permission, obj):
    '''We must call getSecurityManager() each time we need to check a
       permission.'''
    sm = getSecurityManager()
    return sm.checkPermission(permission, obj)

# ------------------------------------------------------------------------------
SENDMAIL_ERROR = 'Error while sending mail: %s.'
ENCODING_ERROR = 'Encoding error while sending mail: %s.'
MAILHOST_ERROR = 'Error with the MailServer while sending mail: %s.'

def getEmailAddress(name, email, encoding='utf-8'):
    '''Creates a full email address from a p_name and p_email.'''
    res = email
    if name:
        res = name.decode(encoding) + ' <%s>' % email
    return res

def sendMail(recipients, obj, event):
    '''Sends a mail related to p_event that occurred on p_obj to
       p_recipients. If p_recipients is None, the mail is sent to
       the system administrator.'''
    enc = obj.portal_properties.site_properties.getProperty('default_charset')
    # Compute user name
    pms = obj.portal_membership
    userName = pms.getAuthenticatedMember().id
    userInfo = pms.getMemberById(userName)
    if userInfo.getProperty('fullname'):
        userName = userInfo.getProperty('fullname')
    # Compute list of PloneMeeting groups for this user
    userGroups = ', '.join([g.Title() for g in \
                            obj.portal_plonemeeting.getUserMeetingGroups()])
    # Create the message parts
    d = 'PloneMeeting'
    portal = obj.portal_url.getPortalObject()
    translationMapping = {'portalUrl': portal.absolute_url(),
                          'portalTitle': portal.Title(),
                          'objectTitle': obj.Title(),
                          'objectUrl': obj.absolute_url(),
                          'meetingTitle': '', 'itemTitle': '',
                          'meetingDavUrl': '',
                          'user': userName,
                          'groups': userGroups,
                          }
    if obj.meta_type == 'MeetingAdvice':
        item = obj.aq_inner.aq_parent
        translationMapping['itemTitle'] = item.Title()
        translationMapping['itemUrl'] = item.absolute_url()
    if obj.meta_type == 'Meeting':
        translationMapping['meetingTitle'] = obj.Title()
        translationMapping['meetingDavUrl'] = obj.absolute_url_path()
    elif obj.meta_type == 'MeetingItem':
        translationMapping['itemTitle'] = obj.Title()
        translationMapping['lastAnnexTitle'] = ''
        translationMapping['lastAnnexTypeTitle'] = ''
        lastAnnex = obj.getLastInsertedAnnex()
        if lastAnnex:
            translationMapping['lastAnnexTitle'] = lastAnnex.Title() 
            translationMapping['lastAnnexTypeTitle'] = \
                lastAnnex.getMeetingFileType().Title()
        meeting = obj.getMeeting(brain=True)
        if meeting:
            translationMapping['meetingTitle'] = meeting.Title()
            mUrl = meeting.absolute_url()
            mUrl = mUrl[:mUrl.find('/at_references/')]
            translationMapping['meetingDavUrl'] = mUrl
    # Update the translationMapping with a sub-product-specific
    # translationMapping, that may also define custom mail subject and body.
    customRes = obj.adapted().getSpecificMailContext(event, translationMapping)
    if customRes:
        subject = customRes[0]
        body = customRes[1]
    else:
        subjectLabel = '%s_mail_subject' % event
        subject = obj.utranslate(subjectLabel, translationMapping, domain=d)
        bodyLabel = '%s_mail_body' % event
        body = obj.utranslate(bodyLabel, translationMapping, domain=d)
    adminFromAddress = getEmailAddress(
        portal.getProperty('email_from_name'),
        portal.getProperty('email_from_address'), enc)
    fromAddress = adminFromAddress
    if obj.portal_plonemeeting.getFunctionalAdminEmail():
        tool = obj.portal_plonemeeting
        fromAddress = getEmailAddress(tool.getFunctionalAdminName(),
                                      tool.getFunctionalAdminEmail(), enc)
    # Send the mail
    if not recipients:
        recipients = [adminFromAddress]
    for recipient in recipients:
        try:
            obj.MailHost.secureSend(
                body.encode(enc), recipient.encode(enc),
                fromAddress.encode(enc), subject.encode(enc),
                charset='utf-8', subtype='html')
        except socket.error, sg:
            logger.warn(SENDMAIL_ERROR % str(sg))
            break
        except UnicodeDecodeError, ue:
            logger.warn(ENCODING_ERROR % str(ue))
            break
        except MailHostError, mhe:
            logger.warn(MAILHOST_ERROR % str(mhe))
            break
        except Exception, e:
            logger.warn(SENDMAIL_ERROR % str(e))
            break

def sendMailIfRelevant(obj, event, permissionOrRole, isRole=False):
    '''An p_event just occurred on meeting or item p_obj. If the corresponding
       meeting config specifies that a mail needs to be sent, this function
       will send a mail. The mail subject and body are defined from i18n labels
       that derive from the event name. if p_isRole is True, p_permissionOrRole
       is a role, and the mail will be sent to every user having this role. If
       p_isRole is False, p_permissionOrRole is a permission and the mail will
       be sent to everyone having this permission.
       If mail sending is enabled for this event, this method returns True.'''
    res = False
    # If p_isRole is True and the current user has this role, I will not send
    # mail: a MeetingManager is already notified!
    currentUser = obj.portal_membership.getAuthenticatedMember()
    if isRole and currentUser.has_role(permissionOrRole):
        res = None # In this case we don't know if mail is enabled or disabled;
        # we just decide to avoid sending the mail.
    else:
        meetingConfig = obj.portal_plonemeeting.getMeetingConfig(obj)
        if (event in meetingConfig.getMailItemEvents()) or \
           (event in meetingConfig.getMailMeetingEvents()):
            # I must send a mail.
            res = True
            enc = obj.portal_properties.site_properties.getProperty(
                'default_charset')
            # Who are the recipients ?
            recipients = []
            for userId in obj.portal_membership.listMemberIds():
                user = obj.acl_users.getUser(userId)
                userInfo = obj.portal_membership.getMemberById(userId)
                if userInfo.getProperty('email'):
                    if isRole:
                        checkMethod = user.has_role
                    else:
                        checkMethod = user.has_permission
                    if checkMethod(permissionOrRole, obj):
                        if userInfo.getProperty('fullname'):
                            name = userInfo.getProperty('fullname').decode(enc)
                            recipient = name + ' <%s>' % \
                                userInfo.getProperty('email')
                        else:
                            recipient = userInfo.getProperty('email')
                        if obj.adapted().includeMailRecipient(event, userId):
                            recipients.append(recipient)
            sendMail(recipients, obj, event)
    return res

# ------------------------------------------------------------------------------
class HubSessionsMarshaller(Marshaller, XmlMarshaller):
    '''Abstract marshaller used as base class for marshalling PloneMeeting
       objects (meetings, items, configs,...).'''
    marshallContentType = 'text/xml; charset="utf-8"'
    frozableTypes = ('Meeting', 'MeetingItem')
    workflowableTypes = ('Meeting', 'MeetingItem', 'MeetingAdvice')

    def demarshall(self, instance, data, **kwargs):
        raise 'Unmarshalling is not implemented yet!'

    def marshall(self, instance, **kwargs):
        res = XmlMarshaller.marshall(self, instance, objectType='archetype')
        return (self.marshallContentType, len(res), res)

    def marshallSpecificElements(self, instance, res):
        '''Marshalls URLs of documents that were generated in the DB from
           p_instance and a given POD template.'''
        if instance.meta_type in self.frozableTypes:
            mConfig = instance.portal_plonemeeting.getMeetingConfig(instance)
            podTemplatesFolder = getattr(mConfig, TOOL_FOLDER_POD_TEMPLATES)
            res.write('<frozenDocuments type="list">')
            for podTemplate in podTemplatesFolder.objectValues():
                objectFolder = instance.getParentNode()
                docId = podTemplate.getDocumentId(instance)
                if hasattr(objectFolder.aq_base, docId) and \
                   podTemplate.isApplicable(instance):
                    res.write('<doc type="object">')
                    self.dumpField(res, 'id', docId)
                    self.dumpField(res, 'templateId', podTemplate.id)
                    self.dumpField(
                        res, 'templateFormat', podTemplate.getPodFormat())
                    self.dumpField(res, 'data', getattr(objectFolder, docId),
                                   fieldType='file')
                    res.write('</doc>')
            res.write('</frozenDocuments>')
        wft = instance.portal_workflow
        if instance.meta_type in self.workflowableTypes:
            # Dump workflow history
            res.write('<workflowHistory type="list">')
            workflows = wft.getWorkflowsFor(instance)
            if workflows:
                history = instance.workflow_history[workflows[0].id]
                for event in history:
                    res.write('<event type="object">')
                    for k, v in event.iteritems(): self.dumpField(res, k, v)
                    res.write('</event>')
            res.write('</workflowHistory>')
        if wft.getWorkflowsFor(instance)[0].id == \
           'plonemeeting_activity_workflow':
            # Add the object state
            objectState = wft.getInfoFor(instance, 'review_state')
            self.dumpField(res, 'active', objectState == 'active')

# ------------------------------------------------------------------------------
def addRecurringItemsIfRelevant(meeting, transition):
    '''Sees in the meeting config linked to p_meeting if the triggering of
       p_transition must lead to the insertion of some recurring items in
       p_meeting.'''
    recItems = []
    meetingConfig = meeting.portal_plonemeeting.getMeetingConfig(meeting)
    recItemsFolder = getattr(meetingConfig, TOOL_FOLDER_RECURRING_ITEMS)
    for recItem in recItemsFolder.objectValues('MeetingItem'):
        if recItem.getMeetingTransitionInsertingMe() == transition:
            recItems.append(recItem)
    if recItems:
        meeting.addRecurringItems(recItems)

# ------------------------------------------------------------------------------
defaultPermissions = (View, AccessContentsInformation, ModifyPortalContent,
                      DeleteObjects)
# I wanted to put permission "ReviewPortalContent" among defaultPermissions,
# but if I do this, it generates an error when calling "manage_permission" in
# method "clonePermissions" (see below). I've noticed that in several
# PloneMeeting standard workflows (meeting_workflow, meetingitem_workflow,
# meetingfile_workflow, etc), although this permission is declared as a
# managed permission, when you go in the ZMI to consult the actual
# permissions that are set on objects governed by those workflows, the
# permission "Review portal content" does not appear in the list at all.

def clonePermissions(srcObj, destObj, permissions=defaultPermissions):
    '''This method applies on p_destObj the same values for p_permissions
       than those that apply for p_srcObj, according to workflow on
       p_srcObj. p_srcObj may be an item or a meeting.'''
    wfTool = srcObj.portal_workflow
    meetingConfig = srcObj.portal_plonemeeting.getMeetingConfig(srcObj)
    if srcObj.meta_type == 'Meeting':
        workflowName = meetingConfig.getMeetingWorkflow()
    else: # MeetingItem
        workflowName = meetingConfig.getItemWorkflow()
    srcWorkflow = getattr(wfTool, workflowName)
    for permission in permissions:
        if permission in srcWorkflow.permissions:
            # Get the roles this permission is given to for srcObj in its
            # current state.
            srcStateDef = getattr(srcWorkflow.states, srcObj.queryState())
            permissionInfo = srcStateDef.getPermissionInfo(permission)
            destObj.manage_permission(permission, permissionInfo['roles'],
                acquire=permissionInfo['acquired'])
    #reindex object because permissions are catalogued too...
    destObj.reindexObject()

# ------------------------------------------------------------------------------
def replaceHtmlEntities(lines):
    """This method replace html entities defined in appy.pod"""
    from appy.pod.xhtml2odt import HTML_ENTITIES
    entity = ''
    ampersand = False
    newlines = ''
    for character in lines:
        if ampersand:
            if character == ';':
                if HTML_ENTITIES.has_key(entity):
                    newlines += HTML_ENTITIES[entity]
                else:
                    newlines += '&'+entity+';'
                ampersand = False
                entity = ''
            elif character == '&':
                newlines += '&'+entity
                entity = ''
            else:
                entity += character
            continue
        if character == '&':
            ampersand = True
            continue
        newlines += character
    if ampersand:
        newlines += '&'+entity
    return newlines

# ------------------------------------------------------------------------------
coreFieldNames = ('id', 'title', 'description')
def getCustomSchemaFields(baseSchema, completedSchema, cols):
    '''The Archetypes schema of any PloneMeeting content type can be extended
       through the "pm_updates.py mechanism". This function returns the list of
       fields that have been added by a sub-product by checking differences
       between the p_baseSchema and the p_completedSchema.'''
    baseFieldNames = baseSchema._fields
    res = []
    for field in completedSchema.fields():
        fieldName = field.getName()
        if (fieldName not in coreFieldNames) and \
           (fieldName not in baseFieldNames) and \
           (field.schemata != 'metadata'):
            res.append(field)
    if cols and (cols > 1):
        # I need to group fields in sub-lists (cols is the number of fields by
        # sublist).
        newRes = []
        fieldLine = []
        for field in res:
            fieldLine.append(field)
            if len(fieldLine) == cols:
                newRes.append(fieldLine)
                fieldLine = []
        # Append the last unfinished line if any (complete this line with
        # "None" values).
        if fieldLine:
            while len(fieldLine) < cols: fieldLine.append(None)
        res = newRes
    return res

# ------------------------------------------------------------------------------
def allowManagerToCreateIn(folder):
    '''Allows me (Manager) to create meeting and items in p_folder.'''
    folder.manage_permission(ADD_CONTENT_PERMISSIONS['MeetingItem'],
        ('Manager', 'MeetingMember',), acquire=0)
    folder.manage_permission(ADD_CONTENT_PERMISSIONS['Meeting'],
        ('Manager', 'MeetingManager',), acquire=0)

def disallowManagerToCreateIn(folder):
    '''Disallows me (Manager) to create meeting and items in p_folder.'''
    folder.manage_permission(ADD_CONTENT_PERMISSIONS['MeetingItem'],
        ('MeetingMember',), acquire=0)
    folder.manage_permission(ADD_CONTENT_PERMISSIONS['Meeting'],
        ('MeetingManager',), acquire=0)

# ------------------------------------------------------------------------------
def getDateFromRequest(day, month, year, start):
    '''This method produces a DateTime instance from info coming from a request.
       p_hour and p_month may be ommitted. p_start is a bool indicating if the
       date will be used as start date or end date; this will allow us to know
       how to fill p_hour and p_month if they are ommitted. If _year is
       ommitted, we will return a date near the Big bang (if p_start is True)
       or near the Apocalypse (if p_start is False). p_day, p_month and p_year
       are required to be valid string representations of integers.'''
    # Determine day
    if not day.strip():
        if start: day = 1
        else: day = 31
    else: day = int(day)
    # Determine month
    if not month.strip():
        if start: month = 1
        else: month = 12
    else: month = int(month)
    # Determine year
    if not year.strip():
        if start: year=1000
        else: year=9999
    else:
        year = int(year)
    return DateTime('%d/%d/%d' % (month, day, year))
# ------------------------------------------------------------------------------
