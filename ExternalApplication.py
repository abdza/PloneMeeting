# -*- coding: utf-8 -*-
#
# File: ExternalApplication.py
#
# Copyright (c) 2010 by []
# Generator: ArchGenXML Version 2.4.1
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """unknown <unknown>"""
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from zope.interface import implements
import interfaces

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from Products.PloneMeeting.config import *

##code-section module-header #fill in your manual code here
import urllib, urllib2, httplib, base64, os, os.path, time
from DateTime import DateTime
from persistent.mapping import PersistentMapping
from appy.shared.xml_parser import XmlUnmarshaller
from appy.pod import convertToXhtml
from Products.PloneMeeting.utils import getCustomAdapter
from Products.PloneMeeting.profiles import *
defValues = ExternalApplicationDescriptor.get()
from Products.PloneMeeting.utils import \
     sendMail, allowManagerToCreateIn, disallowManagerToCreateIn, \
     clonePermissions
from Products.PloneMeeting.MeetingConfig import MeetingConfig
import logging
logger = logging.getLogger('PloneMeeting')
class DistantSiteError(Exception): pass
##/code-section module-header

schema = Schema((

    BooleanField(
        name='notify',
        default= defValues.notify,
        widget=BooleanField._properties['widget'](
            description="Notify",
            description_msgid="ea_notify_descr",
            label='Notify',
            label_msgid='PloneMeeting_label_notify',
            i18n_domain='PloneMeeting',
        ),
    ),
    StringField(
        name='notifyUrl',
        default= defValues.notifyUrl,
        widget=StringField._properties['widget'](
            description="NotifyUrl",
            description_msgid="notify_url_descr",
            size=70,
            label='Notifyurl',
            label_msgid='PloneMeeting_label_notifyUrl',
            i18n_domain='PloneMeeting',
        ),
        validators=('isURL',),
    ),
    StringField(
        name='notifyEmail',
        default= defValues.notifyEmail,
        widget=StringField._properties['widget'](
            description="NotifyEmail",
            description_msgid="notify_email_descr",
            size=70,
            label='Notifyemail',
            label_msgid='PloneMeeting_label_notifyEmail',
            i18n_domain='PloneMeeting',
        ),
        validators=('isEmail',),
    ),
    StringField(
        name='notifyProxy',
        default= defValues.notifyProxy,
        widget=StringField._properties['widget'](
            description="NotifyProxy",
            description_msgid="notify_proxy_descr",
            size=70,
            label='Notifyproxy',
            label_msgid='PloneMeeting_label_notifyProxy',
            i18n_domain='PloneMeeting',
        ),
        validators=('isURL',),
    ),
    StringField(
        name='notifyLogin',
        default= defValues.notifyLogin,
        widget=StringField._properties['widget'](
            description="NotifyLogin",
            description_msgid="notify_login_descr",
            label='Notifylogin',
            label_msgid='PloneMeeting_label_notifyLogin',
            i18n_domain='PloneMeeting',
        ),
    ),
    StringField(
        name='notifyPassword',
        default= defValues.notifyPassword,
        widget=PasswordWidget(
            description="NotifyPassword",
            description_msgid="notify_password_descr",
            label='Notifypassword',
            label_msgid='PloneMeeting_label_notifyPassword',
            i18n_domain='PloneMeeting',
        ),
    ),
    StringField(
        name='loginHeaderKey',
        default= defValues.loginHeaderKey,
        widget=StringField._properties['widget'](
            description="LoginHeaderKey",
            description_msgid="login_header_key_descr",
            label='Loginheaderkey',
            label_msgid='PloneMeeting_label_loginHeaderKey',
            i18n_domain='PloneMeeting',
        ),
    ),
    StringField(
        name='passwordHeaderKey',
        default= defValues.passwordHeaderKey,
        widget=StringField._properties['widget'](
            description="PasswordHeaderKey",
            description_msgid="password_header_key_descr",
            label='Passwordheaderkey',
            label_msgid='PloneMeeting_label_passwordHeaderKey',
            i18n_domain='PloneMeeting',
        ),
    ),
    StringField(
        name='meetingParamName',
        default= defValues.meetingParamName,
        widget=StringField._properties['widget'](
            description="MeetingParamName",
            description_msgid="meeting_param_name_descr",
            label='Meetingparamname',
            label_msgid='PloneMeeting_label_meetingParamName',
            i18n_domain='PloneMeeting',
        ),
    ),
    StringField(
        name='notifyProtocol',
        default= defValues.notifyProtocol,
        widget=SelectionWidget(
            description="NotifyProtocol",
            description_msgid="notify_protocol_descr",
            label='Notifyprotocol',
            label_msgid='PloneMeeting_label_notifyProtocol',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        vocabulary='listProtocols',
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

ExternalApplication_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
ExternalApplication_schema = ModelExtender(
    ExternalApplication_schema, 'extapp').run()
##/code-section after-schema

class ExternalApplication(BaseContent, BrowserDefaultMixin):
    """
    """
    security = ClassSecurityInfo()

    implements(interfaces.IExternalApplication)

    meta_type = 'ExternalApplication'
    _at_rename_after_creation = True

    schema = ExternalApplication_schema

    ##code-section class-header #fill in your manual code here
    URL_NOTIFY_ERROR = 'Application "%s" could not be contacted at URL "%s". ' \
        'I will try to send him a mail instead (if an email address is ' \
        'defined for this application). Error is: %s.'
    CONNECT_ERROR = 'Error while contacting distant site %s (%s).'
    MEETING_ALREADY_IMPORTED = 'Meeting "%s" was NOT imported (already here).'
    MEETING_IN_CREATION = 'Importing meeting "%s"...'
    MEETING_CREATED = 'Meeting "%s" was successfully imported in home ' \
        'folder of user "pmManager".'
    MEETING_AND_USER_CREATED = MEETING_CREATED + ' This user has been ' \
        'created (password=meeting) and has roles Member, MeetingManager ' \
        'and MeetingObserverGlobal.'
    MEETING_CONFIG_IN_CREATION = 'Importing meeting config "%s"...'
    MEETING_CONFIG_CREATED = 'Meeting config "%s" successfully imported.'
    SUBOBJECT_IN_CREATION = 'Creating config object "%s"...'
    SUBOBJECT_CREATED = 'Config object "%s" created.'
    ITEM_IN_CREATION = 'Importing item "%s"...'
    ITEM_CREATED = 'Item "%s" created.'
    ANNEX_IN_CREATION = 'Importing annex "%s"...'
    ANNEX_CREATED = 'Annex "%s" created.'
    ADVICE_IN_CREATION = 'Importing advice "%s"...'
    ADVICE_CREATED = 'Advice "%s" created.'
    GROUP_ALREADY_IMPORTED = 'Group "%s" was NOT imported (already here).'
    GROUP_IN_CREATION = 'Importing group "%s"...'
    GROUP_CREATED = 'Group "%s" has been imported successfully.'

    notBasicMeetingFields = ('id', 'items', 'lateItems', 'creation_date',
        'modification_date', 'frozenDocuments', 'workflowHistory')
    notBasicItemFields = ('id', 'classifier', 'preferredMeeting', 'reference',
        'annexes', 'annexesDecision', 'advices', 'creation_date',
        'modification_date', 'pm_modification_date', 'frozenDocuments',
        'workflowHistory', 'votes')
    notBasicAdviceFields = ('id', 'creation_date', 'modification_date',
        'pm_modification_date', 'workflowHistory')
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePublic('listProtocols')
    def listProtocols(self):
        res = DisplayList(( ("httpGet", 'HTTP GET'),
                            ("httpPost", 'HTTP POST') ))
        return res

    def _sendHttpRequest(self, url=None):
        '''Sends a HTTP request at p_url to the external application. If p_url
           is not specified, self.getNotifyUrl() is used. Returns a 2-tuple:
           1st value tells if the request was successfull or not, 2nd value
           is the response of the external application in case of success or
           the error message in case of failure.'''
        # Determine request parameters
        params = None
        if self.getNotify():
            # Give to the target application meeting URL as parameter
            params = urllib.urlencode({self.getMeetingParamName(): meetingUrl})
            protocol = self.getNotifyProtocol()
        else:
            protocol = 'httpGet' # We force this value for contacting the master
            # PloneMeeting site.
        # Determine URL
        if url:
            appUrl = url
        else:
            appUrl = self.getNotifyUrl()
            if (protocol == 'httpGet') and params:
                appUrl = '%s?%s' % (appUrl, params)
        # Create the request object
        httpReq = urllib2.Request(appUrl)
        if (protocol == 'httpPost') and params:
            httpReq.add_data(params)
        # Add credentials if needed
        if self.getNotifyLogin():
            if self.getNotify():
                httpReq.add_header(self.getLoginHeaderKey(),
                                   self.getNotifyLogin())
                httpReq.add_header(self.getPasswordHeaderKey(),
                                   self.getNotifyPassword())
            else:
                auth64 = base64.encodestring('%s:%s' % (self.getNotifyLogin(),
                    self.getNotifyPassword()))[:-1]
                httpReq.add_header("Authorization", "Basic %s" % auth64)
        # Specify a proxy if needed
        if self.getNotifyProxy():
            httpReq.set_proxy(self.getNotifyProxy(), 'http')
        # Send the request
        try:
            response = urllib2.urlopen(httpReq)
            res = (True, response.read())
        except IOError, ioe:
            res = (False, convertToXhtml(str(ioe)))
            logger.warn(self.URL_NOTIFY_ERROR% (self.Title(), appUrl, str(ioe)))
        except httplib.HTTPException, he:
            msg = str(he) + '(' + he.__class__.__name__ + ')'
            res = (False, convertToXhtml(msg))
            logger.warn(self.URL_NOTIFY_ERROR % (self.Title(), appUrl, msg))
        return res

    security.declarePublic('notifyExternalApplication')
    def notifyExternalApplication(self, meeting=None):
        '''Notifies the external app I represent that p_meeting has been
           archived. If p_meeting is None, a dummy meetingUrl will be sent
           for testing purposes.'''
        mustSendMail = True
        if not meeting:
            meetingUrl = '/dummy/meeting'
        else:
            meetingUrl = meeting.absolute_url_path()
        res = None
        if self.getNotifyUrl():
            mustSendMail = False
            success, res = self._sendHttpRequest()
            if not success:
                mustSendMail = True
        # Try to send a mail if needed
        if mustSendMail and self.getNotifyEmail():
            obj = meeting
            if not meeting:
                obj = self
            sendMail([self.getNotifyEmail()], obj, 'meetingIsArchived')
        return res

    security.declarePublic('listArchivedMeetings')
    def listArchivedMeetings(self):
        '''Gets the list of archived meetings at the PloneMeeting master site.'''
        # Gets the meeting config URLs by getting tool information
        toolUrl = self.getNotifyUrl() + '/portal_plonemeeting'
        success, response = self._sendHttpRequest(toolUrl)
        if not success:
            return (False, self.CONNECT_ERROR % (toolUrl, response))
        masterTool = XmlUnmarshaller().parse(response)
        meetings = []
        for configUrl in masterTool.meetingConfigs:
            # Gets the list of archived meetings in this meeting config.
            success, response = self._sendHttpRequest(configUrl)
            if not success:
                return (False, self.CONNECT_ERROR % (configUrl, response))
            masterConfig = XmlUnmarshaller().parse(response)
            configTitle = u'%s (%s)' % (masterConfig.id, masterConfig.title)
            for masterMeeting in masterConfig.availableMeetings:
                alreadyImported = False
                if self.portal_catalog(meta_type="Meeting",id=masterMeeting.id):
                    alreadyImported = True
                meetings.append( (masterMeeting.title, masterMeeting.url,
                    configTitle, configUrl, masterConfig.id, alreadyImported))
        return True, meetings

    security.declarePublic('listMeetingGroups')
    def listMeetingGroups(self):
        '''Gets the list of available meeting groups in a master site.'''
        toolUrl = self.getNotifyUrl() + '/portal_plonemeeting'
        success, response = self._sendHttpRequest(toolUrl)
        if not success:
            return (False, self.CONNECT_ERROR % (toolUrl, response))
        masterTool = XmlUnmarshaller().parse(response)
        res = []
        for mg in masterTool.meetingGroups:
            res.append( (mg.title, mg.id, mg.acronym, mg.active, mg.url) )
        return (True, res)

    security.declarePublic('importMeetingGroup')
    def importMeetingGroup(self, groupUrl=None):
        '''Imports in the tool the distant meeting group at p_groupUrl.'''
        if not groupUrl:
            groupUrl = self.REQUEST.get('groupUrl')
            calledFromPage = True
        else:
            calledFromPage = False
        logger.info(self.GROUP_IN_CREATION % groupUrl)
        success, response = self._sendHttpRequest(groupUrl)
        if not success:
            msg = self.CONNECT_ERROR % (groupUrl, response)
            if calledFromPage: return msg
            else: raise DistantSiteError(msg)
        masterGroup = XmlUnmarshaller(klass=GroupDescriptor).parse(response)
        masterGroup.creators = []
        masterGroup.observers = []
        masterGroup.reviewers = []
        masterGroup.advisers = []
        if not hasattr(self.portal_plonemeeting.aq_base, masterGroup.id):
            self.portal_plonemeeting.addUsersAndGroups([masterGroup])
            res = self.GROUP_CREATED % masterGroup.title
        else:
            res = self.GROUP_ALREADY_IMPORTED % masterGroup.title
        logger.info(res)
        return res

    security.declarePublic('importMeetingGroups')
    def importMeetingGroups(self):
        '''Imports several groups at once.'''
        urls = self.REQUEST.get('masterUrls', None)
        res = ''
        if urls:
            try:
                for url in urls.split('|'):
                    if url:
                        res += self.importMeetingGroup(url) + '<br/>'
            except DistantSiteError, de:
                return str(de)
        return res

    security.declarePublic('importAdvice')
    def importAdvice(self, adviceUrl, item, meetingConfig):
        '''Imports the distant advice at p_adviceUrl and creates it in
           p_item.'''
        logger.info(self.ADVICE_IN_CREATION % adviceUrl)
        success, response = self._sendHttpRequest(adviceUrl)
        if not success:
            raise DistantSiteError(self.CONNECT_ERROR % (adviceUrl, response))
        masterAdvice = XmlUnmarshaller().parse(response)
        # Import the agreement level if needed
        if masterAdvice.agreementLevel:
            agFolder = getattr(meetingConfig, TOOL_FOLDER_AGREEMENT_LEVELS)
            agLevel = getattr(agFolder, masterAdvice.agreementLevel, None)
            if not agLevel:
                # Import the agreement level on-the-fly
                agUrl = '%s/portal_plonemeeting/%s/%s/%s' % (
                    self.getNotifyUrl(), meetingConfig.id,
                    TOOL_FOLDER_AGREEMENT_LEVELS, masterAdvice.agreementLevel)
                agLevel = self.importMeetingConfigSubObject(
                    TOOL_FOLDER_AGREEMENT_LEVELS, agUrl, meetingConfig)
        # Create the advice
        item.invokeFactory('MeetingAdvice', id=masterAdvice.id)
        advice = getattr(item, masterAdvice.id)
        # Set "basic" advice attributes
        for fieldName, fieldValue in masterAdvice.__dict__.iteritems():
            if fieldName not in self.notBasicAdviceFields:
                exec 'advice.set%s%s(masterAdvice.%s)'% (fieldName[0].upper(),
                    fieldName[1:], fieldName)
        # What to do with adviserName? It should correspond to an existing
        # Plone group of advisors.
        advice.creation_date = masterAdvice.creation_date
        advice.modification_date = masterAdvice.modification_date
        advice.pm_modification_date = masterAdvice.pm_modification_date
        advice.reindexObject()
        advice.modification_date = masterAdvice.modification_date
        logger.info(self.ADVICE_CREATED % advice.Title())

    security.declarePublic('importAnnex')
    def importAnnex(self, annexUrl, item, meetingConfig, decisionRelated=False):
        '''Imports the distant annex at p_annexUrl, creates it in p_item which
           is a folder and links it to it, too, through the reference field
           "annexes" or "annexesDecision", depending on p_decisionRelated.'''
        logger.info(self.ANNEX_IN_CREATION % annexUrl)
        success, response = self._sendHttpRequest(annexUrl)
        if not success:
            raise DistantSiteError(self.CONNECT_ERROR % (annexUrl, response))
        masterAnnex = XmlUnmarshaller().parse(response)
        # Determine file type
        fileTypeId = os.path.basename(masterAnnex.meetingFileType[0])
        fileType = getattr(meetingConfig.meetingfiletypes, fileTypeId, None)
        if not fileType:
            # Get the file type on-the-fly.
            fileType = self.importMeetingConfigSubObject(
                TOOL_FOLDER_FILE_TYPES, masterAnnex.meetingFileType[0],
                meetingConfig)
        # Create the meetingFile
        item.invokeFactory('MeetingFile', id=masterAnnex.id,
            file=masterAnnex.file.content, title=masterAnnex.title,
            meetingFileType=(fileType,))
        annex = getattr(item, masterAnnex.id)
        annex.setExtractedText(masterAnnex.extractedText)
        annex.setCreators(masterAnnex.creators)
        # Link the annex to the item
        if decisionRelated:
            annexes = item.getAnnexesDecision()
        else:
            annexes = item.getAnnexes()
        annexes.append(annex)
        if decisionRelated:
            item.setAnnexesDecision(annexes)
        else:
            item.setAnnexes(annexes)
        annex.creation_date = masterAnnex.creation_date
        annex.modification_date = masterAnnex.modification_date
        annex.pm_modification_date = masterAnnex.pm_modification_date
        annex.reindexObject()
        annex.modification_date = masterAnnex.modification_date
        logger.info(self.ANNEX_CREATED % annex.Title())

    security.declarePublic('importItem')
    def importItem(self, itemUrl, meeting, meetingConfig, destFolder,
                   isLate=False):
        '''Imports in p_destFolder the distant item at p_itemUrl and link it
           into p_meeting.'''
        logger.info(self.ITEM_IN_CREATION % itemUrl)
        success, response = self._sendHttpRequest(itemUrl)
        if not success:
            raise DistantSiteError(self.CONNECT_ERROR % (itemUrl, response))
        masterItem = XmlUnmarshaller().parse(response)
        itemType = meetingConfig.getItemTypeName()
        # Make PloneMeeting aware of the current content type
        self.REQUEST.set('type_name', itemType)
        itemId = masterItem.id
        if hasattr(destFolder.aq_base, masterItem.id):
            # Some item IDS may be the same because they are stored in several
            # home folders in the master site.
            itemId = 'item%f' % time.time()
        itemId = destFolder.invokeFactory(itemType, itemId)
        item = getattr(destFolder, itemId)
        # Set item attributes.
        # Resolve reference to the classifier
        if masterItem.classifier:
            cFolder = getattr(meetingConfig, TOOL_FOLDER_CLASSIFIERS)
            classifier = getattr(cFolder, masterItem.classifier, None)
            if not classifier:
                # Get the classifier on-the-fly
                classifierUrl = '%s/portal_plonemeeting/%s/%s/%s' % (
                    self.getNotifyUrl(), meetingConfig.id,
                    TOOL_FOLDER_CLASSIFIERS, masterItem.classifier)
                self.importMeetingConfigSubObject(
                    TOOL_FOLDER_CLASSIFIERS, classifierUrl, meetingConfig)
                classifier = getattr(cFolder, masterItem.classifier)
            item.setClassifier(classifier)
        # Download MeetingGroups if needed
        neededGroups = [masterItem.proposingGroup] + masterItem.associatedGroups
        if meetingConfig.getUseGroupsAsCategories() and item.getCategory():
            neededGroups.append(item.getCategory())
        tool = meetingConfig.getParentNode()
        for groupId in neededGroups:
            if not hasattr(tool, groupId):
                # I need to retrieve this group
                groupUrl = '%s/portal_plonemeeting/%s' % (self.getNotifyUrl(),
                    groupId)
                self.importMeetingGroup(groupUrl)
        # Download categories if needed
        if not meetingConfig.getUseGroupsAsCategories():
            category = item.getCategory(True)
            if not category:
                categoryUrl = '%s/portal_plonemeeting/%s/%s/%s' % (
                    self.getNotifyUrl(), meetingConfig.id,
                    TOOL_FOLDER_CATEGORIES, item.getCategory())
                self.importMeetingConfigSubObject(
                    TOOL_FOLDER_CATEGORIES, categoryUrl, meetingConfig)
        # Set "basic" item attributes
        for fieldName, fieldValue in masterItem.__dict__.iteritems():
            if fieldName not in self.notBasicItemFields:
                exec 'item.set%s%s(masterItem.%s)'% (fieldName[0].upper(),
                    fieldName[1:], fieldName)
        item.at_post_create_script()
        # Set votes
        for vote in masterItem.votes:
            item.votes[vote.voter] = vote.voteValue
        # Import the frozen documents linked to this item, if any
        for frozenDoc in masterItem.frozenDocuments:
            docId = '%s_%s.%s' % (
                item.id, frozenDoc.templateId, frozenDoc.templateFormat)
            # We reconstitute the ID here because the item ID may not be the
            # same as the one from the corresponding item on the master site.
            destFolder.invokeFactory('File', id=docId,
                file=frozenDoc.data.content)
            doc = getattr(destFolder, docId)
            doc.setFormat(frozenDoc.data.mimeType)
            clonePermissions(item, doc)
        # Retrieve the workflow history, and add a last "virtual" transition
        # representing the transfer from one site to another.
        history = [event.__dict__ for event in masterItem.workflowHistory]
        history.append({'action': u'transfer', 'actor': u'admin',
            'comments': '', 'review_state': u'archived', 'time':DateTime()})
        item.workflow_history = PersistentMapping()
        item.workflow_history['meetingitem_archive_workflow'] = tuple(history)
        # Link the item to the meeting
        if isLate:
            lateItems = meeting.getLateItems()
            lateItems.append(item)
            meeting.setLateItems(lateItems)
        else:
            items = meeting.getItems()
            items.append(item)
            meeting.setItems(items)
        # Add annexes
        for annexUrl in masterItem.annexes:
            self.importAnnex(annexUrl, item, meetingConfig)
        for annexUrl in masterItem.annexesDecision:
            self.importAnnex(annexUrl, item, meetingConfig,decisionRelated=True)
        item.updateAnnexIndex()
        # Add advices
        for adviceUrl in masterItem.advices:
            self.importAdvice(adviceUrl, item, meetingConfig)
        item.updateAdviceIndex()
        # Update dates and creators
        item.setCreators(masterItem.creators)
        item.creation_date = masterItem.creation_date
        item.modification_date = masterItem.modification_date
        item.pm_modification_date = masterItem.pm_modification_date
        item.reindexObject()
        item.modification_date = masterItem.modification_date
        logger.info(self.ITEM_CREATED % item.Title())

    security.declarePublic('importMeetingConfigSubObject')
    def importMeetingConfigSubObject(self, objectType, objectUrl,
        meetingConfig=None, unmarshallOnly=False):
        '''Imports a distant sub-object of type p_objectType at p_objectUrl.
           If unmarshallOnly is True, is simply creates and returns a
           *Descriptor instance unmarshalled from the distant site. Else,
           it also creates the corresponding object in the meeting config.
           p_unmarshallOnly=False occurs when we need to import several objects:
           we do not create them directly but we store unmarshalled instances in
           lists that are defined on a MeetingConfigDescriptor that, in a later
           step, will do the whole job of creating all the corresponding
           sub-objects. p_meetingConfig is necessary only if p_unmarshallonly
           is False.'''
        logger.info(self.SUBOBJECT_IN_CREATION % objectUrl)
        success, response = self._sendHttpRequest(objectUrl)
        if not success:
            raise DistantSiteError(self.CONNECT_ERROR % (objectUrl, response))
        typeInfo = MeetingConfig.subFoldersInfo[objectType]
        exec 'klass = %s' % typeInfo[3]
        masterObject = XmlUnmarshaller(klass=klass).parse(response)
        logger.info(self.SUBOBJECT_CREATED % masterObject.title)
        if unmarshallOnly:
            return masterObject
        else:
            # Create the corresponding object.
            if objectType == TOOL_FOLDER_CATEGORIES:
                return meetingConfig.addCategory(masterObject, True)
            elif objectType == TOOL_FOLDER_CLASSIFIERS:
                return meetingConfig.addCategory(masterObject, False)
            elif objectType == TOOL_FOLDER_FILE_TYPES:
                return meetingConfig.addFileType(masterObject, self)
            elif objectType == TOOL_FOLDER_AGREEMENT_LEVELS:
                return meetingConfig.addAgreementLevel(masterObject, self)
            elif objectType == TOOL_FOLDER_POD_TEMPLATES:
                return meetingConfig.addPodTemplate(masterObject, self)
            elif objectType == TOOL_FOLDER_MEETING_USERS:
                return meetingConfig.addMeetingUser(masterObject, self)

    security.declarePublic('updateMeetingConfig')
    def updateMeetingConfig(self, configUrl, meetingConfig):
        '''The distant meeting config at p_configUrl already exists; we check
           here if sub-objects have been added, and we import them if it is the
           case.'''
        # Get the distant meeting config
        logger.info(self.MEETING_CONFIG_IN_CREATION % configUrl)
        success, response = self._sendHttpRequest(configUrl)
        if not success:
            raise DistantSiteError(self.CONNECT_ERROR % (configUrl, response))
        masterConfig = XmlUnmarshaller(
            klass=MeetingConfigDescriptor).parse(response)
        # Import additional sub-objects if any
        for folderName, fInfo in MeetingConfig.subFoldersInfo.iteritems():
            if fInfo[2]:
                folder = getattr(meetingConfig, folderName)
                for objectUrl in getattr(masterConfig, folderName):
                    objectId = os.path.basename(objectUrl)
                    if not hasattr(folder.aq_base, objectId):
                        # Import the new object
                        self.importMeetingConfigSubObject(folderName, objectUrl,
                            meetingConfig)

    security.declarePublic('importMeetingConfigSubObject')
    def importMeetingConfig(self, configUrl):
        '''Imports into this site the distant meeting configuration at
           p_configUrl and returns the created meetingConfig.'''
        # Get the distant meeting config
        logger.info(self.MEETING_CONFIG_IN_CREATION % configUrl)
        success, response = self._sendHttpRequest(configUrl)
        if not success:
            raise DistantSiteError(self.CONNECT_ERROR % (configUrl, response))
        masterConfig = XmlUnmarshaller(
            klass=MeetingConfigDescriptor).parse(response)
        # Get the sub-objects within this meeting config. Currently, I have
        # only retrieved the URLs to the sub-objects in masterConfig.
        for folderName, fInfo in MeetingConfig.subFoldersInfo.iteritems():
            if fInfo[2]:
                objectsList = []
                for objectUrl in getattr(masterConfig, folderName):
                    masterObject = self.importMeetingConfigSubObject(
                        folderName, objectUrl, unmarshallOnly=True)
                    objectsList.append(masterObject)
                exec 'masterConfig.%s = objectsList' % fInfo[2]
        masterConfig.recurringItems = []
        # Because we are on an "archive" site, I will use specific "archive"
        # workflows for meetings and items instead of those used on the
        # master site.
        masterConfig.itemWorkflow = 'meetingitem_archive_workflow'
        masterConfig.meetingWorkflow = 'meeting_archive_workflow'
        masterConfig.meetingAppDefaultView = 'topic_searchalldecisions'
        masterConfig.itemTopicStates = ('archived',)
        masterConfig.meetingTopicStates = ()
        masterConfig.decisionTopicStates = ('archived',)
        res = self.portal_plonemeeting.createMeetingConfig(masterConfig, self)
        logger.info(self.MEETING_CONFIG_CREATED % masterConfig.id)
        return res

    security.declarePublic('importArchivedMeeting')
    def importArchivedMeeting(self, meetingUrl=None):
        '''Imports a meeting from a master Plone site. The WebDAV URL of the
           meeting is in the request or in p_meetingUrl.'''
        rq = self.REQUEST
        if not meetingUrl:
            meetingUrl = rq.get('meetingUrl')
        logger.info(self.MEETING_IN_CREATION % meetingUrl)
        configUrl = rq.get('configUrl')
        configId = rq.get('configId')
        destFolder = None # Where the meeting will be created
        try:
            # If the corresponding meeting config does not exist on this site, I
            # must create it first.
            tool = self.getParentNode()
            configIds = [c.id for c in tool.objectValues('MeetingConfig')]
            if configId not in configIds:
                meetingConfig = self.importMeetingConfig(configUrl)
            else:
                meetingConfig = getattr(tool, configId)
                self.updateMeetingConfig(configUrl, meetingConfig)
            # Import the meeting in itself.
            success, response = self._sendHttpRequest(meetingUrl)
            if not success:
                raise DistantSiteError(
                    self.CONNECT_ERROR % (meetingUrl, response))
            masterMeeting = XmlUnmarshaller().parse(response)
            meetingType = meetingConfig.getMeetingTypeName()
            # Make PloneMeeting aware of the current meeting type
            rq.set('type_name', meetingType)
            # If user "pmManager" does not exist, I will create it. Indeed,
            # I need a MeetingManager for storing meetings in its config folder.
            if not self.portal_membership.getMemberById('pmManager'):
                # Create the MeetingManager
                self.portal_registration.addMember('pmManager', 'meeting',
                    ['Member', 'MeetingManager', 'MeetingObserverGlobal'],
                    properties={'username': 'pmManager',
                        'fullname':'Archive user', 'email':'you@plonegov.org'})
                res = self.MEETING_AND_USER_CREATED % masterMeeting.title
            else:
                res = self.MEETING_CREATED % masterMeeting.title
            # I will store meetings and items in the home folder of pmManager
            # (one folder for every meeting + included items).
            portal = self.portal_url.getPortalObject()
            if not hasattr(portal.Members, 'pmManager'):
                portal.portal_membership.createMemberArea('pmManager')
            configFolder = tool.getPloneMeetingFolder(
                meetingConfig.id, 'pmManager')
            if hasattr(configFolder, masterMeeting.id):
                return self.MEETING_ALREADY_IMPORTED % masterMeeting.title
            configFolder.invokeFactory(
                'Folder', masterMeeting.id, title=masterMeeting.title)
            destFolder = getattr(configFolder, masterMeeting.id)
            allowManagerToCreateIn(destFolder)
            meetingId = destFolder.invokeFactory(meetingType, masterMeeting.id)
            meeting = getattr(destFolder, meetingId)
            # Update meeting data
            for fieldName, fieldValue in masterMeeting.__dict__.iteritems():
                if fieldName not in self.notBasicMeetingFields:
                    exec 'meeting.set%s%s(masterMeeting.%s)' % (
                        fieldName[0].upper(), fieldName[1:], fieldName)
            # Import the frozen documents linked to this meeting, if any
            for frozenDoc in masterMeeting.frozenDocuments:
                destFolder.invokeFactory('File', id=frozenDoc.id,
                    file=frozenDoc.data.content)
                doc = getattr(destFolder, frozenDoc.id)
                doc.setFormat(frozenDoc.data.mimeType)
                clonePermissions(meeting, doc)
            # Retrieve the workflow history and add a last "virtual" transition
            # representing the transfer from one site to another.
            history = [e.__dict__ for e in masterMeeting.workflowHistory]
            history.append({'action': u'transfer', 'actor': u'admin',
                'comments': '', 'review_state': u'archived', 'time':DateTime()})
            meeting.workflow_history = PersistentMapping()
            meeting.workflow_history['meeting_archive_workflow']= tuple(history)
            # Import the items included in this meeting, into the same folder as
            # the meeting itself.
            for itemUrl in masterMeeting.items:
                self.importItem(itemUrl, meeting, meetingConfig, destFolder)
            for itemUrl in masterMeeting.lateItems:
                self.importItem(itemUrl, meeting, meetingConfig, destFolder,
                    isLate=True)
            meeting.creation_date = masterMeeting.creation_date
            meeting.modification_date = masterMeeting.modification_date
            meeting.reindexObject()
            meeting.modification_date = masterMeeting.modification_date
            disallowManagerToCreateIn(destFolder)
            logger.info(res)
        except DistantSiteError, de:
            res = str(de)
            logger.info(res)
            # Delete the folder where the incomplete meeting was created, if it
            # was created.
            if destFolder:
                # First, remove folder content.
                if destFolder.objectIds():
                    for elem in destFolder.objectValues():
                        if elem.meta_type == 'Meeting':
                            for item in elem.getItems():
                                elem.removeGivenObject(item)
                            for item in elem.getLateItems():
                                elem.removeGivenObject(item)
                        destFolder.removeGivenObject(elem)
                # Then, remove the folder.
                destFolder.getParentNode().removeGivenObject(destFolder)
        return res

    security.declarePublic('importArchivedMeetings')
    def importArchivedMeetings(self):
        '''Imports several meetings at once.'''
        urls = self.REQUEST.get('masterUrls', None)
        res = ''
        if urls:
            for url in urls.split('|'):
                if url:
                    res += self.importArchivedMeeting(url) + '<br/>'
        return res

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self): self.adapted().onEdit(isCreated=True)

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self): self.adapted().onEdit(isCreated=False)

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'ExternalApplication': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''



registerType(ExternalApplication, PROJECTNAME)
# end of class ExternalApplication

##code-section module-footer #fill in your manual code here
##/code-section module-footer



