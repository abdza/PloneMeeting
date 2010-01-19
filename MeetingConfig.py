# -*- coding: utf-8 -*-
#
# File: MeetingConfig.py
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

##code-section module-header #fill in your manual code here
import os.path
from Globals import InitializeClass
from OFS.Image import File
from OFS.ObjectManager import BeforeDeleteException
from Products.CMFCore.utils import getToolByName
from zope.component import getGlobalSiteManager
from Products.ATReferenceBrowserWidget.ATReferenceBrowserWidget import \
     ReferenceBrowserWidget
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.interfaces import *
from Products.PloneMeeting.utils import getInterface, getCustomAdapter, \
     getCustomSchemaFields, HubSessionsMarshaller
from Products.PloneMeeting.profiles import MeetingConfigDescriptor
from Products.PloneMeeting.Meeting import Meeting_schema
from Products.PloneMeeting.MeetingItem import MeetingItem_schema
from Products.CMFCore.Expression import Expression, createExprContext
defValues = MeetingConfigDescriptor.get()
# This way, I get the default values for some MeetingConfig fields,
# that are defined in a unique place: the MeetingConfigDescriptor class, used
# for importing profiles.
import logging
logger = logging.getLogger('PloneMeeting')

# Marshaller -------------------------------------------------------------------
class ConfigMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a meeting config into a XML file that another
       PloneMeeting site may get through WebDAV.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'meetingConfig'

    def marshallSpecificElements(self, mc, res):
        HubSessionsMarshaller.marshallSpecificElements(self, mc, res)
        # Add the object state
        configState = mc.portal_workflow.getInfoFor(mc, 'review_state')
        self.dumpField(res, 'active', configState == 'active')
        # Add the URLs of the archived meetings in this meeting config
        meetingType = mc.getMeetingTypeName()
        brains = mc.portal_catalog(
            portal_type=meetingType, review_state='archived', sort_on='getDate')
        res.write('<availableMeetings type="list" count="%d">' % len(brains))
        for brain in brains:
            res.write('<meeting type="object">')
            self.dumpField(res, 'id', brain.id)
            self.dumpField(res, 'title', brain.Title)
            self.dumpField(res, 'url', brain.getURL())
            res.write('</meeting>')
        res.write('</availableMeetings>')
        # Adds links to sub-objects
        for folderName, folderInfo in mc.subFoldersInfo.iteritems():
            folder = getattr(mc, folderName)
            res.write('<%s type="list" count="%d">' % \
                (folderName, len(folder.objectIds())))
            for subObject in folder.objectValues():
                self.dumpField(res, 'url', subObject.absolute_url())
            res.write('</%s>' % folderName)

InitializeClass(ConfigMarshaller)

# Definition of validators -----------------------------------------------------
from Products.validation.interfaces.IValidator import IValidator
from Products.validation import validation

# Validation-specific error messages -------------------------------------------
WRONG_INTERFACE = 'You must specify here interface "%s" or a subclass of it.'
NO_ADAPTER_FOUND = 'No adapter was found that provides "%s" for "%s".'

class WorkflowInterfacesValidator:
    '''Checks that declared interfaces exist and that adapters were defined for
       it.'''
    __implements__ = (IValidator, )
    def __init__(self, name, baseInterface, baseWorkflowInterface):
        self.name = name
        self.baseInterface = baseInterface
        self.baseWorkflowInterface = baseWorkflowInterface
    def _getPackageName(self, klass):
        '''Returns the full package name if p_klass.'''
        return '%s.%s' % (klass.__module__, klass.__name__)
    def __call__(self, value, *args, **kwargs):
        obj = kwargs['instance']
        # Get the interface corresponding to the interface name
        # specified in p_value.
        theInterface = None
        try:
           theInterface = getInterface(value)
        except Exception, e:
            return str(e)
        # Check that this interface is self.baseWorkflowInterface or
        # a subclass of it
        if not issubclass(theInterface, self.baseWorkflowInterface):
            return WRONG_INTERFACE % (self._getPackageName(
                                        self.baseWorkflowInterface))
        # Check that there exits an adapter that provides theInterface for
        # self.baseInterface.
        sm = getGlobalSiteManager()
        adapter = sm.adapters.lookup1(self.baseInterface, theInterface)
        if not adapter:
            return NO_ADAPTER_FOUND % (self._getPackageName(theInterface),
                                       self._getPackageName(self.baseInterface))
        return True

validation.register(
    WorkflowInterfacesValidator('itemConditionsInterfaceValidator',
        IMeetingItem, IMeetingItemWorkflowConditions))
validation.register(
    WorkflowInterfacesValidator('itemActionsInterfaceValidator',
        IMeetingItem, IMeetingItemWorkflowActions))
validation.register(
    WorkflowInterfacesValidator('meetingConditionsInterfaceValidator',
        IMeeting, IMeetingWorkflowConditions))
validation.register(
    WorkflowInterfacesValidator('meetingActionsInterfaceValidator',
        IMeeting, IMeetingWorkflowActions))
validation.register(
    WorkflowInterfacesValidator('adviceConditionsInterfaceValidator',
        IMeetingAdvice, IMeetingAdviceWorkflowConditions))
validation.register(
    WorkflowInterfacesValidator('adviceActionsInterfaceValidator',
        IMeetingAdvice, IMeetingAdviceWorkflowActions))

DUPLICATE_SHORT_NAME = 'Short name "%s" is already used by another meeting ' \
                       'configuration. Please choose another one.'
class ShortNameValidator:
    '''Checks that the short name is unique among all meeting configurations.'''
    __implements__ = (IValidator, )
    def __init__(self, name):
        self.name = name
    def __call__(self, value, *args, **kwargs):
        meetingConfig = kwargs['instance']
        for mConfig in meetingConfig.portal_plonemeeting.objectValues(
            'MeetingConfig'):
            if (mConfig != meetingConfig) and \
               (mConfig.getShortName() == value):
                return DUPLICATE_SHORT_NAME % value
        return True

validation.register(ShortNameValidator('shortNameIsUnique'))
# ------------------------------------------------------------------------------
##/code-section module-header

