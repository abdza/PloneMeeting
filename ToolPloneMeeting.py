# -*- coding: utf-8 -*-
#
# File: ToolPloneMeeting.py
#
# Copyright (c) 2009 by PloneGov
# Generator: ArchGenXML Version 1.5.2
#            http://plone.org/products/archgenxml
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

__author__ = """Gaetan DELANNAY <gaetan.delannay@geezteem.com>, Gauthier BASTIEN
<gbastien@commune.sambreville.be>, Stephan GEULETTE
<stephan.geulette@uvcw.be>"""
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from Products.PloneMeeting.config import *


from Products.CMFCore.utils import UniqueObject

    
##code-section module-header #fill in your manual code here
import os, os.path, time
from OFS.CopySupport import _cb_decode
from BTrees.OOBTree import OOBTree
from AccessControl import getSecurityManager
from Globals import InitializeClass
from DateTime import DateTime
import transaction
import OFS.Moniker
from ZODB.POSException import ConflictError
from zope.interface import directlyProvides
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.permissions import AccessContentsInformation
from Products.CMFCore.Expression import Expression, createExprContext
from Products.CMFCore.permissions import View
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFPlone.PloneBatch import Batch
from Products.CMFPlone.i18nl10n import utranslate
from Products.CMFPlone.browser.interfaces import INavigationRoot
from Products.ATContentTypes import permission as ATCTPermissions
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.tests.profiling import profiler
from Products.PloneMeeting.profiles import PloneMeetingConfiguration
from Products.PloneMeeting.utils import getCustomAdapter, \
    HubSessionsMarshaller, monthsIds, weekdaysIds
from Products.PloneMeeting.Searcher import Searcher
from Products.PloneMeeting.MeetingFile import MeetingFile

# Some constants ---------------------------------------------------------------
MEETING_CONFIG_ERROR = 'A validation error occurred while instantiating ' \
                       'meeting configuration with id "%s". %s'
MEETING_CONFIG_FIELD_ERROR = 'Validation error on field "%s" of meeting ' \
                             'config "%s". %s'

defValues = PloneMeetingConfiguration.get()
# This way, I get the default values for some MeetingConfig fields,
# that are defined in a unique place: the MeetingConfigDescriptor class, used
# for importing profiles.