schema = Schema((

    TextField(
        name='assembly',
        default= defValues.assembly,
        widget=TextAreaWidget(
            description="Assembly",
            description_msgid="assembly_descr",
            label='Assembly',
            label_msgid='PloneMeeting_label_assembly',
            i18n_domain='PloneMeeting',
        )
    ),

    TextField(
        name='signatures',
        default= defValues.signatures,
        widget=TextAreaWidget(
            description="Signatures",
            description_msgid="signatures_descr",
            label='Signatures',
            label_msgid='PloneMeeting_label_signatures',
            i18n_domain='PloneMeeting',
        )
    ),

    StringField(
        name='folderTitle',
        widget=StringWidget(
            size=70,
            description="FolderTitle",
            description_msgid="folder_title_descr",
            label='Foldertitle',
            label_msgid='PloneMeeting_label_folderTitle',
            i18n_domain='PloneMeeting',
        ),
        required=True
    ),

    StringField(
        name='shortName',
        widget=StringWidget(
            description="ShortName",
            description_msgid="short_name_descr",
            condition="python: here.portal_factory.isTemporary(here)",
            label='Shortname',
            label_msgid='PloneMeeting_label_shortName',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        validators=('shortNameIsUnique',)
    ),

    BooleanField(
        name='isDefault',
        default= defValues.isDefault,
        widget=BooleanField._properties['widget'](
            description="IsDefault",
            description_msgid="config_is_default_descr",
            label='Isdefault',
            label_msgid='PloneMeeting_label_isDefault',
            i18n_domain='PloneMeeting',
        )
    ),

    IntegerField(
        name='lastItemNumber',
        default=defValues.lastItemNumber,
        widget=IntegerField._properties['widget'](
            description="LastItemNumber",
            description_msgid="last_item_number_descr",
            label='Lastitemnumber',
            label_msgid='PloneMeeting_label_lastItemNumber',
            i18n_domain='PloneMeeting',
        )
    ),

    IntegerField(
        name='lastMeetingNumber',
        default=defValues.lastMeetingNumber,
        widget=IntegerField._properties['widget'](
            description="LastMeetingNumber",
            description_msgid="last_meeting_number_descr",
            label='Lastmeetingnumber',
            label_msgid='PloneMeeting_label_lastMeetingNumber',
            i18n_domain='PloneMeeting',
        )
    ),

    StringField(
        name='configVersion',
        default=defValues.configVersion,
        widget=StringWidget(
            description="ConfigVersion",
            description_msgid="config_version_descr",
            label='Configversion',
            label_msgid='PloneMeeting_label_configVersion',
            i18n_domain='PloneMeeting',
        )
    ),

    LinesField(
        name='usedItemAttributes',
        widget=MultiSelectionWidget(
            description="UsedItemAttributes",
            description_msgid="used_item_attributes_descr",
            label='Useditemattributes',
            label_msgid='PloneMeeting_label_usedItemAttributes',
            i18n_domain='PloneMeeting',
        ),
        schemata="data",
        multiValued=1,
        vocabulary='listUsedItemAttributes',
        default= defValues.usedItemAttributes,
        enforceVocabulary=True
    ),

    LinesField(
        name='usedMeetingAttributes',
        widget=MultiSelectionWidget(
            description="UsedMeetingAttributes",
            description_msgid="used_meeting_attributes_descr",
            label='Usedmeetingattributes',
            label_msgid='PloneMeeting_label_usedMeetingAttributes',
            i18n_domain='PloneMeeting',
        ),
        schemata="data",
        multiValued=1,
        vocabulary='listUsedMeetingAttributes',
        default= defValues.usedMeetingAttributes,
        enforceVocabulary=True
    ),

    BooleanField(
        name='useGroupsAsCategories',
        default= defValues.useGroupsAsCategories,
        widget=BooleanField._properties['widget'](
            description="UseGroupsAsCategories",
            description_msgid="use_groups_as_categories_descr",
            label='Usegroupsascategories',
            label_msgid='PloneMeeting_label_useGroupsAsCategories',
            i18n_domain='PloneMeeting',
        ),
        schemata="data"
    ),

    BooleanField(
        name='toDiscussDefault',
        default= defValues.toDiscussDefault,
        widget=BooleanField._properties['widget'](
            description="ToDiscussDefault",
            description_msgid="to_discuss_default_descr",
            label='Todiscussdefault',
            label_msgid='PloneMeeting_label_toDiscussDefault',
            i18n_domain='PloneMeeting',
        ),
        schemata="data"
    ),

    BooleanField(
        name='toDiscussLateDefault',
        default= defValues.toDiscussLateDefault,
        widget=BooleanField._properties['widget'](
            description="ToDiscussLateDefault",
            description_msgid="to_discuss_late_default_descr",
            label='Todiscusslatedefault',
            label_msgid='PloneMeeting_label_toDiscussLateDefault',
            i18n_domain='PloneMeeting',
        ),
        schemata="data"
    ),

    TextField(
        name='itemReferenceFormat',
        default= defValues.itemReferenceFormat,
        widget=TextAreaWidget(
            description="ItemReferenceFormat",
            description_msgid="item_reference_format_descr",
            label='Itemreferenceformat',
            label_msgid='PloneMeeting_label_itemReferenceFormat',
            i18n_domain='PloneMeeting',
        ),
        schemata="data"
    ),

    StringField(
        name='sortingMethodOnAddItem',
        default= defValues.sortingMethodOnAddItem,
        widget=SelectionWidget(
            description="sortingMethodOnAddItem",
            description_msgid="sorting_method_on_add_item_descr",
            format="select",
            label='Sortingmethodonadditem',
            label_msgid='PloneMeeting_label_sortingMethodOnAddItem',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        schemata="data",
        vocabulary='listSortingMethods'
    ),

    TextField(
        name='allItemTags',
        default= defValues.allItemTags,
        widget=TextAreaWidget(
            description="AllItemTags",
            description_msgid="all_item_tags_descr",
            label='Allitemtags',
            label_msgid='PloneMeeting_label_allItemTags',
            i18n_domain='PloneMeeting',
        ),
        schemata="data"
    ),

    BooleanField(
        name='sortAllItemTags',
        default= defValues.sortAllItemTags,
        widget=BooleanField._properties['widget'](
            description="SortAllItemTags",
            description_msgid="sort_all_item_tags_descr",
            label='Sortallitemtags',
            label_msgid='PloneMeeting_label_sortAllItemTags',
            i18n_domain='PloneMeeting',
        ),
        schemata="data"
    ),

    LinesField(
        name='recordItemHistoryStates',
        widget=MultiSelectionWidget(
            description="RecordItemHistoryStates",
            description_msgid="record_item_history_states_descr",
            label='Recorditemhistorystates',
            label_msgid='PloneMeeting_label_recordItemHistoryStates',
            i18n_domain='PloneMeeting',
        ),
        schemata="data",
        multiValued=1,
        vocabulary='listItemStates',
        default= defValues.recordItemHistoryStates,
        enforceVocabulary=True
    ),

    StringField(
        name='itemWorkflow',
        widget=SelectionWidget(
            format="select",
            description="ItemWorkflow",
            description_msgid="item_workflow_descr",
            label='Itemworkflow',
            label_msgid='PloneMeeting_label_itemWorkflow',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        schemata="workflow",
        vocabulary='listWorkflows',
        default= defValues.itemWorkflow,
        enforceVocabulary=True
    ),

    StringField(
        name='itemConditionsInterface',
        default= defValues.itemConditionsInterface,
        widget=StringWidget(
            size=70,
            description="ItemConditionsInterface",
            description_msgid="item_conditions_interface_descr",
            label='Itemconditionsinterface',
            label_msgid='PloneMeeting_label_itemConditionsInterface',
            i18n_domain='PloneMeeting',
        ),
        schemata="workflow",
        validators=('itemConditionsInterfaceValidator',)
    ),

    StringField(
        name='itemActionsInterface',
        default= defValues.itemActionsInterface,
        widget=StringWidget(
            size=70,
            description="ItemActionsInterface",
            description_msgid="item_actions_interface_descr",
            label='Itemactionsinterface',
            label_msgid='PloneMeeting_label_itemActionsInterface',
            i18n_domain='PloneMeeting',
        ),
        schemata="workflow",
        validators=('itemActionsInterfaceValidator',)
    ),

    StringField(
        name='meetingWorkflow',
        widget=SelectionWidget(
            format="select",
            description="MeetingWorkflow",
            description_msgid="meeting_workflow_descr",
            label='Meetingworkflow',
            label_msgid='PloneMeeting_label_meetingWorkflow',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        schemata="workflow",
        vocabulary='listWorkflows',
        default= defValues.meetingWorkflow,
        enforceVocabulary=True
    ),

    StringField(
        name='meetingConditionsInterface',
        default= defValues.meetingConditionsInterface,
        widget=StringWidget(
            size=70,
            description="MeetingConditionsInterface",
            description_msgid="meeting_conditions_interface_descr",
            label='Meetingconditionsinterface',
            label_msgid='PloneMeeting_label_meetingConditionsInterface',
            i18n_domain='PloneMeeting',
        ),
        schemata="workflow",
        validators=('meetingConditionsInterfaceValidator',)
    ),

    StringField(
        name='meetingActionsInterface',
        default= defValues.meetingActionsInterface,
        widget=StringWidget(
            size=70,
            description="MeetingActionsInterface",
            description_msgid="meeting_actions_interface_descr",
            label='Meetingactionsinterface',
            label_msgid='PloneMeeting_label_meetingActionsInterface',
            i18n_domain='PloneMeeting',
        ),
        schemata="workflow",
        validators=('meetingActionsInterfaceValidator',)
    ),

    StringField(
        name='adviceConditionsInterface',
        default= defValues.adviceConditionsInterface,
        widget=StringWidget(
            size=70,
            description="AdviceConditionsInterface",
            description_msgid="advice_conditions_interface_descr",
            label='Adviceconditionsinterface',
            label_msgid='PloneMeeting_label_adviceConditionsInterface',
            i18n_domain='PloneMeeting',
        ),
        schemata="workflow",
        validators=('adviceConditionsInterfaceValidator',)
    ),

    StringField(
        name='adviceActionsInterface',
        default= defValues.adviceActionsInterface,
        widget=StringWidget(
            size=70,
            description="AdviceActionsInterface",
            description_msgid="advice_actions_interface_descr",
            label='Adviceactionsinterface',
            label_msgid='PloneMeeting_label_adviceActionsInterface',
            i18n_domain='PloneMeeting',
        ),
        schemata="workflow",
        validators=('adviceActionsInterfaceValidator',)
    ),

    LinesField(
        name='itemTopicStates',
        widget=MultiSelectionWidget(
            description="ItemTopicStates",
            description_msgid="item_topic_states_descr",
            label='Itemtopicstates',
            label_msgid='PloneMeeting_label_itemTopicStates',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui",
        multiValued=1,
        vocabulary='listItemStates',
        default= defValues.itemTopicStates,
        enforceVocabulary=True
    ),

    LinesField(
        name='meetingTopicStates',
        widget=MultiSelectionWidget(
            description="MeetingTopicStates",
            description_msgid="meeting_topic_states_descr",
            label='Meetingtopicstates',
            label_msgid='PloneMeeting_label_meetingTopicStates',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui",
        multiValued=1,
        vocabulary='listMeetingStates',
        default= defValues.meetingTopicStates,
        enforceVocabulary=True
    ),

    LinesField(
        name='decisionTopicStates',
        widget=MultiSelectionWidget(
            description="DecisionTopicStates",
            description_msgid="decision_topic_states_descr",
            label='Decisiontopicstates',
            label_msgid='PloneMeeting_label_decisionTopicStates',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui",
        multiValued=1,
        vocabulary='listMeetingStates',
        default= defValues.decisionTopicStates,
        enforceVocabulary=True
    ),

    IntegerField(
        name='maxShownMeetings',
        default=defValues.maxShownMeetings,
        widget=IntegerField._properties['widget'](
            description="MaxShownMeetings",
            description_msgid="max_shown_meetings_descr",
            label='Maxshownmeetings',
            label_msgid='PloneMeeting_label_maxShownMeetings',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        schemata="gui"
    ),

    IntegerField(
        name='maxDaysDecisions',
        default= defValues.maxDaysDecisions,
        widget=IntegerField._properties['widget'](
            description="MaxDaysDecision",
            description_msgid="max_days_decisions_descr",
            label='Maxdaysdecisions',
            label_msgid='PloneMeeting_label_maxDaysDecisions',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        schemata="gui"
    ),

    StringField(
        name='meetingAppDefaultView',
        default= defValues.meetingAppDefaultView,
        widget=SelectionWidget(
            description="MeetingAppDefaultView",
            description_msgid="meeting_app_default_view_descr",
            label='Meetingappdefaultview',
            label_msgid='PloneMeeting_label_meetingAppDefaultView',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        schemata="gui",
        vocabulary='listMeetingAppAvailableViews'
    ),

    LinesField(
        name='itemsListVisibleColumns',
        widget=MultiSelectionWidget(
            description="ItemsListVisibleColumns",
            description_msgid="items_list_visible_columns_descr",
            label='Itemslistvisiblecolumns',
            label_msgid='PloneMeeting_label_itemsListVisibleColumns',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui",
        multiValued=1,
        vocabulary='listItemsListVisibleColumns',
        default= defValues.itemsListVisibleColumns,
        enforceVocabulary=True
    ),

    IntegerField(
        name='maxShownAvailableItems',
        default= defValues.maxShownAvailableItems,
        widget=IntegerField._properties['widget'](
            description="MaxShownAvailableItems",
            description_msgid="max_shown_available_items_descr",
            label='Maxshownavailableitems',
            label_msgid='PloneMeeting_label_maxShownAvailableItems',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui"
    ),

    IntegerField(
        name='maxShownMeetingItems',
        default= defValues.maxShownMeetingItems,
        widget=IntegerField._properties['widget'](
            description="MaxShownMeetingitems",
            description_msgid="max_shown_meeting_items_descr",
            label='Maxshownmeetingitems',
            label_msgid='PloneMeeting_label_maxShownMeetingItems',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui"
    ),

    IntegerField(
        name='maxShownLateItems',
        default= defValues.maxShownLateItems,
        widget=IntegerField._properties['widget'](
            description="MaxShownLateItems",
            description_msgid="max_shown_late_items_descr",
            label='Maxshownlateitems',
            label_msgid='PloneMeeting_label_maxShownLateItems',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui"
    ),

    BooleanField(
        name='enableDuplication',
        default= defValues.enableDuplication,
        widget=BooleanField._properties['widget'](
            description="EnableDuplication",
            description_msgid="enable_duplication_descr",
            label='Enableduplication',
            label_msgid='PloneMeeting_label_enableDuplication',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui"
    ),

    BooleanField(
        name='enableGotoPage',
        default= defValues.enableGotoPage,
        widget=BooleanField._properties['widget'](
            description="EnableGotoPage",
            description_msgid="enable_goto_page_descr",
            label='Enablegotopage',
            label_msgid='PloneMeeting_label_enableGotoPage',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui"
    ),

    BooleanField(
        name='enableGotoItem',
        default= defValues.enableGotoItem,
        widget=BooleanField._properties['widget'](
            description="EnableGotoItem",
            description_msgid="enable_goto_item_descr",
            label='Enablegotoitem',
            label_msgid='PloneMeeting_label_enableGotoItem',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui"
    ),

    BooleanField(
        name='openAnnexesInSeparateWindows',
        default= defValues.openAnnexesInSeparateWindows,
        widget=BooleanField._properties['widget'](
            description="OpenAnnexesInSeparateWindows",
            description_msgid="open_annexes_in_separate_windows_descr",
            label='Openannexesinseparatewindows',
            label_msgid='PloneMeeting_label_openAnnexesInSeparateWindows',
            i18n_domain='PloneMeeting',
        ),
        schemata="gui"
    ),

    ReferenceField(
        name='toDoListTopics',
        widget=ReferenceBrowserWidget(
            allow_search=False,
            allow_browse=True,
            description="ToDoListTopics",
            description_msgid="to_do_list_topics",
            startup_directory="getTopicsFolder",
            label='Todolisttopics',
            label_msgid='PloneMeeting_label_toDoListTopics',
            i18n_domain='PloneMeeting',
        ),
        allowed_types=('Topic',),
        schemata="gui",
        multiValued=True,
        relationship="ToDoTopics"
    ),

    LinesField(
        name='mailItemEvents',
        widget=MultiSelectionWidget(
            description="MailItemEvents",
            description_msgid="mail_item_events_descr",
            label='Mailitemevents',
            label_msgid='PloneMeeting_label_mailItemEvents',
            i18n_domain='PloneMeeting',
        ),
        schemata="mail",
        multiValued=1,
        vocabulary='listItemEvents',
        default= defValues.mailItemEvents,
        enforceVocabulary=True
    ),

    LinesField(
        name='mailMeetingEvents',
        widget=MultiSelectionWidget(
            description="MailMeetingEvents",
            description_msgid="mail_meeting_events",
            label='Mailmeetingevents',
            label_msgid='PloneMeeting_label_mailMeetingEvents',
            i18n_domain='PloneMeeting',
        ),
        schemata="mail",
        multiValued=1,
        vocabulary='listMeetingEvents',
        default= defValues.mailMeetingEvents,
        enforceVocabulary=True
    ),

    StringField(
        name='tasksMacro',
        default= defValues.tasksMacro,
        widget=StringWidget(
            size=70,
            description="TasksMacro",
            description_msgid="tasks_macro_descr",
            label='Tasksmacro',
            label_msgid='PloneMeeting_label_tasksMacro',
            i18n_domain='PloneMeeting',
        ),
        schemata="tasks"
    ),

    StringField(
        name='taskCreatorRole',
        default= defValues.taskCreatorRole,
        widget=SelectionWidget(
            description="TaskCreatorRole",
            description_msgid="task_creator_role_descr",
            label='Taskcreatorrole',
            label_msgid='PloneMeeting_label_taskCreatorRole',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        schemata="tasks",
        vocabulary='listRoles'
    ),

    BooleanField(
        name='useAdvices',
        default= defValues.useAdvices,
        widget=BooleanField._properties['widget'](
            description="UseAdvices",
            description_msgid="use_advices_descr",
            label='Useadvices',
            label_msgid='PloneMeeting_label_useAdvices',
            i18n_domain='PloneMeeting',
        ),
        schemata="advices"
    ),

    LinesField(
        name='optionalAdvisers',
        widget=MultiSelectionWidget(
            description="OptionalAdvisers",
            description_msgid="optional_advisers_descr",
            label='Optionaladvisers',
            label_msgid='PloneMeeting_label_optionalAdvisers',
            i18n_domain='PloneMeeting',
        ),
        schemata="advices",
        multiValued=1,
        vocabulary='listOptionalAdvisers',
        default=defValues.optionalAdvisers,
        enforceVocabulary=True
    ),

    BooleanField(
        name='useCopies',
        default= defValues.useCopies,
        widget=BooleanField._properties['widget'](
            description="UseCopies",
            description_msgid="use_copies_descr",
            label='Usecopies',
            label_msgid='PloneMeeting_label_useCopies',
            i18n_domain='PloneMeeting',
        ),
        schemata="advices"
    ),

    LinesField(
        name='selectableCopyGroups',
        widget=MultiSelectionWidget(
            size=20,
            description="SelectableCopyGroups",
            description_msgid="selectable_copy_groups_descr",
            label='Selectablecopygroups',
            label_msgid='PloneMeeting_label_selectableCopyGroups',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        schemata="advices",
        multiValued=1,
        vocabulary='listSelectableCopyGroups'
    ),

    BooleanField(
        name='useVotes',
        default= defValues.useVotes,
        widget=BooleanField._properties['widget'](
            description="UseVotes",
            description_msgid="use_votes_descr",
            label='Usevotes',
            label_msgid='PloneMeeting_label_useVotes',
            i18n_domain='PloneMeeting',
        ),
        schemata="votes"
    ),

    LinesField(
        name='votesEncoder',
        widget=MultiSelectionWidget(
            description="VotesEncoder",
            description_msgid="votes_encoder_descr",
            format="checkbox",
            label='Votesencoder',
            label_msgid='PloneMeeting_label_votesEncoder',
            i18n_domain='PloneMeeting',
        ),
        schemata="votes",
        multiValued=1,
        vocabulary='listVotesEncoders',
        default=defValues.votesEncoder,
        enforceVocabulary=True
    ),

    LinesField(
        name='usedVoteValues',
        widget=MultiSelectionWidget(
            description="UsedVoteValues",
            description_msgid="used_vote_values_descr",
            format="checkbox",
            label='Usedvotevalues',
            label_msgid='PloneMeeting_label_usedVoteValues',
            i18n_domain='PloneMeeting',
        ),
        schemata="votes",
        multiValued=1,
        vocabulary='listAllVoteValues',
        default=defValues.usedVoteValues,
        enforceVocabulary=True
    ),

    StringField(
        name='defaultVoteValue',
        default=defValues.defaultVoteValue,
        widget=SelectionWidget(
            description="DefaultVoteValue",
            description_msgid="default_vote_value_descr",
            label='Defaultvotevalue',
            label_msgid='PloneMeeting_label_defaultVoteValue',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        schemata="votes",
        vocabulary='listAllVoteValues'
    ),

),
)

##code-section after-local-schema #fill in your manual code here
# Error-related constants
ACTION_EXISTS = 'An action with id "%s" already exists.'
##/code-section after-local-schema

MeetingConfig_schema = OrderedBaseFolderSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
MeetingConfig_schema = ModelExtender(MeetingConfig_schema, 'config').run()
# Register the marshaller for DAV/XML export.
MeetingConfig_schema.registerLayer('marshall', ConfigMarshaller())
##/code-section after-schema

class MeetingConfig(OrderedBaseFolder):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(OrderedBaseFolder,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'MeetingConfig'

    meta_type = 'MeetingConfig'
    portal_type = 'MeetingConfig'
    allowed_content_types = ['Folder']
    filter_content_types = 1
    global_allow = 1
    #content_icon = 'MeetingConfig.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "MeetingConfig"
    typeDescMsgId = 'description_edit_meetingconfig'

    _at_rename_after_creation = True

    schema = MeetingConfig_schema

    ##code-section class-header #fill in your manual code here
    # Information about each sub-folder that will be created within a meeting
    # config.
    subFoldersInfo = {
        TOOL_FOLDER_CATEGORIES: ('Categories', 'MeetingCategory', 'categories',
            'CategoryDescriptor'),
        TOOL_FOLDER_CLASSIFIERS: ('Classifiers', 'MeetingCategory',
            'classifiers', 'CategoryDescriptor'),
        TOOL_FOLDER_RECURRING_ITEMS: ('Recurring items', 'itemType', None, ''),
        'topics': ('Topics', 'Topic', None, ''),
        TOOL_FOLDER_FILE_TYPES: ('Meeting file types', 'MeetingFileType',
            'meetingFileTypes', 'MeetingFileTypeDescriptor'),
        TOOL_FOLDER_AGREEMENT_LEVELS: ('Meeting advices agreement levels',
            'MeetingAdviceAgreementLevel', 'agreementLevels',
            'MeetingAdviceAgreementLevelDescriptor'),
        TOOL_FOLDER_POD_TEMPLATES: ('Document templates', 'PodTemplate',
            'podTemplates', 'PodTemplateDescriptor'),
        TOOL_FOLDER_MEETING_USERS: ('Meeting users', 'MeetingUser',
            'meetingUsers', 'MeetingUserDescriptor')
        }
    metaTypes = ('MeetingItem', 'Meeting')
    metaNames = ('Item', 'Meeting')
    defaultWorkflows = ('meetingitem_workflow', 'meeting_workflow')

    # Format is : topicId, a list of topic criteria, a sort_on attribute
    # and a topicScriptId used to manage complex searches.
    topicsInfo = (
        # My items
        ( 'searchmyitems',
        (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
           ('Creator', 'ATCurrentAuthorCriterion', None),
        ), 'created', '',
           "python: here.portal_plonemeeting.userIsAmong('creators')"
        ),
        # All (visible) items
        ( 'searchallitems',
        (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
        ), 'created', '', ''
        ),
        # Items in copy : need a script to do this search.
        ( 'searchallitemsincopy',
        (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
        ), 'created', 'searchItemsInCopy',
           "python: here.portal_plonemeeting.getMeetingConfig(here)." \
           "getUseCopies()"
        ),
        # Items to advice : need a script to do this search.
        ( 'searchallitemstoadvice',
        (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
        ), 'created', 'searchItemsToAdvice',
           "python: here.portal_plonemeeting.userIsAmong('advisers')"
        ),
        # Advised items : need a script to do this search.
        ( 'searchalladviseditems',
        (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
        ), 'created', 'searchAdvisedItems',
           "python: here.portal_plonemeeting.userIsAmong('advisers')"
        ),
        # All not-yet-decided meetings
        ( 'searchallmeetings',
        (  ('Type', 'ATPortalTypeCriterion', 'Meeting'),
        ), 'getDate', '', ''
        ),
        # All decided meetings
        ( 'searchalldecisions',
        ( ('Type', 'ATPortalTypeCriterion', 'Meeting'),
        ), 'getDate', '', ''
        ),
    )

    # List of topics that take care of the states defined in a meetingConfig
    topicsUsingMeetingConfigStates = {
        'MeetingItem' : ('searchmyitems', 'searchallitems', ),
        'Meeting': ('searchallmeetings', 'searchalldecisions', ),
    }
    __dav_marshall__ = True # MeetingConfig is folderish so normally it can't be
    # marshalled through WebDAV.
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePrivate('setAllItemTagsField')
    def setAllItemTagsField(self):
        '''Sets the correct value for the field "allItemTags".'''
        tags = [t.strip() for t in self.getAllItemTags().split('\n')]
        if self.getSortAllItemTags():
            tags.sort()
        self.setAllItemTags('\n'.join(tags))

    security.declarePrivate('listUsedAttributes')
    def listUsedAttributes(self, schema):
        res = []
        for field in schema.fields():
            if hasattr(field, 'optional'):
                res.append((field.getName(), self.utranslate(
                    field.widget.label_msgid, domain=field.widget.i18n_domain)))
        return DisplayList(tuple(res))

    security.declarePrivate('listUsedItemAttributes')
    def listUsedItemAttributes(self):
        return self.listUsedAttributes(MeetingItem_schema)

    security.declarePrivate('listUsedMeetingAttributes')
    def listUsedMeetingAttributes(self):
        return self.listUsedAttributes(Meeting_schema)

    security.declarePrivate('listItemsListVisibleColumns')
    def listItemsListVisibleColumns(self):
        d = 'PloneMeeting'
        res = DisplayList((
                ("state", self.utranslate(
                    'item_state', domain=d)),
                ("creator", self.utranslate(
                    'pm_creator', domain=d)),
                ("categoryOrProposingGroup", self.utranslate(
                    "category_or_proposing_group", domain=d)),
                ("proposingGroupAcronym", self.utranslate(
                    "proposing_group_acronym", domain=d)),
                ("associatedGroups", self.utranslate(
                    "PloneMeeting_label_associatedGroups", domain=d)),
                ("associatedGroupsAcronyms", self.utranslate(
                    "associated_groups_acronyms", domain=d)),
              ))
        return res

    security.declarePrivate('listVotesEncoders')
    def listVotesEncoders(self):
        d = "PloneMeeting"
        res = DisplayList((
            ("aMeetingManager", self.utranslate('a_meeting_manager', domain=d)),
            ("theVoterHimself", self.utranslate('the_voter_himself', domain=d)),
            ))
        return res

    security.declarePrivate('listAllVoteValues')
    def listAllVoteValues(self):
        d = "PloneMeeting"
        u = self.utranslate
        res = DisplayList((
            ("not_yet", u('vote_value_not_yet', domain=d)),
            ("yes", u('vote_value_yes', domain=d)),
            ("no", u('vote_value_no', domain=d)),
            ("abstain", u('vote_value_abstain', domain=d)),
            ("does_not_vote",u('vote_value_does_not_vote',domain=d)),
            ))
        return res

    security.declarePrivate('updatePortalTypes')
    def updatePortalTypes(self):
        '''Reupdates the portal_types in this meeting config.'''
        pt = self.portal_types
        for metaTypeName in self.metaTypes:
            portalTypeName = '%s%s' % (metaTypeName, self.getShortName())
            portalType = getattr(pt, portalTypeName)
            basePortalType = getattr(pt, metaTypeName)
            portalType._actions = tuple(basePortalType._cloneActions())

    security.declarePrivate('registerPortalTypes')
    def registerPortalTypes(self):
        '''Registers, into portal_types, specific item and meeting types
           corresponding to this meeting config.'''
        i = -1
        registeredFactoryTypes = self.portal_factory.getFactoryTypes().keys()
        factoryTypesToRegister = []
        for metaTypeName in self.metaTypes:
            i += 1
            portalTypeName = '%s%s' % (metaTypeName, self.getShortName())
            # If the portal type corresponding to the meta type is
            # registered in portal_factory (in the model:
            # use_portal_factory=True), we must also register the new
            # portal_type we are currently creating.
            if metaTypeName in registeredFactoryTypes:
                factoryTypesToRegister.append(portalTypeName)
            if not hasattr(self.portal_types, portalTypeName):
                typeInfoName = "PloneMeeting: %s (%s)" % (metaTypeName,
                                                          metaTypeName)
                self.portal_types.manage_addTypeInformation(
                    getattr(self.portal_types, metaTypeName).meta_type,
                    id=portalTypeName, typeinfo_name=typeInfoName)
                # Set the human readable title explicitly
                portalType = getattr(self.portal_types, portalTypeName)
                portalType.title = portalTypeName
                # Associate a workflow for this new portal type.
                exec 'workflowName = self.get%sWorkflow()' % self.metaNames[i]
                try:
                    wf = getattr(self.portal_workflow, workflowName)
                except AttributeError:
                    logger.warn('Workflow "%s" was not found. Using "%s" ' \
                                'instead.' %  (workflowName,
                                self.defaultWorkflows[i]))
                    workflowName = self.defaultWorkflows[i]
                self.portal_workflow.setChainForPortalTypes([portalTypeName],
                                                            workflowName)
                # Copy actions from the base portal type
                basePortalType = getattr(self.portal_types, metaTypeName)
                portalType._actions = tuple(basePortalType._cloneActions())
                # If type is MeetingItem-based, associate him with a different
                # workflow in workflow policy portal_plonemeeting_policy
                # moreover, we add the extra portal_types/actions
                if metaTypeName == 'MeetingItem':
                    ppw = self.portal_placeful_workflow
                    toolPolicy = ppw.portal_plonemeeting_policy
                    toolPolicy.setChain(portalTypeName,
                                        ('plonemeeting_onestate_workflow',))

        # Update the factory tool with the list of types to register
        self.portal_factory.manage_setPortalFactoryTypes(
            listOfTypeIds=factoryTypesToRegister+registeredFactoryTypes)

    security.declarePrivate('createTopics')
    def createTopics(self):
        '''Adds a bunch of topics within the 'topics' sub-folder.'''
        for topicId, topicCriteria, sortCriterion, searchScriptId, \
            topic_tal_expr in self.topicsInfo:
            self.topics.invokeFactory('Topic', topicId)
            topic = getattr(self.topics, topicId)
            topic.setExcludeFromNav(True)
            topic.setTitle(topicId)
            mustAddStateCriterium = False
            for criterionName, criterionType, criterionValue in topicCriteria:
                criterion = topic.addCriterion(field=criterionName,
                                               criterion_type=criterionType)
                if criterionValue != None:
                    if criterionType == 'ATPortalTypeCriterion':
                        if criterionValue in ('MeetingItem', 'Meeting'):
                            mustAddStateCriterium = True
                        topic.manage_addProperty(
                            TOPIC_TYPE, criterionValue, 'string')
                        # This is necessary to add a script doing the search
                        # when the it is too complicated for a topic.
                        topic.manage_addProperty(
                            TOPIC_SEARCH_SCRIPT, searchScriptId, 'string')
                        # Add a tal expression property
                        topic.manage_addProperty(
                            TOPIC_TAL_EXPRESSION, topic_tal_expr, 'string')
                        criterionValue = '%s%s' % \
                            (criterionValue, self.getShortName())
                    criterion.setValue([criterionValue])
            if mustAddStateCriterium:
                # We must add a state-related criterium. But for an item or
                # meeting-related topic ?
                if topicId == 'searchallmeetings':
                    getStatesMethod = self.getMeetingTopicStates
                elif topicId == 'searchalldecisions':
                    getStatesMethod = self.getDecisionTopicStates
                else:
                    getStatesMethod = self.getItemTopicStates
                stateCriterion = topic.addCriterion(
                    field='review_state', criterion_type='ATListCriterion')
                stateCriterion.setValue(getStatesMethod())
            topic.setLimitNumber(True)
            topic.setItemCount(20)
            topic.setSortCriterion(sortCriterion, True)
            topic.setCustomView(True)
            topic.setCustomViewFields(['Title', 'CreationDate', 'Creator',
                                       'review_state'])
            topic.reindexObject()

    security.declarePrivate('updateIsDefaultFields')
    def updateIsDefaultFields(self):
        '''If this config becomes the default one, all the others must not be
           default meetings.'''
        otherConfigs = self.getParentNode().objectValues('MeetingConfig')
        if self.getIsDefault():
            # All the others must not be default meeting configs.
            for mConfig in otherConfigs:
                if mConfig != self:
                    mConfig.setIsDefault(False)
        else:
            # At least one other must be the default config
            defConfig = None
            for mConfig in otherConfigs:
                if mConfig.getIsDefault():
                    defConfig = mConfig
                    break
            if not defConfig:
                self.setIsDefault(True)
                msg = self.utranslate('config_is_still_default',
                                      domain='PloneMeeting')
                self.plone_utils.addPortalMessage(msg)

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self):
        '''Create the sub-folders of a meeting config, that will contain
           categories, recurring items, etc., and create the tab that
           corresponds to this meeting config.'''

        # Register the portal types that are specific to this meeting config.
        self.registerPortalTypes()

        # Create the subfolders
        for folderId, folderInfo in self.subFoldersInfo.iteritems():
            self.invokeFactory('Folder', folderId)
            folder = getattr(self, folderId)
            folder.setTitle(folderInfo[0])
            folder.setConstrainTypesMode(1)
            allowedType = folderInfo[1]
            if allowedType == 'itemType':
                allowedType = self.getItemTypeName()
            folder.setLocallyAllowedTypes([allowedType])
            folder.setImmediatelyAddableTypes([allowedType])
            folder.reindexObject()

        # Set a property allowing to know in which MeetingConfig we are
        self.manage_addProperty(MEETING_CONFIG, self.id, 'string')

        # Create the topics related to this meeting config
        self.createTopics()

        # Create the action (tab) that corresponds to this meeting config
        actions = self.portal_actions.listActions()
        action_ids = [action.id for action in actions]
        actionId = '%s_action' % self.getId()
        if actionId in action_ids:
            raise PloneMeetingError(ACTION_EXISTS % actionId)
        self.portal_actions.addAction(
            id = actionId, name = self.Title(),
            action = 'python:portal.portal_plonemeeting.getPloneMeetingFolder'\
                     '("%s").absolute_url()' % self.getId(),
            condition ='python:portal.portal_plonemeeting.' \
                       'showPloneMeetingTab("%s")' % self.getId(),
            permission = 'View',
            category = 'portal_tabs')

        # Sort the item tags if needed
        self.setAllItemTagsField()
        self.updateIsDefaultFields()
        self.adapted().onEdit(isCreated=True) # Call sub-product code if any

    def at_post_edit_script(self):
        '''Updates the workflows for items and meetings, and the
           item/meeting/decisionTopicStates.'''
        s = self.portal_workflow.setChainForPortalTypes
        # Update meeting item workflow
        s([self.getItemTypeName()], self.getItemWorkflow())
        # Update meeting workflow
        s([self.getMeetingTypeName()], self.getMeetingWorkflow())
        # Update portal types
        self.updatePortalTypes()
        # Update topics
        for topicGroup in ('MeetingItem', 'Meeting'):
            # Ok, now update each default topics using the states
            # defined in the meetingConfig.
            for topic in self.topicsUsingMeetingConfigStates[topicGroup]:
                # Delete the state-related criterion (normally it exists)
                try:
                    topicObj = getattr(self.topics, topic)
                except AttributeError:
                    # The default topic is not there?
                    continue
                try:
                    topicObj.deleteCriterion(
                        'crit__review_state_ATListCriterion')
                except AttributeError:
                    pass
                # Recreate it with the possibly updated list of states
                stateCriterion = topicObj.addCriterion(
                    field='review_state', criterion_type='ATListCriterion')
                # Which method must I use for getting states ?
                if topicGroup == 'MeetingItem':
                    getStatesMethod = self.getItemTopicStates
                else:
                    if topicObj.getId() == 'searchalldecisions':
                        getStatesMethod = self.getDecisionTopicStates
                    else:
                        getStatesMethod = self.getMeetingTopicStates
                stateCriterion.setValue(getStatesMethod())
        # Update item tags order if I must sort them
        self.setAllItemTagsField()
        self.updateIsDefaultFields()
        self.adapted().onEdit(isCreated=False) # Call sub-product code if any

    security.declarePublic('getItemTypeName')
    def getItemTypeName(self):
        '''Gets the name of the portal_type of the meeting item for this
           config.'''
        return 'MeetingItem%s' % self.getShortName()

    security.declarePublic('getMeetingTypeName')
    def getMeetingTypeName(self):
        '''Gets the name of the portal_type of the meeting for this
           config.'''
        return 'Meeting%s' % self.getShortName()

    security.declarePublic('getTopics')
    def getTopics(self, topicType):
        '''Gets topics related to type p_topicType.'''
        res = []
        for topic in self.topics.objectValues('ATTopic'):
            # Get the 2 properties : TOPIC_TYPE and TOPIC_SEARCH_SCRIPT
            topicTypeProp = topic.getProperty(TOPIC_TYPE)
            if topicTypeProp == topicType:
                topicSearchScriptProp = topic.getProperty(
                    TOPIC_SEARCH_SCRIPT, '')
                # We append the topic and the scriptId if it is not deactivated.
                # We filter on the review_state; else, the Manager will see
                # every topic in the portlets, which would be confusing.
                if self.portal_workflow.getInfoFor(topic, 'review_state') == \
                    'active':
                    tal_expr = topic.getProperty(TOPIC_TAL_EXPRESSION)
                    tal_res = True
                    if tal_expr:
                        ctx = createExprContext(
                            topic.getParentNode(),
                            self.portal_url.getPortalObject(), topic)
                        try:
                            tal_res = Expression(tal_expr)(ctx)
                        except Exception, e:
                            tal_res = False
                    if tal_res:
                        res.append((topic, topicSearchScriptProp))
        return res

    security.declarePublic('listWorkflows')
    def listWorkflows(self):
        '''Lists the workflows registered in portal_workflow.'''
        res = []
        for workflowName in self.portal_workflow.listWorkflows():
            res.append( (workflowName, workflowName) )
        return DisplayList(tuple(res))

    security.declarePublic('listStates')
    def listStates(self, objectType):
        '''Lists the possible states for the p_objectType ("Item" or "Meeting")
           used in this meeting config.'''
        res = []
        exec 'workflowName = self.get%sWorkflow()' % objectType
        workflow = getattr(self.portal_workflow, workflowName)
        for state in workflow.states.objectValues():
            res.append( (state.id, self.utranslate(state.id)) )
        return res

    security.declarePublic('listTransitions')
    def listTransitions(self, objectType):
        '''Lists the possible transitions for the p_objectType ("Item" or
           "Meeting") used in this meeting config.'''
        res = []
        exec 'workflowName = self.get%sWorkflow()' % objectType
        workflow = getattr(self.portal_workflow, workflowName)
        for t in workflow.transitions.objectValues():
            name = self.utranslate(t.id) + ' (' + t.id + ')'
            # Indeed several transitions can have the same translation
            # (ie "correct")
            res.append( (t.id, name) )
        return res

    security.declarePublic('listItemStates')
    def listItemStates(self):
        return DisplayList(tuple(self.listStates('Item')))

    security.declarePublic('listMeetingStates')
    def listMeetingStates(self):
        return DisplayList(tuple(self.listStates('Meeting')))

    security.declarePublic('listItemEvents')
    def listItemEvents(self):
        '''Lists the events related to items that will trigger a mail being
           sent.'''
        d = 'PloneMeeting'
        t = self.utranslate
        res = DisplayList((
            ("lateItem", t('event_late_item', domain=d)),
            ("annexAdded", t('event_add_annex', domain=d)),
            ("adviceAdded", t('event_add_advice', domain=d)),
            ("askDiscussItem", t('event_ask_discuss_item', domain=d)),
            ))
        return res

    security.declarePublic('listMeetingEvents')
    def listMeetingEvents(self):
        '''Lists the events related to meetings that will trigger a mail being
           sent.'''
        # Those events correspond to transitions of the workflow that governs
        # meetings.
        return DisplayList(tuple(self.listTransitions('Meeting')))

    security.declarePublic('getFileTypes')
    def getFileTypes(self, decisionRelated=False, typesIds=[]):
        '''Gets the item- or decision-related active meeting file types. If
           p_typesIds is not empty, it returns only file types whose ids are
           in this param.'''
        res = []
        for ft in self.meetingfiletypes.objectValues('MeetingFileType'):
            if (ft.getDecisionRelated() == decisionRelated) and \
               (self.portal_workflow.getInfoFor(ft, 'review_state')== 'active'):
                if not typesIds or (typesIds and (ft.id in typesIds)):
                    res.append(ft)
        return res

    security.declarePublic('getAgreementLevels')
    def getAgreementLevels(self, levelsIds=[]):
        '''Gets the item-related active meeting advice agreement levels. If
           p_typesIds is not empty, it returns only agreement levels whose ids
           are in this param.'''
        res = []
        for ft in self.agreementlevels.objectValues(
            'MeetingAdviceAgreementLevel'):
            if (self.portal_workflow.getInfoFor(ft, 'review_state')== 'active'):
                if not levelsIds or (levels and (ft.id in levelsIds)):
                    res.append(ft)
        return res

    security.declarePublic('getCategories')
    def getCategories(self, classifiers=False):
        '''Returns the active categories defined for this meeting config, or
           the active groups if groups are used as categories, or classifiers
           if p_classifiers is True.'''
        if classifiers:
            catFolder = self.classifiers
        elif self.getUseGroupsAsCategories():
            return self.portal_plonemeeting.getActiveGroups()
        else:
            catFolder = self.categories
        res = []
        for cat in catFolder.objectValues('MeetingCategory'):
            if self.portal_workflow.getInfoFor(cat, 'review_state') == \
               'active':
                res.append(cat)
        return res

    security.declarePublic('getAnnexesIconsWidth')
    def getAnnexesIconsWidth(self, decisionRelated=False):
        '''Returns the estimated size of the "annexes icons" block corresponding
           to this meeting config.'''
        res = 5
        for annex in self.getFileTypes(decisionRelated):
            res += annex.getTheIcon().width + 10
        return res

    security.declarePublic('getAgreementLevelsIconsWidth')
    def getAgreementLevelsIconsWidth(self):
        '''Returns the estimated size of the "agreementLevels icons" block
           corresponding to this meeting config.'''
        res = 5
        for agl in self.getAgreementLevels():
            res += agl.getTheIcon().width + 10
        return res

    security.declarePublic('listMeetingAppAvailableViews')
    def listMeetingAppAvailableViews(self):
        '''Returns a list of views available when a user clicks on a particular
           tab choosing a kind of meeting. This gives the admin a way to choose
           between the folder availables views (from portal_type) or a
           PloneMeeting-managed view based on PloneMeeting topics.

           We add a 'folder_' or a 'topic_' suffix to precise the kind of view.
        '''
        res = []
        topics = []
        try:
            # We try to get the topics folder defined in the meetingConfig
            topics_folder = getattr(self, 'topics')
            topics = topics_folder.objectValues('ATTopic')
        except AttributeError:
            logger.warn("No topics folder found.")

        # We add the folder views available in portal_type.Folder
        type_info = self.portal_types.getTypeInfo('Folder')
        available_views = type_info.getAvailableViewMethods(type_info)
        for view in available_views:
            # View "meetingfolder_redirect_view" is simply a view that checks
            # which view must be shown as PloneMeeting folder view and redirects
            # the user to the correct view. But it is a view in itself; the user
            # may not choose it. So we do not append it to the list of
            # available views on PloneMeeting folders.
            if view != 'meetingfolder_redirect_view':
                # Get the title by accessing the template
                # This title is managed by title_or_id and retrieved from the
                # .pt.metadata file
                method = getattr(self, view, None)
                if method is not None:
                    # A method might be a template, script or method
                    try:
                        title = method.aq_inner.aq_explicit.title_or_id()
                    except AttributeError:
                        title = view
                res.append(('folder_' + view,
                        self.utranslate(title, domain="plone")))
        # We add the topic based views
        for topic in topics:
            res.append( ('topic_' + topic.getId(),
                        self.utranslate(topic.Title())) )
        return DisplayList(tuple(res))

    security.declarePublic('listRoles')
    def listRoles(self):
        res = []
        for role in self.acl_users.portal_role_manager.listRoleIds():
            res.append( (role, role) )
        return DisplayList(tuple(res))

    security.declarePublic('listOptionalAdvisers')
    def listOptionalAdvisers(self):
        '''Returns a list of Plone groups members of MeetingGroups advisers.'''
        return DisplayList(tuple([(pg.getId(), pg.getProperty('title')) \
            for pg in self.getMeetingGroups(suffixes=['advisers', ])]))

    security.declarePublic('getMeetingGroups')
    def getMeetingGroups(self, suffixes=[]):
        '''Returns the list of Plone groups that are related to a MeetingGroup.
           If p_suffixes is defined, we limit the search to Plone groups having
           those suffixes. (_creators, _advisers, ...).'''
        pmtool = getToolByName(self, 'portal_plonemeeting')
        meeting_groups = pmtool.getActiveGroups()
        res = []
        if not suffixes:
            # If we did not received any suffixes, we take every existing
            # suffixes from config.py.
            suffixes = MEETINGROLES.keys()
        for mg in meeting_groups:
            for groupSuffix in suffixes:
                groupId = mg.getPloneGroupId(groupSuffix)
                ploneGroup = self.portal_groups.getGroupById(groupId)
                if ploneGroup is not None:
                    res.append(ploneGroup)
        return res

    security.declarePublic('getAvailablePodTemplates')
    def getAvailablePodTemplates(self, obj):
        '''Returns the list of POD templates that the currently logged in user
           may use for generating documents related to item or meeting p_obj.'''
        res = []
        podTemplateFolder = getattr(self, TOOL_FOLDER_POD_TEMPLATES)
        for podTemplate in podTemplateFolder.objectValues():
            if podTemplate.isApplicable(obj) and \
                self.portal_workflow.getInfoFor(
                    podTemplate, 'review_state') == 'active':
                res.append(podTemplate)
        return res

    security.declarePublic('listSortingMethods')
    def listSortingMethods(self):
        '''Return a list of available sorting methods when adding a item
           to a meeting'''
        res = []
        for sm in itemSortMethods:
            res.append( (sm, self.utranslate(sm, domain='PloneMeeting')) )
        return DisplayList(tuple(res))

    security.declarePublic('listSelectableCopyGroups')
    def listSelectableCopyGroups(self):
        '''Returns a list of groups that can be selected on an item as copy for
           the item.'''
        res = []
        # Get every Plone group related to a MeetingGroup
        meetingPloneGroups = self.getMeetingGroups()
        for group in meetingPloneGroups:
            res.append((group.id, group.getProperty('title')))

        return DisplayList(tuple(res))

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'MeetingConfig': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        '''Checks if the current meetingConfig can be deleted :
          - no Meeting and MeetingItem linked to this config can exist
          - the meetingConfig folder of the Members must be empty.'''
        # If we are trying to remove the Plone Site, bypass this hook.
        if not item.meta_type == "Plone Site":
            # Checks that no Meeting and no MeetingItem remains.
            brains = self.portal_catalog(portal_type=self.getMeetingTypeName())
            if brains:
                # We found at least one Meeting.
                raise BeforeDeleteException, \
                        "can_not_delete_meetingconfig_meeting"
            brains = self.portal_catalog(portal_type=self.getItemTypeName())
            if brains:
                # We found at least one MeetingItem.
                raise BeforeDeleteException, \
                        "can_not_delete_meetingconfig_meetingitem"
            # Check that every meetingConfig folder of Members is empty.
            members = self.portal_membership.getMembersFolder()
            meetingFolderId = self.getId()
            for member in members.objectValues():
                # Get the right meetingConfigFolder
                if hasattr(member, ROOT_FOLDER):
                    root_folder = getattr(member, ROOT_FOLDER)
                    if hasattr(root_folder, meetingFolderId):
                        # We found the right folder, check if it is empty
                        configFolder = getattr(root_folder, meetingFolderId)
                        if configFolder.objectValues():
                            raise BeforeDeleteException, \
                                    "can_not_delete_meetingconfig_meetingfolder"
            # If everything is OK, we can remove every meetingFolder
            for member in members.objectValues():
                # Get the right meetingConfigFolder
                if hasattr(member, ROOT_FOLDER):
                    root_folder = getattr(member, ROOT_FOLDER)
                    if hasattr(root_folder, meetingFolderId):
                        # We found the right folder, remove it
                        root_folder.manage_delObjects(meetingFolderId)
            # And we remove the corresponding action from portal_actions
            actionId = '%s_action' % meetingFolderId
            tool = self.portal_actions
            actions = tool.listActions()
            actions = [x for x in actions if not x.id == actionId]
            tool._actions = tuple(actions)
            # Remove the portal types which are specific to this meetingConfig
            for pt in [self.getMeetingTypeName(), self.getItemTypeName()]:
                self.portal_types.manage_delObjects([pt])
        BaseFolder.manage_beforeDelete(self, item, container)

    security.declarePublic('getCustomFields')
    def getCustomFields(self, cols):
        return getCustomSchemaFields(schema, self.schema, cols)

    security.declarePublic('getTopicsForPortletToDo')
    def getTopicsForPortletToDo(self):
        ''' Returns a list of topics to display in portlet_todo '''
        # Use getTopics to filter available topics with the TAL expression
        # defined on it
        availableTopics = self.getTopics('Meeting') + \
                          self.getTopics('MeetingItem')
        # Now, filter again with topics selected in self.toDoListTopics
        res = []
        toDoListTopics = self.getToDoListTopics()
        for topicObj, topicScriptId in availableTopics:
          if topicObj in toDoListTopics:
              res.append((topicObj, topicScriptId))
        return res

    security.declarePublic('getActiveMeetingUsers')
    def getActiveMeetingUsers(self, usages=('assemblyMember',)):
        '''Returns the active MeetingUsers having at least one usage among
           p_usage.'''
        res = []
        mUsersFolder = getattr(self, TOOL_FOLDER_MEETING_USERS)
        wfTool = self.portal_workflow
        for mUser in mUsersFolder.objectValues():
            mUserState = wfTool.getInfoFor(mUser, 'review_state')
            if (mUserState == 'active'):
                for usage in mUser.getUsages():
                    if usage in usages:
                        res.append(mUser)
        return res

    security.declarePrivate('addCategory')
    def addCategory(self, catDescr, classifier=False):
        '''Creates a category or a classifier (depending on p_classifier) from
           a CategoryDescriptor.'''
        if classifier:
            folder = getattr(self, TOOL_FOLDER_CLASSIFIERS)
        else:
            folder = getattr(self, TOOL_FOLDER_CATEGORIES)
        folder.invokeFactory('MeetingCategory', catDescr.id,
            title=catDescr.title, description=catDescr.description)
        cat = getattr(folder, catDescr.id)
        if not catDescr.active:
            self.portal_workflow.doActionFor(cat, 'deactivate')
        return cat

    security.declarePrivate('addRecurringItem')
    def addRecurringItem(self, recItemDescr):
        '''Adds a recurring item from a RecurringItemDescriptor.'''
        folder = getattr(self, TOOL_FOLDER_RECURRING_ITEMS)
        folder.invokeFactory(self.getItemTypeName(), **recItemDescr.__dict__)
        item = getattr(folder, recItemDescr.id)
        item.at_post_create_script()
        return item

    security.declarePrivate('addFileType')
    def addFileType(self, ft, source):
        '''Adds a file type from a FileTypeDescriptor p_ft.'''
        folder = getattr(self, TOOL_FOLDER_FILE_TYPES)
        if isinstance(source, basestring):
            # The image must be retrieved on disk from a profile
            iconPath = '%s/images/%s' % (source, ft.iconFile)
            iconFile = file(iconPath, 'rb')
            iconContent = iconFile.read()
        else:
            # The image is already here
            iconContent = File('dummyId', ft.theIcon.name,
                ft.theIcon.content, content_type=ft.theIcon.mimeType)
            ft.predefinedFileTitle = ft.predefinedTitle
        folder.invokeFactory('MeetingFileType', ft.id, title=ft.title,
            theIcon=iconContent, predefinedTitle=ft.predefinedFileTitle,
            decisionRelated=ft.decisionRelated)
        if isinstance(source, basestring): iconFile.close()
        fileType = getattr(folder, ft.id)
        if not ft.active:
            self.portal_workflow.doActionFor(fileType, 'deactivate')
        return fileType

    security.declarePrivate('addAgreementLevel')
    def addAgreementLevel(self, maal, source):
        '''Adds an agreement level from an AgreementLevelDescriptor p_maal.'''
        folder = getattr(self, TOOL_FOLDER_AGREEMENT_LEVELS)
        if isinstance(source, basestring):
            iconPath = '%s/images/%s' % (source, maal.iconFile)
            iconFile = file(iconPath, 'rb')
            iconContent = iconFile.read()
        else:
            iconContent = File('dummyId', maal.theIcon.name,
                maal.theIcon.content, content_type=maal.theIcon.mimeType)
        folder.invokeFactory('MeetingAdviceAgreementLevel', maal.id,
            title=maal.title, theIcon=iconContent)
        if isinstance(source, basestring): iconFile.close()
        al = getattr(folder, maal.id)
        if not maal.active:
            self.portal_workflow.doActionFor(al, 'deactivate')
        return al

    security.declarePrivate('addPodTemplate')
    def addPodTemplate(self, podTemplateDescr, source):
        '''Adds a POD template from a PodTemplateDescritor instance.'''
        folder = getattr(self, TOOL_FOLDER_POD_TEMPLATES)
        if isinstance(source, basestring):
            fileName = podTemplateDescr.podTemplate
            filePath = '%s/templates/%s' % (source, fileName)
            podTemplateDescr.podTemplate = file(filePath)
        else:
            pt = podTemplateDescr.podTemplate
            podTemplateDescr.podTemplate = File('dummyId', pt.name,
                pt.content, content_type=pt.mimeType)
        folder.invokeFactory('PodTemplate', **podTemplateDescr.__dict__)
        if isinstance(source, basestring):
            podTemplateDescr.podTemplate.close()
            podTemplateDescr.podTemplate = fileName
        podTemplate = getattr(folder, podTemplateDescr.id)
        if not podTemplateDescr.active:
            self.portal_workflow.doActionFor(podTemplate, 'deactivate')
        return podTemplate

    security.declarePrivate('addMeetingUser')
    def addMeetingUser(self, mud, source):
        '''Adds a meeting user from a MeetingUserDescriptor instance p_mud).'''
        folder = getattr(self, TOOL_FOLDER_MEETING_USERS)
        userInfo = self.portal_membership.getMemberById(mud.ploneUserId)
        userTitle = mud.ploneUserId
        if userInfo:
            userTitle = userInfo.getProperty('fullname')
        if not userTitle: userTitle = mud.ploneUserId
        folder.invokeFactory('MeetingUser', mud.id,
            ploneUserId=mud.ploneUserId, title=userTitle, duty=mud.duty,
            usages=mud.usages, signatureIsDefault=mud.signatureIsDefault)
        meetingUser = getattr(folder, mud.id)
        if mud.signatureImage:
            if isinstance(source, basestring):
                imageName = mud.signatureImage
                signaturePath = '%s/images/%s'% (source, imageName)
                signatureImageFile = file(signaturePath, 'rb')
            else:
                si = mud.signatureImage
                signatureImageFile = File('dummyId', si.name, si.content,
                    content_type=si.mimeType)
            meetingUser.setSignatureImage(signatureImageFile)
            signatureImageFile.close()
        if not mud.active:
            self.portal_workflow.doActionFor(meetingUser, 'deactivate')
        return meetingUser

    security.declarePublic('getMeetingUserFromPloneUser')
    def getMeetingUserFromPloneUser(self, ploneUserId):
        '''Returns the Meeting user that corresponds to p_ploneUserId.'''
        mUserFolder = getattr(self, TOOL_FOLDER_MEETING_USERS)
        for meetingUser in mUserFolder.objectValues():
            if (meetingUser.getPloneUserId() == ploneUserId):
                return meetingUser
        return None

    security.declarePublic('getStatesToSearch')
    def getStatesToSearch(self, role, perm):
        """
          Return a list of states where the role has the permission for a workflow
        """
        workflow = getToolByName(self, 'portal_workflow').getWorkflowById(self.getItemWorkflow())
        res = []
        for state in workflow.states.values():
            permissions = state.getManagedPermissions()
            if permissions:
                for permission in permissions:
                    #if we found the right permission, check the roles
                    if permission == perm:
                        if role in state.getPermissionInfo(perm)['roles']:
                            res.append(state.id)
                            break
        return res



registerType(MeetingConfig, PROJECTNAME)
# end of class MeetingConfig

##code-section module-footer #fill in your manual code here
##/code-section module-footer