# Marshaller -------------------------------------------------------------------
class ToolMarshaller(HubSessionsMarshaller):
    '''Allows to marshall the tool into a XML file that another PloneMeeting
       site may get through WebDAV.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'tool'

    def marshallSpecificElements(self, tool, res):
        HubSessionsMarshaller.marshallSpecificElements(self, tool, res)
        # Add the URLs of the meeting configs defined in the tool
        meetingConfigs = tool.objectValues('MeetingConfig')
        res.write('<meetingConfigs type="list" count="%d">'%len(meetingConfigs))
        for mc in meetingConfigs:
            self.dumpField(res, 'meetingConfig', mc.absolute_url())
        res.write('</meetingConfigs>')
        meetingGroups = tool.objectValues('MeetingGroup')
        res.write('<meetingGroups type="list" count="%d">' % len(meetingGroups))
        for mg in meetingGroups:
            res.write('<group type="object">')
            self.dumpField(res, 'id', mg.id)
            self.dumpField(res, 'title', mg.Title())
            self.dumpField(res, 'acronym', mg.getAcronym())
            self.dumpField(res, 'url', mg.absolute_url())
            self.dumpField(res, 'active', mg.portal_workflow.getInfoFor(
                mg, 'review_state') == 'active')
            res.write('</group>')
        res.write('</meetingGroups>')

InitializeClass(ToolMarshaller)

# Validation-specific stuff ----------------------------------------------------
from Products.validation.interfaces.IValidator import IValidator
from Products.validation import validation

_PY = 'Please specify a file corresponding to a Python interpreter ' \
      '(ie "/usr/bin/python").'
FILE_NOT_FOUND = 'Path "%s" was not found.'
VALUE_NOT_FILE = 'Path "%s" is not a file. ' + _PY
NO_PYTHON = "Name '%s' does not starts with 'python'. " + _PY
NOT_UNO_ENABLED_PYTHON = '"%s" is not a UNO-enabled Python interpreter. ' \
                         'To check if a Python interpreter is UNO-enabled, ' \
                         'launch it and type "import uno". If you have no ' \
                         'ImportError exception it is ok.'

class UnoEnabledPythonValidator:
    '''Checks that the specified python path corresponds to a UNO-enabled python
       interpreter.'''
    __implements__ = (IValidator, )
    def __init__(self, name):
        self.name = name
    def __call__(self, value, *args, **kwargs):
        if value:
            if not os.path.exists(value):
                return FILE_NOT_FOUND % value
            if not os.path.isfile(value):
                return VALUE_NOT_FILE % value
            if not os.path.basename(value).startswith('python'):
                return NO_PYTHON % value
            if os.system('%s -c "import uno"' % value):
                return NOT_UNO_ENABLED_PYTHON % value
        return True

validation.register(UnoEnabledPythonValidator('unoEnabledPythonValidator'))

##/code-section module-header

schema = Schema((

    StringField(
        name='unoEnabledPython',
        default= defValues.unoEnabledPython,
        widget=StringWidget(
            size=60,
            label="Path of a UNO-enabled Python interpreter (ie /usr/bin/python)",
            description="UnoEnabledPython",
            description_msgid="uno_enabled_python",
            label_msgid='PloneMeeting_label_unoEnabledPython',
            i18n_domain='PloneMeeting',
        ),
        validators=('unoEnabledPythonValidator',)
    ),

    IntegerField(
        name='openOfficePort',
        default= defValues.openOfficePort,
        widget=IntegerField._properties['widget'](
            description="OpenOfficePort",
            description_msgid="open_office_port",
            label='Openofficeport',
            label_msgid='PloneMeeting_label_openOfficePort',
            i18n_domain='PloneMeeting',
        )
    ),

    BooleanField(
        name='ploneDiskAware',
        default= defValues.ploneDiskAware,
        widget=BooleanField._properties['widget'](
            description="PloneDiskAware",
            description_msgid="plone_disk_aware_descr",
            label='Plonediskaware',
            label_msgid='PloneMeeting_label_ploneDiskAware',
            i18n_domain='PloneMeeting',
        )
    ),

    StringField(
        name='meetingFolderTitle',
        default= defValues.meetingFolderTitle,
        widget=StringWidget(
            size=60,
            description="MeetingFolderTitle",
            description_msgid="meeting_folder_title",
            label='Meetingfoldertitle',
            label_msgid='PloneMeeting_label_meetingFolderTitle',
            i18n_domain='PloneMeeting',
        ),
        required=True
    ),

    BooleanField(
        name='navigateLocally',
        default= defValues.navigateLocally,
        widget=BooleanField._properties['widget'](
            description_msgid="navigate_locally",
            description="NavigateLocally",
            label='Navigatelocally',
            label_msgid='PloneMeeting_label_navigateLocally',
            i18n_domain='PloneMeeting',
        )
    ),

    StringField(
        name='functionalAdminEmail',
        default=defValues.functionalAdminEmail,
        widget=StringWidget(
            size=60,
            description="FunctionalAdminEmail",
            description_msgid="functional_admin_email_descr",
            label='Functionaladminemail',
            label_msgid='PloneMeeting_label_functionalAdminEmail',
            i18n_domain='PloneMeeting',
        ),
        validators=('isEmail',)
    ),

    StringField(
        name='functionalAdminName',
        default=defValues.functionalAdminName,
        widget=StringWidget(
            size=60,
            description="FunctionalAdminName",
            description_msgid="functional_admin_name_descr",
            label='Functionaladminname',
            label_msgid='PloneMeeting_label_functionalAdminName',
            i18n_domain='PloneMeeting',
        )
    ),

    StringField(
        name='usedColorSystem',
        default= defValues.usedColorSystem,
        widget=SelectionWidget(
            description="UsedColorSystem",
            description_msgid="used_color_system_descr",
            format="select",
            label='Usedcolorsystem',
            label_msgid='PloneMeeting_label_usedColorSystem',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        vocabulary='listAvailableColorSystems'
    ),

    TextField(
        name='colorSystemDisabledFor',
        default= defValues.colorSystemDisabledFor,
        widget=TextAreaWidget(
            description="ColorSystemDisabledFor",
            description_msgid="color_system_disabled_for_descr",
            label='Colorsystemdisabledfor',
            label_msgid='PloneMeeting_label_colorSystemDisabledFor',
            i18n_domain='PloneMeeting',
        )
    ),

    BooleanField(
        name='restrictUsers',
        default= defValues.restrictUsers,
        widget=BooleanField._properties['widget'](
            description="RestrictUsers",
            description_msgid="restrict_users_descr",
            label='Restrictusers',
            label_msgid='PloneMeeting_label_restrictUsers',
            i18n_domain='PloneMeeting',
        )
    ),

    TextField(
        name='unrestrictedUsers',
        default= defValues.unrestrictedUsers,
        widget=TextAreaWidget(
            description="UnrestrictedUsers",
            description_msgid="unrestricted_users_descr",
            label='Unrestrictedusers',
            label_msgid='PloneMeeting_label_unrestrictedUsers',
            i18n_domain='PloneMeeting',
        )
    ),

    StringField(
        name='dateFormat',
        default= defValues.dateFormat,
        widget=StringWidget(
            description="DateFormat",
            description_msgid="date_format_descr",
            label='Dateformat',
            label_msgid='PloneMeeting_label_dateFormat',
            i18n_domain='PloneMeeting',
        ),
        required=True
    ),

    BooleanField(
        name='extractTextFromFiles',
        default= defValues.extractTextFromFiles,
        widget=BooleanField._properties['widget'](
            description="ExtractTextFromFiles",
            description_msgid="extract_text_from_files_descr",
            label='Extracttextfromfiles',
            label_msgid='PloneMeeting_label_extractTextFromFiles',
            i18n_domain='PloneMeeting',
        )
    ),

    LinesField(
        name='availableOcrLanguages',
        default= defValues.availableOcrLanguages,
        widget=MultiSelectionWidget(
            description="AvailableOcrLanguages",
            description_msgid="available_ocr_languages_descr",
            format="checkbox",
            label='Availableocrlanguages',
            label_msgid='PloneMeeting_label_availableOcrLanguages',
            i18n_domain='PloneMeeting',
        ),
        multiValued=1,
        vocabulary='listOcrLanguages'
    ),

    StringField(
        name='defaultOcrLanguage',
        default= defValues.defaultOcrLanguage,
        widget=SelectionWidget(
            description="DefaultOcrLanguage",
            description_msgid="default_ocr_language_descr",
            label='Defaultocrlanguage',
            label_msgid='PloneMeeting_label_defaultOcrLanguage',
            i18n_domain='PloneMeeting',
        ),
        vocabulary='listOcrLanguages'
    ),

    IntegerField(
        name='maxSearchResults',
        default= defValues.maxSearchResults,
        widget=IntegerField._properties['widget'](
            description="MaxSearchResults",
            description_msgid="max_search_results_descr",
            label='Maxsearchresults',
            label_msgid='PloneMeeting_label_maxSearchResults',
            i18n_domain='PloneMeeting',
        ),
        schemata="pm_search"
    ),

    IntegerField(
        name='maxShownFoundItems',
        default= defValues.maxShownFoundItems,
        widget=IntegerField._properties['widget'](
            description="MaxShownFoundItems",
            description_msgid="max_shown_found_items_descr",
            label='Maxshownfounditems',
            label_msgid='PloneMeeting_label_maxShownFoundItems',
            i18n_domain='PloneMeeting',
        ),
        schemata="pm_search"
    ),

    IntegerField(
        name='maxShownFoundMeetings',
        default= defValues.maxShownFoundMeetings,
        widget=IntegerField._properties['widget'](
            description="MaxShownFoundMeetings",
            description_msgid="max_shown_found_meetings_descr",
            label='Maxshownfoundmeetings',
            label_msgid='PloneMeeting_label_maxShownFoundMeetings',
            i18n_domain='PloneMeeting',
        ),
        schemata="pm_search"
    ),

    IntegerField(
        name='maxShownFoundAnnexes',
        default= defValues.maxShownFoundAnnexes,
        widget=IntegerField._properties['widget'](
            description="MaxShownFoundAnnexes",
            description_msgid="max_shown_found_annexes_descr",
            label='Maxshownfoundannexes',
            label_msgid='PloneMeeting_label_maxShownFoundAnnexes',
            i18n_domain='PloneMeeting',
        ),
        schemata="pm_search"
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

ToolPloneMeeting_schema = OrderedBaseFolderSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
ToolPloneMeeting_schema = ModelExtender(ToolPloneMeeting_schema, 'tool').run()
# Register the marshaller for DAV/XML export.
ToolPloneMeeting_schema.registerLayer('marshall', ToolMarshaller())
##/code-section after-schema

class ToolPloneMeeting(UniqueObject, OrderedBaseFolder):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(UniqueObject,'__implements__',()),) + (getattr(OrderedBaseFolder,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'PloneMeeting'

    meta_type = 'ToolPloneMeeting'
    portal_type = 'ToolPloneMeeting'
    allowed_content_types = ['MeetingConfig', 'MeetingGroup', 'ExternalApplication']
    filter_content_types = 1
    global_allow = 0
    #content_icon = 'ToolPloneMeeting.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "PloneMeeting"
    typeDescMsgId = 'description_edit_toolplonemeeting'
    #toolicon = 'ToolPloneMeeting.gif'


    actions =  (


       {'action': "string:$object_url/base_metadata",
        'category': "object",
        'id': 'metadata',
        'name': 'Properties',
        'permissions': ("Manage portal",),
        'condition': 'python:1'
       },


    )

    _at_rename_after_creation = True

    schema = ToolPloneMeeting_schema

    ##code-section class-header #fill in your manual code here
    schema = schema.copy()
    schema["id"].widget.visible = False
    schema["title"].widget.visible = False

    left_slots = ['here/portlet_prefs/macros/portlet']
    right_slots = []
    ploneDiskActions = ('copy', 'cut', 'folderContents', 'paste', 'delete',
                        'rename')
    ploneMeetingTypes = ('MeetingItem', 'MeetingFile')
    __dav_marshall__ = True # Tool is folderish so normally it can't be
    # marshalled through WebDAV.
    topicResultAction = {'category': 'document_actions', 'available': True,
      'title': 'show_or_hide_details',
      'url': 'javascript:toggleMeetingDescriptions()',
      'name': 'Print this page', 'visible': True, 'allowed': True,
      'id': 'toggleDescriptions', 'permissions': ('View',)}
    ocrLanguages = ('eng', 'fra', 'deu', 'ita', 'nld', 'por', 'spa', 'vie')
    ##/code-section class-header


    # tool-constructors have no id argument, the id is fixed
    def __init__(self, id=None):
        OrderedBaseFolder.__init__(self,'portal_plonemeeting')
        self.setTitle('PloneMeeting')
        
        ##code-section constructor-footer #fill in your manual code here
        ##/code-section constructor-footer


    # tool should not appear in portal_catalog
    def at_post_edit_script(self):
        self.unindexObject()
        
        ##code-section post-edit-method-footer #fill in your manual code here
        self.updatePloneDiskActions()
        self.adapted().onEdit(isCreated=False)
        ##/code-section post-edit-method-footer


    # Methods

    # Manually created methods

    security.declarePrivate('updatePloneDiskActions')
    def updatePloneDiskActions(self):
        '''Shows or hides plone-disk-related actions depending on attribute
          ploneDiskAware.'''
        visibility = False
        if self.getPloneDiskAware():
            visibility = True
        for action in self.portal_actions.listActions():
            if action.id in self.ploneDiskActions:
                action.visible = visibility

    security.declarePublic('at_post_create_script')
    def at_post_create_script(self):
        self.updatePloneDiskActions()
        self.adapted().onEdit(isCreated=True)

    security.declarePublic('getActiveGroups')
    def getActiveGroups(self, notEmptySuffix=None):
        '''Gets the groups that are active. Moreover, we check that group
           suffixes passed as argument are not empty.  If it is the case, we do
           not return the group neither.'''
        res = []
        for group in self.objectValues('MeetingGroup'):
            if self.portal_workflow.getInfoFor(group, 'review_state') == \
               'active':
                # Check that there is at least one user in the notEmptySuffix
                # of the Plone group
                if notEmptySuffix:
                    ploneGroupId = group.getPloneGroupId(suffix=notEmptySuffix)
                    if len(self.portal_groups.getGroupMembers(ploneGroupId)):
                        res.append(group)
                else:
                    res.append(group)
        return res

    security.declarePublic('getUserPloneGroups')
    def getUserPloneGroups(self, userId=None, active=True, suffix=None):
        '''Gets the plone groups linked to MeetingGroup of the authenticated
           user or p_userId instead if given.'''
        if userId:
            user = self.portal_membership.getMemberById(userId)
        else:
            user = self.portal_membership.getAuthenticatedMember()
        res = []
        if active:
            active_groups = [group.getId() for group in self.getActiveGroups()]
        for groupId in self.portal_groups.getGroupsForPrincipal(user):
            if suffix and not groupId.endswith("_%s" % suffix):
                # If we received a suffix, just returned the right suffixed
                # Plone groups
                continue
            group = self.portal_groups.getGroupById(groupId)
            props = group.getProperties()
            if props.has_key('meetingGroupId') and \
               props['meetingGroupId']:
                if active and props['meetingGroupId'] not in active_groups:
                    continue
                res.append(group)
        return res

    security.declarePublic('getUserMeetingGroups')
    def getUserMeetingGroups(self, userId=None, active=True, suffix=None):
        '''Gets a list of MeetingGroups the user is member of.'''
        res = []
        for group in self.getUserPloneGroups(
            userId=userId, active=active, suffix=suffix):
            groupId = group.getProperties()['meetingGroupId']
            group = getattr(self.aq_base, groupId, None)
            if group and (group not in res):
                res.append(group)
        return res

    security.declarePublic('getPloneMeetingFolder')
    def getPloneMeetingFolder(self, meetingConfigId, userId=None):
        '''Returns the folder, within the member area, that corresponds to
           p_meetingConfigId. If this folder and its parent folder ("My
           meetings" folder) do not exist, they are created.'''
        portal = getToolByName(self, 'portal_url').getPortalObject()
        home_folder = portal.portal_membership.getHomeFolder(userId)
        if home_folder is None: # Necessary for the admin zope user
            return portal
        if not hasattr(home_folder, ROOT_FOLDER):
            # Create the "My meetings" folder
            home_folder.invokeFactory('Folder', ROOT_FOLDER,
                                      title=self.getMeetingFolderTitle())
            rootFolder = getattr(home_folder, ROOT_FOLDER)
            rootFolder.setConstrainTypesMode(1)
            rootFolder.setLocallyAllowedTypes(['Folder', 'Large Plone Folder'])
            rootFolder.setImmediatelyAddableTypes(
                ['Folder', 'Large Plone Folder'])
            # If "navigateLocally" is True, we set rootFolder as
            # INavigationRoot.
            # Beware that the home portlet will follow this and will point on
            # the local INavigationRoot. The solution is to change the action
            # index_html to set "string:${portal/portal_url/getPortalPath}".
            if self.getNavigateLocally():
                directlyProvides(rootFolder, INavigationRoot)
                rootFolder.reindexObject()

        root_folder = getattr(home_folder, ROOT_FOLDER)
        if not hasattr(root_folder, meetingConfigId):
            # We call here a python script containing only a call to
            # createPloneMeetingFolder()
            # We do so to permit to another product to overwrite the script to
            # do more in another context (like in the Container product)
            portal.create_meetingconfig_folder(meetingConfigId, userId)
        return getattr(root_folder, meetingConfigId)

    security.declarePublic('createMeetingConfigFolder')
    def createMeetingConfigFolder(self, meetingConfigId, userId):
        '''Creates, within the "My meetings" folder, the sub-folder
           corresponding to p_meetingConfigId'''
        portal = getToolByName(self, 'portal_url').getPortalObject()
        root_folder = getattr(portal.portal_membership.getHomeFolder(userId),
                              ROOT_FOLDER)
        meetingConfig = getattr(self, meetingConfigId)
        # Allow to create large plone folders
        #if the user is NOT plone disk aware, we create a Large Plone Folder
        #else, we create a common ATFolder...
        if not self.getPloneDiskAware():
            getattr(portal.portal_types, 'Large Plone Folder').global_allow = 1
            root_folder.invokeFactory('Large Plone Folder', meetingConfigId,
                                  title=meetingConfig.getFolderTitle())
            getattr(portal.portal_types, 'Large Plone Folder').global_allow = 0
        else:
            #add a common folder because 'Large Plone Folder' does not
            #bring us every needed functionnalities if we want to
            #browse thru folders
            root_folder.invokeFactory('Folder', meetingConfigId,
                                  title=meetingConfig.getFolderTitle())

        mc_folder = getattr(root_folder, meetingConfigId)
        # We add the MEETING_CONFIG property to the folder
        mc_folder.manage_addProperty(MEETING_CONFIG, meetingConfigId, 'string')
        mc_folder.setLayout('meetingfolder_redirect_view')
        mc_folder.setConstrainTypesMode(1)
        allowedTypes = [meetingConfig.getItemTypeName(), \
                        meetingConfig.getMeetingTypeName()] + \
                       ['Document', 'Image', 'File', 'Folder', 'MeetingFile']
        mc_folder.setLocallyAllowedTypes(allowedTypes)
        if self.getPloneDiskAware():
            mc_folder.setImmediatelyAddableTypes(allowedTypes[:-1])
        else:
            mc_folder.setImmediatelyAddableTypes([])
        # Define permissions on this folder. Some remarks:
        # * We override here default permissions/roles mappings as initially
        #   defined in config.py through calls to Products.CMFCore.permissions.
        #   setDefaultRoles (as generated by ArchGenXML). Indeed,
        #   setDefaultRoles may only specify the default Zope roles (Manager,
        #   Owner, Member) but we need to specify PloneMeeting-specific roles.
        # * By setting those permissions, we give "too much" permissions;
        #   security will be more constraining thanks to workflows linked to
        #   content types whose instances will be stored in this folder.
        # * The "write_permission" on field "MeetingItem.annexes" is set on
        #   "PloneMeeting: Add annex". It means that people having this
        #   permission may also disassociate annexes from items.
        mc_folder.manage_permission('Add portal content', ('Owner',), acquire=0)
        mc_folder.manage_permission(ADD_CONTENT_PERMISSIONS['MeetingItem'],
            ('Owner',), acquire=0)
        mc_folder.manage_permission(ADD_CONTENT_PERMISSIONS['Meeting'],
            ('MeetingManager',), acquire=0)
        # The following permission is needed for storing pod-generated documents
        # representing items or meetings directly into the ZODB (useful for
        # exporting data through WebDAV or for freezing the generated doc)
        mc_folder.manage_permission('ATContentTypes: Add File',
            ploneMeetingUpdaters, acquire=0)
        # Only Manager may change the set of allowable types in folders.
        mc_folder.manage_permission(ATCTPermissions.ModifyConstrainTypes,
            ['Manager'], acquire=0)

    security.declarePublic('getMeetingConfig')
    def getMeetingConfig(self, context):
        '''Based on p_context's portal type, we get the corresponding meeting
           config.'''
        res = None
        portalTypeName = context.getPortalTypeName()
        if portalTypeName in ('MeetingItem', 'Meeting'):
            # Archetypes bug. When this method is called within a default_method
            # (when displaying a edit form), the portal_type is not already
            # correctly set (it is equal to the meta_type, which is not
            # necessarily equal to the portal type). In this case we look for
            # the correct portal type in the request.
            portalTypeName = self.REQUEST.get('type_name', None)
        # Find config based on portal type of current p_context
        for config in self.objectValues('MeetingConfig'):
            if (portalTypeName == config.getItemTypeName()) or \
               (portalTypeName == config.getMeetingTypeName()):
                res = config
                break
        if not res:
            # Get the property on the folder that indicates that this is the
            # "official" folder of a meeting config.
            try:
                res = getattr(self, context.aq_acquire(MEETING_CONFIG))
            except AttributeError:
                res = None
        return res

    security.declarePublic('createMeetingConfigFolder')
    def createMeetingConfig(self, configData, source):
        '''Creates a new meeting configuration from p_configData which is a
           MeetingConfigDescriptor instance. If p_source is a string, it
           corresponds to the absolute path of a profile; additional (binary)
           data like images or templates that need to be attached to some
           sub-objects of the meeting config will be searched there. If not, it
           corresponds to an ExternalApplication instance; additional data has
           been already gathered (in memory, as FileWrapper instances) from
           another Plone site which is was used as base for copying a meeting
           configuration in this site.'''
        self.invokeFactory('MeetingConfig', **configData.getData())
        meetingConfig = getattr(self, configData.id)
        # Validates meeting config (validation seems not to be triggered
        # automatically when an object is created from code).
        errors = meetingConfig.schema.validate(meetingConfig)
        if errors:
            raise PloneMeetingError(
                MEETING_CONFIG_ERROR % meetingConfig.getId(), errors)
        # Goddamned, custom validators do no seem to be called.
        for fieldName in configData.fieldsWithCustomValidators:
            exec 'fieldValue = meetingConfig.get%s%s()' % (
                fieldName[0].upper(), fieldName[1:])
            for validator in meetingConfig.getField(fieldName).validators:
                res = validator[0](fieldValue, instance=meetingConfig)
                if not isinstance(res, bool):
                    raise PloneMeetingError(
                        MEETING_CONFIG_FIELD_ERROR % (
                            fieldName, meetingConfig.getId(), res))
        # Goddamned end.
        meetingConfig._at_creation_flag = False # It seems that this flag,
        # internal to Archetypes, is not set when the meeting config is
        # created from code, not through-the-web. So we force it here.
        # This way, once we will update the meeting config through-the-web,
        # at_post_create_script will not be called again, but
        # at_post_edit_script instead.
        meetingConfig.at_post_create_script() # Is called automatically only
        # when the object is created through-the-web.
        if not configData.active:
            self.portal_workflow.doActionFor(meetingConfig, 'deactivate')
        # Adds the sub-objects within the meetingConfig (categories,
        # classifiers, pod templates, etc).
        for catDescr in configData.categories:
            meetingConfig.addCategory(catDescr, False)
        for catDescr in configData.classifiers:
            meetingConfig.addCategory(catDescr, True)
        for recItemDescr in configData.recurringItems:
            meetingConfig.addRecurringItem(recItemDescr)
        for ft in configData.meetingFileTypes:
            meetingConfig.addFileType(ft, source)
        for maal in configData.agreementLevels:
            meetingConfig.addAgreementLevel(maal, source)
        for podTemplateDescr in configData.podTemplates:
            meetingConfig.addPodTemplate(podTemplateDescr, source)
        for mud in configData.meetingUsers:
            meetingConfig.addMeetingUser(mud, source)
        return meetingConfig

    security.declarePublic('getDefaultMeetingConfig')
    def getDefaultMeetingConfig(self):
        '''Gets the default meeting config.'''
        res = None
        for config in self.objectValues('MeetingConfig'):
            if config.isDefault:
                res = config
                break
        return res

    security.declarePublic('getJsCompliantString')
    def getJsCompliantString(self, s):
        '''Returns p_s that can be inserted into a Javascript variable,
           without (double-)quotes problems.'''
        res = s.replace('"', r'\"')
        res = res.replace("'", r"\'")
        return res

    security.declarePublic('checkMayView')
    def checkMayView(self, value):
        '''Check if we have the 'View' permission on p_value which can be an
           object or a brain. We use this because checkPermission('View',
           brain.getObject()) raises Unauthorized when the brain comes from
           the portal_catalog (not from the uid_catalog, because getObject()
           has been overridden in this tool and does an unrestrictedTraverse
           to the object.'''
        klassName = value.__class__.__name__
        if klassName in ('MeetingItem', 'Meeting'):
            obj = value
        else:
            # It is a brain
            obj = self.unrestrictedTraverse(value.getPath())
        return getSecurityManager().checkPermission(View, obj)

    security.declarePublic('isPloneMeetingUser')
    def isPloneMeetingUser(self):
        '''Is the current user a PloneMeeting user (ie, does it have at least
           one of the roles used in PloneMeeting ?'''
        res = False
        user = self.portal_membership.getAuthenticatedMember()
        if user:
            for role in user.getRoles():
                if role in ploneMeetingRoles:
                    res = True
                    break
        return res

    security.declarePublic('isInPloneMeeting')
    def isInPloneMeeting(self, context):
        '''Is the user 'in' PloneMeeting (ie somewhere in PloneMeeting-related
           folders that are created within member folders)?'''
        try:
            context.aq_acquire(MEETING_CONFIG)
            res = True
        except AttributeError:
            res = False
        return res

    security.declarePublic('showPloneMeetingTab')
    def showPloneMeetingTab(self, meetingConfigId):
        '''I show the PloneMeeting tabs (corresponding to meeting configs) if
           the user has one of the PloneMeeting roles and if the meeting config
           is active.'''
        # Is the meeting config active ?
        try:
            meetingConfig = getattr(self, meetingConfigId)
        except AttributeError:
            return False
        if self.portal_workflow.getInfoFor(meetingConfig, 'review_state') == \
           'inactive':
            return False
        # Has the current user the permission to see the meeting config ?
        user = self.portal_membership.getAuthenticatedMember()
        if not user.has_permission(AccessContentsInformation, meetingConfig):
            return False
        return True

    security.declarePublic('getUserName')
    def getUserName(self, userId):
        '''Returns the full name of user having id p_userId.'''
        res = userId
        user = self.portal_membership.getMemberById(userId)
        if user:
            fullName = user.getProperty('fullname')
            if fullName:
                res = fullName
        return res

    security.declarePublic('rememberAccess')
    def rememberAccess(self, uid, commitNeeded=True):
        '''Remember the fact that the currently logged user just accessed
           object with p_uid.'''
        if self.getUsedColorSystem() == "modification_color":
            member = self.portal_membership.getAuthenticatedMember()
            memberId = member.getId()
            if not self.accessInfo.has_key(memberId):
                self.accessInfo[memberId] = OOBTree()
            self.accessInfo[memberId][uid] = DateTime() # Now
            if commitNeeded:
                transaction.commit()

    security.declarePublic('lastModifsConsultedOn')
    def lastModifsConsultedOn(self, uid, objModifDate):
        '''Did the user already consult last modifications made on obj with uid
           p_uid and that was last modified on p_objModifDate ?'''
        res = True
        neverConsulted = False
        member = self.portal_membership.getAuthenticatedMember()
        memberId = member.getId()
        if self.accessInfo.has_key(memberId):
            accessInfo = self.accessInfo[memberId]
            if accessInfo.has_key(uid):
                res = accessInfo[uid] > objModifDate
            else:
                res = False
                neverConsulted = True
        else:
            res = False
            neverConsulted = True
        return (res, neverConsulted)

    security.declarePublic('lastModifsConsultedOnAnnexes')
    def lastModifsConsultedOnAnnexes(self, annexes):
        '''Did the user already consult last modifications made on all annexes
           in p_annexes ?'''
        res = True
        for annex in annexes:
            res = res and self.lastModifsConsultedOn(
                annex['uid'], annex['modification_date'])[0]
        return res

    security.declarePublic('lastModifsConsultedOnAdvices')
    def lastModifsConsultedOnAdvices(self, advices):
        '''Did the user already consult last modifications made on all advices
           in p_advices ?'''
        res = True
        for adviceInfo in advices:
            res = res and self.lastModifsConsultedOn(
                adviceInfo['uid'], adviceInfo['modification_date'])[0]
        return res

    security.declarePublic('getColoredLink')
    def getColoredLink(self, obj, showColors, showIcon=False, contentValue=None,
        target='', maxLength=0):
        '''Produces the link to an item or annex with the right color (if the
           colors must be shown depending on p_showColors). p_target optionally
           specifies the 'target' attribute of the 'a' tag.  The maxLength defines
           the number of character to display in case the content of the link is
           too long.'''
        def checkMaxLength(text):
            """
              Check if we need to format the text if it is too long
            """
            if maxLength and len(text) > maxLength:
                return text[:maxLength] + '...'
            return text

        #particular behaviour for annexes and advices
        isAnnexOrAdvice = False

        if obj.__class__.__name__ in self.ploneMeetingTypes:
            uid = obj.UID()
            modifDate = obj.pm_modification_date
            url = obj.absolute_url()
            title = obj.Title()
            if contentValue:
                content = checkMaxLength(contentValue)
            else:
                content = checkMaxLength(title)
        else:
            # It is an annex/advice entry in an annexIndex/adviceIndex
            isAnnexOrAdvice = True
            uid = obj['uid']
            modifDate = obj['modification_date']
            url = obj['url']
            title = obj['Title']
            if showIcon:
                content = '<img src="%s"/><b>1</b>' % obj['iconUrl']
            elif contentValue:
                content = checkMaxLength(contentValue)
            else:
                content = checkMaxLength(title)
        tg = target
        if target: tg = ' target="%s"' % target
        if not showColors:
            # We do not want to colorize the link, we just return a classical
            # link. We apply the 'pmNoNewContent" id so the link is not colored.
            res = '<a href="%s" title="%s" id="pmNoNewContent"%s>%s</a>' % \
                  (url, title, tg, content)
        else:
            # We want to colorize links, but how?
            if self.getUsedColorSystem() == "state_color":
                # We just colorize the link depending on the workflow state of
                # the item
                try:
                    if isAnnexOrAdvice:
                        obj_state = obj['review_state']
                    else:
                        obj_state = self.portal_workflow.getInfoFor(
                            obj, 'review_state')
                    wf_class = "state-%s" % obj_state
                    res = '<a href="%s" title="%s" class="%s"%s>%s</a>' % \
                        (url, title, wf_class, tg, content)
                except (KeyError, WorkflowException):
                    # If there is no workflow associated with the type
                    # catch the exception or error and return a not colored link
                    # this is the case for annexes that does not have an
                    # associated workflow.
                    res = '<a href="%s" title="%s" id="pmNoNewContent"%s>%s' \
                          '</a>' % (url, title, tg, content)
            else:
                # We colorize the link depending on the last modification of the
                # item.
                # Did the user already consult last modifs on the object?
                modifsConsulted, neverConsulted = self.lastModifsConsultedOn(
                    uid, modifDate)
                # Compute href
                href = url
                # If the user did not consult last modification on this object,
                # we need to append a given suffix to the href. This way, the
                # link will not appear as visited and the user will know that he
                # needs to consult the item again because a change occurred on
                # it.
                if (not neverConsulted) and (not modifsConsulted):
                    href += '?time=%f' % time.time()
                # Compute id
                linkId = None
                if modifsConsulted:
                    linkId = 'pmNoNewContent'
                idPart = ''
                if linkId:
                    idPart = ' id="%s"' % linkId
                res = '<a href="%s" title="%s"%s%s>%s</a>' % \
                      (href, title, idPart, tg, content)
        return res

    security.declarePublic('showColorsForUser')
    def showColorsForUser(self):
        '''Must I show the colors from the color system for the current user?'''
        res = False
        # If we choosed to use a coloration model, we check if we have to show
        # colors to the current user.
        if self.getUsedColorSystem() != 'no_color':
            res = True
            member = self.portal_membership.getAuthenticatedMember()
            memberId = member.getId()
            usersToExclude = [u.strip() for u in \
                              self.getColorSystemDisabledFor().split('\n')]
            if usersToExclude and (memberId in usersToExclude):
                res = False
        return res

    security.declareProtected('Manage portal', 'purgeAccessInfo')
    def purgeAccessInfo(self):
        '''Removes all entries in self.accessInfo that are related to users that
           do not exist anymore.'''
        toDelete = []
        for memberId in self.accessInfo.iterkeys():
            member = self.portal_membership.getMemberById(memberId)
            if not member:
                toDelete.append(memberId)
        for userId in toDelete:
            del self.accessInfo[userId]
        return toDelete

    security.declarePublic('enterProfiler')
    def enterProfiler(self, methodName):
        from Products.PloneMeeting.tests.profiling import profiler
        profiler.enter(methodName)

    security.declarePublic('leaveProfiler')
    def leaveProfiler(self):
        from Products.PloneMeeting.tests.profiling import profiler
        profiler.leave()

    security.declarePublic('userIsAmong')
    def userIsAmong(self, groupSuffix=''):
        '''Check if the currently logged user is in a 'groupSuffix' Plone
           group.'''
        user = self.portal_membership.getAuthenticatedMember()
        res = False
        for groupId in self.portal_groups.getGroupsForPrincipal(user):
            group = self.portal_groups.getGroupById(groupId)
            props = group.getProperties()
            if props.has_key('meetingRole') and \
               (props['meetingRole'] == MEETINGROLES[groupSuffix]):
                res = True
                break
        return res

    security.declarePublic('generateDocument')
    def generateDocument(self):
        '''Generates the document from a template specified in the request
           for a given item or meeting whose UID is also in the request. If the
           document is already present in the database, this method does not
           generate it with pod but simply returns the stored document.'''
        templateId = self.REQUEST.get('templateId')
        itemUids = self.REQUEST.get('itemUids', None)
        objectUid = self.REQUEST.get('objectUid')
        obj = self.uid_catalog(UID=objectUid)[0].getObject()
        meetingConfig = self.getMeetingConfig(obj)
        templatesFolder = getattr(meetingConfig, TOOL_FOLDER_POD_TEMPLATES)
        podTemplate = getattr(templatesFolder, templateId)
        objFolder = obj.getParentNode()
        docId = podTemplate.getDocumentId(obj)
        if hasattr(objFolder.aq_base, docId):
            # The doc was frozen in the DB. So return it.
            doc = getattr(objFolder, docId)
            res = doc.index_html(self.REQUEST, self.REQUEST.RESPONSE)
        else:
            oldDocId = '%s.%s' % (obj.id, podTemplate.getPodFormat())
            if hasattr(objFolder.aq_base, oldDocId):
                # Backward compatibility with PloneMeeting <=1.3:
                # The name of the generated files had this format.
                doc = getattr(objFolder.aq_base, oldDocId)
                res = doc.index_html(self.REQUEST, self.REQUEST.RESPONSE)
            else:
                # The doc must be computed by POD. So call POD.
                res = podTemplate.generateDocument(obj, itemUids)
        return res

    security.declarePublic('listAvailableColorSystems')
    def listAvailableColorSystems(self):
        '''Return a list of available color system'''
        res = []
        for cs in colorSystems:
            res.append( (cs, self.utranslate(cs, domain='PloneMeeting')) )
        return DisplayList(tuple(res))

    security.declarePublic('listOcrLanguages')
    def listOcrLanguages(self):
        '''Return the list of OCR languages supported by Tesseract.'''
        res = []
        for lang in self.ocrLanguages:
            res.append( (lang, self.utranslate('language_%s' % lang,
                                               domain='PloneMeeting')) )
        return DisplayList(tuple(res))

    security.declarePublic('getAdviceAgreementLevelById')
    def getAdviceAgreementLevelById(self, meetingConfig, agreementLevelId):
        '''Returns an agreementlevel object found in the meetingConfig with
           the p_agreementLevelId.'''
        agLevFolder = getattr(meetingConfig.aq_inner,
            TOOL_FOLDER_AGREEMENT_LEVELS)
        return getattr(agLevFolder.aq_inner, agreementLevelId)

    security.declarePublic('getAdviceAgreementLevels')
    def getAdviceAgreementLevels(self, meetingConfig, onStates=[]):
        '''Return the agreementlevel objects found in the meetingConfig.
           If onStates is not empty, only objects on state in p_onStates are
           returned.'''
        agLevFolder = getattr(meetingConfig.aq_inner,
            TOOL_FOLDER_AGREEMENT_LEVELS)
        lst=[]
        wft = self.portal_workflow
        for agreementLevel in agLevFolder.objectValues(\
            'MeetingAdviceAgreementLevel'):
            if onStates and \
                wft.getInfoFor(agreementLevel, 'review_state') not in onStates:
                continue
            lst.append(agreementLevel)
        return lst

    security.declarePublic('showMeetingView')
    def showMeetingView(self):
        '''If PloneMeeting is in "Restrict users" mode, the "Meeting view" page
           must not be shown to some users: users that do not have role
           MeetingManager and are not listed in a specific list
           (self.unrestrictedUsers).'''
        restrictMode = self.getRestrictUsers()
        res = True
        if restrictMode:
            user = self.portal_membership.getAuthenticatedMember()
            isManager = user.has_role('MeetingManager') or \
                        user.has_role('Manager')
            if not isManager:
                # Check if the user is in specific list
                if user.id not in [u.strip() for u in \
                                   self.getUnrestrictedUsers().split('\n')]:
                    res = False
        return res

    security.declarePublic('getMeetingGroup')
    def getMeetingGroup(self, ploneGroupId):
        '''Returns the meeting group containing the plone group with id
            p_ploneGroupId.'''
        ploneGroup = self.portal_groups.getGroupById(ploneGroupId)
        props = ploneGroup.getProperties()
        if props.has_key('meetingGroupId') and props['meetingGroupId']:
            return getattr(self.aq_base, props['meetingGroupId'], None)

    security.declarePublic('getItemsList')
    def getItemsList(self, meeting, whichItems, startNumber=1):
        '''On meeting_view, we need to display various lists of items: items,
           late items or available items. This method returns a 5-tuple with:
           (1) the needed list, (2) the total number of items, (3) the batch
           size, (4) the first number of the whole list (which is not 1
           for the list of late items) and (5) the number of the first item
           in the result.'''
        meetingConfig = self.getMeetingConfig(meeting)
        firstNumber = 1
        firstBatchNumber = 1
        if whichItems == 'availableItems':
            batchSize = meetingConfig.getMaxShownAvailableItems()
            res = [b.getObject() for b in meeting.adapted().getAvailableItems()]
            totalNbOfItems = len(res)
        elif whichItems == 'meetingItems':
            batchSize = meetingConfig.getMaxShownMeetingItems()
            res = meeting.getItemsInOrder(batchSize=batchSize,
                                          startNumber=startNumber)
            totalNbOfItems = len(meeting.getRawItems())
            if res: firstBatchNumber = res[0].getItemNumber()
        elif whichItems == 'lateItems':
            batchSize = meetingConfig.getMaxShownLateItems()
            res = meeting.getItemsInOrder(batchSize=batchSize,
                                          startNumber=startNumber, late=True)
            totalNbOfItems = len(meeting.getRawLateItems())
            firstNumber = len(meeting.getRawItems())+1
            if res: firstBatchNumber =res[0].getItemNumber(relativeTo='meeting')
        return res, totalNbOfItems, batchSize, firstNumber, firstBatchNumber

    security.declarePublic('getMissingAdvicesConstants')
    def getMissingAdvicesConstants(self):
        '''Returns the Missing advices" functionnality-related constants.'''
        return [MISSING_ADVICES_ID, MISSING_ADVICES_ICON_URL]

    security.declarePublic('gotoReferer')
    def gotoReferer(self):
        '''This method allows to go back to the referer URL after a script has
           been executed. There are some special cases to manage in the referer
           URL (like managing parameters *StartNumber when we must come back to
           meeting_view which includes paginated lists.'''
        rq = self.REQUEST
        urlBack = rq['HTTP_REFERER']
        if rq.has_key('iStartNumber'):
            # We must come back to the meeting_view and pay attention to
            # pagination.
            if urlBack.find('?') != -1:
                urlBack = urlBack[:urlBack.index('?')]
            urlBack += '?iStartNumber=%s&lStartNumber=%s' % \
                    (rq['iStartNumber'], rq['lStartNumber'])
        return rq.RESPONSE.redirect(urlBack)

    security.declarePublic('batchAdvancedSearch')
    def batchAdvancedSearch(self, brains, topic, REQUEST, batch_size=0):
        '''Returns a Batch object given a list of p_brains.'''
        b_start = REQUEST.get('b_start', 0)
        # if batch_size is different than 0, use it
        # batch_size is used by portlet_todo for example
        # either, if we defined a limit number in the topic, use it
        # or set it to config.py/DEFAULT_TOPIC_ITEM_COUNT
        if batch_size:
            b_size = batch_size
        elif topic.getLimitNumber():
            b_size = topic.getItemCount() or DEFAULT_TOPIC_ITEM_COUNT
        else:
            b_size = DEFAULT_TOPIC_ITEM_COUNT
        batch = Batch(brains, b_size, int(b_start), orphan=0)
        return batch

    security.declarePublic('pasteItems')
    def pasteItems(self, destFolder, copiedData, copyAnnexes=False,
                   copyAdvices=False, newOwnerId=None):
        '''Paste objects (previously copied) in destFolder. If p_newOwnerId
           is specified, it will become the new owner of the item.'''
        meetingConfig = self.getMeetingConfig(destFolder)
        pasteResult = destFolder.manage_pasteObjects(copiedData)
        if not newOwnerId:
            # The new owner will become the currently logged user
            newOwnerId = self.portal_membership.getAuthenticatedMember().getId()
        res = []
        i = -1
        for itemId in pasteResult:
            i += 1
            newItem = getattr(destFolder, itemId['new_id'])
            # Get copied item
            copiedItem = None
            copiedId = _cb_decode(copiedData)[1][i]
            m = OFS.Moniker.loadMoniker(copiedId)
            try:
                copiedItem = m.bind(destFolder.getPhysicalRoot())
            except ConflictError:
                raise
            except:
                raise PloneMeetingError, 'Could not copy.'
            if newItem.__class__.__name__ == "MeetingItem":
                # The creator is kept, redefine it
                self.plone_utils.changeOwnershipOf(newItem, newOwnerId)
                newItem.setCreators( (newOwnerId,) )
                # The creation date is kept, redefine it
                newItem.setCreationDate(newItem.modified())
                # Set some default values that could not be initialized properly
                toDiscussDefault = meetingConfig.getToDiscussDefault()
                newItem.setToDiscuss(toDiscussDefault)
                newItem.getField('classifier').set(
                    newItem, copiedItem.getClassifier())
                    # No counter increment on related category.
                newItem.at_post_create_script()
                # Manage annexes and advices.
                if not copyAnnexes:
                    # Delete the annexes that have been copied.
                    for annex in newItem.objectValues('MeetingFile'):
                        self.removeGivenObject(annex)
                else:
                    # Recreate the references to annexes: the copy/paste does
                    # not handle this correctly.
                    for annexType in ('Annexes', 'AnnexesDecision'):
                        exec 'oldAnnexes = copiedItem.get%s()' % annexType
                        newAnnexes = []
                        for annex in oldAnnexes:
                            newAnnex = getattr(newItem, annex.id)
                            newAnnex.setMeetingFileType(
                                annex.getMeetingFileType())
                            newAnnexes.append(newAnnex)
                        exec 'newItem.set%s(newAnnexes)' % annexType
                        exec 'for a in newItem.get%s(): ' \
                             'a.updateAnnexSecurity()' % annexType
                if not copyAdvices:
                    for advice in newItem.objectValues('MeetingAdvice'):
                        self.removeGivenObject(advice)
                # Recompute indexes.
                newItem.updateAnnexIndex()
                newItem.updateAdviceIndex()
                res.append(newItem)
        return res

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'ToolPloneMeeting': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''

    security.declarePublic('deleteObjectsByPaths')
    def deleteObjectsByPaths(self, paths):
        '''This method is used by the meetingfolder_view. We receive a list of
           p_paths and we try to remove the elements using deletegiven_uid.'''
        failure = {}
        success = []
        # Use the portal for traversal in case we have relative paths
        portal = getToolByName(self, 'portal_url').getPortalObject()
        traverse = portal.restrictedTraverse
        try:
            for path in paths:
                obj = traverse(path)
                # Check here that we have 'Delete objects' on the object.
                if not self.portal_membership.checkPermission(
                    'Delete objects', obj):
                    raise Exception, "can_not_delete_object"
                res = portal.delete_givenuid(obj.UID())
                if not "object_deleted" in res:
                    # Take the last part of the url+portalMessage wich is the
                    # untranslated i18n msgid.
                    raise Exception, res.split('=')[-1]
                success.append('%s (%s)' % (obj.title_or_id(), path))
        except Exception, e:
            failure = e
        return success, failure

    security.declarePublic('showTodoPortlet')
    def showTodoPortlet(self, context):
        '''Must we show the portlet_todo ?'''
        meetingConfig = self.getMeetingConfig(context)
        if self.isPloneMeetingUser() and self.isInPloneMeeting(context) and \
           (meetingConfig and meetingConfig.getToDoListTopics()) and \
           (meetingConfig and meetingConfig.getTopicsForPortletToDo()):
            return True
        return False

    security.declarePublic('readCookie')
    def readCookie(self, key):
        '''Returns the cookie value at p_key.'''
        httpCookie = self.REQUEST.get('HTTP_COOKIE', '')
        res = None
        indexKey = httpCookie.find(key)
        if indexKey != -1:
            res = httpCookie[indexKey+len(key)+1:]
            sepIndex = res.find(';')
            if sepIndex != -1:
                res = res[:sepIndex]
        return res

    security.declarePublic('addTopicResultAction')
    def addTopicResultAction(self, actions, topic):
        '''Adds a virtual action to be shown when topic results are show, in
           order to be able to toggle item descriptions when displaying lists
           of items outside a meeting (=result of a topic view).'''
        if topic.getProperty('meeting_topic_type') == 'MeetingItem':
            actions['document_actions'].append(self.topicResultAction)

    security.declarePublic('addExternalApplications')
    def addExternalApplications(self, extApps):
        '''Adds external applications to the tool from p_textApps which is a
           list of ExternalApplicationDescriptor instances.'''
        for extApp in extApps:
            self.invokeFactory('ExternalApplication', **extApp.__dict__)

    security.declarePublic('addUser')
    def addUser(self, userData):
        '''Adds a new Plone user from p_userData which is a UserDescriptor
           instance if it does not already exist.'''
        if userData.id not in self.acl_users.source_users.getUserNames():
            self.portal_registration.addMember(
                userData.id, userData.password,
                ['Member'] + userData.globalRoles,
                properties={'username': userData.id, 'email': userData.email,
                            'fullname': userData.fullname or ''})
            # Add the user to some Plone groups
            groupsTool = self.portal_groups
            for groupDescr in userData.ploneGroups:
                # Create the group if it does not exist
                if not groupsTool.getGroupById(userData.id):
                    groupsTool.addGroup(userData.id, title=groupDescr.title)
                    groupsTool.setRolesForGroup(groupDescr.id, groupDescr.roles)
                groupsTool.addPrincipalToGroup(userData.id, groupDescr.id)

    security.declarePublic('addUsersAndGroups')
    def addUsersAndGroups(self, groups, usersOutsideGroups=[]):
        '''Creates MeetingGroups (and potentially Plone users in it) in the
           tool based on p_groups which is a list of GroupDescriptor instances.
           if p_usersOutsideGroups is not empty, it is a list of UserDescriptor
           instances that will serve to create the corresponding Plone users.'''
        groupsTool = self.portal_groups
        for groupDescr in groups:
            self.invokeFactory('MeetingGroup', **groupDescr.getData())
            group = getattr(self, groupDescr.id)
            group._at_creation_flag = False
            # See note on _at_creation_flag attr below.
            group.at_post_create_script()
            # Create users
            for userDescr in groupDescr.getUsers(): self.addUser(userDescr)
            # Add users in the correct Plone groups.
            for groupSuffix in MEETINGROLES.iterkeys():
                groupId = group.getPloneGroupId(groupSuffix)
                for userDescr in getattr(groupDescr, groupSuffix):
                    if userDescr.id not in groupsTool.getGroupMembers(groupId):
                        groupsTool.addPrincipalToGroup(userDescr.id, groupId)
            if not groupDescr.active:
                self.portal_workflow.doActionFor(group, 'deactivate')
        # Create users that are outside any PloneMeeting group (like WebDAV
        # users)
        for userDescr in usersOutsideGroups: self.addUser(userDescr)

    security.declarePublic('performAdvancedSearch')
    def performAdvancedSearch(self):
        '''Performs an advanced search and returns the search results.'''
        return Searcher(self).run()

    security.declarePublic('getTopicResults')
    def getTopicResults(self, topic):
        '''This method computes results of p_topic.'''
        rq = self.REQUEST
        scriptId = rq.get('scriptId', None)
        if scriptId:
            res = getattr(self, scriptId)(topic)
        else:
            res = topic.queryCatalog(batch=True)
        return res

    security.declarePublic('attributeIsUsed')
    def attributeIsUsed(self, objectType, attrName):
        '''Returns True if attribute named p_attrName is used for at least
           one meeting config for p_objectType.'''
        configAttr = None
        if objectType == 'item':
            configAttr = 'getUsedItemAttributes'
        elif objectType == 'meeting':
            configAttr = 'getUsedMeetingAttributes'
        for meetingConfig in self.objectValues('MeetingConfig'):
            if attrName == 'category':
                if not meetingConfig.getUseGroupsAsCategories():
                    return True
            else:
                if attrName in getattr(meetingConfig, configAttr)():
                    if (attrName == 'classifier') and \
                       (len(meetingConfig.classifiers.objectIds()) > 130):
                        # The selection widget currently used is inadequate
                        # for a large number of classifiers. In this case we
                        # should use the popup for selecting classifiers. This
                        # has not been implemented yet, so for the moment if
                        # there are too much classifiers we do as if this field
                        # was not used.
                        return False
                    return True
        return False

    security.declarePublic('getFormattedDate')
    def getFormattedDate(self, aDate, lang=None):
        '''Returns p_aDate as formatted by the user-defined date format defined
           in Archetypes field dateFormat.'''
        fmt = self.getDateFormat()
        u = self.utranslate
        # Manage day of week
        dow = u(weekdaysIds[aDate.dow()], target_language=lang)
        fmt = fmt.replace('%dt', dow.lower())
        fmt = fmt.replace('%DT', dow)
        # Manage month
        month = u(monthsIds[aDate.month()], target_language=lang)
        fmt = fmt.replace('%mt', month.lower())
        fmt = fmt.replace('%MT', month)
        return aDate.strftime(fmt)



registerType(ToolPloneMeeting, PROJECTNAME)
# end of class ToolPloneMeeting

##code-section module-footer #fill in your manual code here
##/code-section module-footer



