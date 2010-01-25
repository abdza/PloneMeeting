# -*- coding: utf-8 -*-
#
# File: MeetingItem.py
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
from persistent.list import PersistentList
from persistent.mapping import PersistentMapping
from AccessControl import getSecurityManager, Unauthorized
from DateTime import DateTime
from zope.interface import implements
from Globals import InitializeClass
from OFS.ObjectManager import BeforeDeleteException
from Products.ATReferenceBrowserWidget.ATReferenceBrowserWidget import \
     ReferenceBrowserWidget
from Products.CMFCore.PortalFolder import PortalFolderBase as PortalFolder
from Products.CMFCore.Expression import Expression, createExprContext
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.permissions import \
     ModifyPortalContent, ReviewPortalContent, DeleteObjects, View
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.Meeting import Meeting
from Products.PloneMeeting.MeetingFile import MeetingFile
from Products.PloneMeeting.interfaces import IMeetingItemWorkflowConditions, \
                                             IMeetingItemWorkflowActions
from Products.PloneMeeting.utils import \
     getWorkflowAdapter, getCustomAdapter, kupuFieldIsEmpty, \
     getCurrentMeetingObject, checkPermission, \
     sendMail, sendMailIfRelevant, HubSessionsMarshaller
import logging
logger = logging.getLogger('PloneMeeting')

# PloneMeetingError-related constants -----------------------------------------
NUMBERING_ERROR = 'No meeting is defined for this item. So it is not ' \
    'possible to get an item number which is relative to the meeting config.'
ITEM_REF_ERROR = 'There was an error in the TAL expression for defining the ' \
    'format of an item reference. Please check this in your meeting config. ' \
    'Original exception: %s'
GROUP_MANDATORY_CONDITION_ERROR = 'There was an error in the TAL expression ' \
    'defining if the group must be considered as a mandatory adviser. ' \
    'Please check this in your meeting config. ' \
    'Original exception: %s'

WRONG_TRANSITION = 'Transition "%s" is inappropriate for adding recurring ' \
    'items.'
REC_ITEM_ERROR = 'There was an error while trying to generate recurring ' \
    'item with id "%s". %s'
BEFOREDELETE_ERROR = 'A BeforeDeleteException was raised by "%s" while ' \
    'trying to delete an item with id "%s"'

# Marshaller ------------------------------------------------------------------
class MeetingItemMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a meeting item into a XML file that one may get
       through WebDAV.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all_with_metadata'
    fieldsToExclude = ['proposingGroup', 'associatedGroups', 'category',
                       'classifier', 'allowDiscussion']
    rootElementName = 'meetingItem'

    def getGroupTitle(self, item, groupId):
        tool = item.portal_plonemeeting
        group = getattr(tool, groupId, None)
        if group:
            res = group.Title()
        else:
            res = groupId
        return res

    def marshallSpecificElements(self, item, res):
        HubSessionsMarshaller.marshallSpecificElements(self, item, res)
        self.dumpField(res, 'reference', item.adapted().getItemReference())
        # Dump groups. We add group title among tag attributes (so we do not
        # use standard field dump). This way, non-PloneMeeting external
        # applications do not need to retrieve separately MeetingGroup objects.
        groupTitle = self.getGroupTitle(item, item.getProposingGroup())
        res.write('<proposingGroup title="')
        res.write(groupTitle); res.write('">')
        res.write(item.getProposingGroup())
        res.write('</proposingGroup>')
        groupIds = item.getAssociatedGroups()
        res.write('<associatedGroups type="list" count="%d">' % len(groupIds))
        for groupId in groupIds:
            groupTitle = self.getGroupTitle(item, groupId)
            res.write('<associatedGroup title="')
            res.write(groupTitle); res.write('">')
            res.write(groupId)
            res.write('</associatedGroup>')
        res.write('</associatedGroups>')
        # For the same reason, dump the categories in a specific way
        cat = item.getCategory(True)
        catTitle = ''
        catId = ''
        if cat:
            catTitle = cat.Title()
            catId = cat.getId()
        res.write('<category title="')
        res.write(catTitle); res.write('">')
        res.write(catId)
        res.write('</category>')
        # Classifier is a reference field. Dump its id only.
        res.write('<classifier>')
        classifier = item.getClassifier()
        if classifier: res.write(classifier.id)
        res.write('</classifier>')
        # Dump advices
        advices = item.getAdvices()
        res.write('<advices type="list" count="%d">' % len(advices))
        for advice in advices:
            self.dumpField(res, 'url', advice.absolute_url())
        res.write('</advices>')
        res.write('<votes type="list">')
        for voter, voteValue in item.votes.iteritems():
            res.write('<vote type="object">')
            self.dumpField(res, 'voter', voter)
            self.dumpField(res, 'voteValue', voteValue)
            res.write('</vote>')
        res.write('</votes>')
        self.dumpField(res, 'pm_modification_date', item.pm_modification_date)
InitializeClass(MeetingItemMarshaller)

# Adapters ---------------------------------------------------------------------
class MeetingItemWorkflowConditions:
    '''Adapts a MeetingItem to interface IMeetingItemWorkflowConditions.'''
    implements(IMeetingItemWorkflowConditions)
    security = ClassSecurityInfo()

    # In those states, the meeting is not closed.
    meetingNotClosedStates = ('published', 'frozen', 'decided')

    def __init__(self, item):
        self.context = item

    def _publishedObjectIsMeeting(self):
        '''Is the object currently published in Plone a Meeting ?'''
        obj = getCurrentMeetingObject(self.context)
        return isinstance(obj, Meeting)

    def _getDateOfAction(self, obj, action):
        '''Returns the date (Zope DateTime object) of the last p_action that
           was performed on object p_obj.'''
        # Get the last validation date of the item
        res = None
        objectHistory = obj.workflow_history
        if objectHistory:
            objectHistory = objectHistory.values()[0] # We suppose here that the
            # object is governed by only one workflow.
            for step in objectHistory:
                if (step['action'] == action):
                    res = step['time']
        return res

    # Implementation of methods from the interface I realize -------------------
    security.declarePublic('mayPropose')
    def mayPropose(self):
        res = False
        member = self.context.portal_membership.getAuthenticatedMember()
        if checkPermission(ReviewPortalContent, self.context) and \
           (not self.context.isDefinedInTool()):
            res = True
        return res

    security.declarePublic('mayValidate')
    def mayValidate(self):
        res = False
        # We check if the current user is MeetingManager to allow transitions
        # for recurring items added in a meeting
        user = self.context.portal_membership.getAuthenticatedMember()
        if (checkPermission(ReviewPortalContent, self.context) or \
            user.has_role('MeetingManager')) and \
           (not self.context.isDefinedInTool()):
            res = True
        return res

    security.declarePublic('mayPresent')
    def mayPresent(self):
        # We may present the item if Plone currently publishes a meeting.
        # Indeed, an item may only be presented within a meeting.
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           self._publishedObjectIsMeeting():
            res = True
        return res

    security.declarePublic('mayDecide')
    def mayDecide(self):
        res = False
        meeting = self.context.getMeeting()
        if checkPermission(ReviewPortalContent, self.context) and meeting and \
           (meeting.queryState() in self.meetingNotClosedStates) and \
           meeting.getDate().isPast() and \
           (not self.context.decisionFieldIsEmpty()):
            res = True
        return res

    security.declarePublic('mayDelay')
    def mayDelay(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayConfirm')
    def mayConfirm(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           self.context.getMeeting().queryState() in ('decided', 'closed'):
            res = True
        return res

    security.declarePublic('mayCorrect')
    def mayCorrect(self):
        res = False
        # We check if the current user is MeetingManager to allow transitions
        # for recurring items added in a meeting
        user = self.context.portal_membership.getAuthenticatedMember()
        if checkPermission(ReviewPortalContent, self.context) or \
           user.has_role('MeetingManager'):
            currentState = self.context.queryState()
            if currentState in ('proposed', 'validated'):
                res = True
            else:
                if self.context.hasMeeting():
                    pubObjIsMeeting = self._publishedObjectIsMeeting()
                    meetingState = self.context.getMeeting().queryState()
                    isLateItem = self.context.isLate()
                    if (currentState == 'presented') and pubObjIsMeeting:
                        if (meetingState == 'created') or \
                           (isLateItem and (meetingState in \
                              self.meetingNotClosedStates)):
                            res = True
                    elif (currentState == 'itempublished') and pubObjIsMeeting:
                        if isLateItem:
                            res = True
                        elif meetingState == 'created':
                            res = True # In fact the user will never be able to
                            # correct the item in this state. The meeting
                            # workflow will do it automatically as soon as the
                            # meeting goes from 'published' to 'created'.
                    elif (currentState == 'itemfrozen') and pubObjIsMeeting:
                        if isLateItem:
                            res = True
                        if meetingState == 'published':
                            res = True # The user will never be able to correct
                            # the item in this state; it will be triggered
                            # automatically as soon as the meeting goes from
                            # 'frozen' to 'published'.
                    elif currentState in ('accepted', 'refused'):
                        if meetingState in self.meetingNotClosedStates:
                            res = True
                    elif currentState == 'confirmed':
                        if meetingState != 'closed':
                            res = True
                    elif currentState == 'itemarchived':
                        if meetingState == 'closed':
                            res = True # The user will never be able to correct
                            # the item in this state; it will be triggered
                            # automatically as soon as the meeting goes from
                            # 'archived' to 'closed'.
                    elif currentState == 'delayed':
                        res = True
        return res

    security.declarePublic('mayDelete')
    def mayDelete(self):
        res = True
        if self.context.getRawAnnexesDecision():
            res = False
        return res

    security.declarePublic('mayDeleteAnnex')
    def mayDeleteAnnex(self, annex):
        return True

    security.declarePublic('meetingIsPublished')
    def meetingIsPublished(self):
        res = False
        if self.context.hasMeeting() and \
           (self.context.getMeeting().queryState() in \
            self.meetingNotClosedStates):
            res = True
        return res

    security.declarePublic('mayPublish')
    def mayPublish(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           self.meetingIsPublished():
            res = True
        return res

    security.declarePublic('mayFreeze')
    def mayFreeze(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            if self.context.hasMeeting() and \
               (self.context.getMeeting().queryState() in \
                ('frozen', 'decided')):
                res = True
        return res

    security.declarePublic('mayArchive')
    def mayArchive(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            meeting = self.context.getMeeting()
            if self.context.hasMeeting() and \
               (self.context.getMeeting().queryState() == 'archived'):
                res = True
        return res

    security.declarePublic('isLateFor')
    def isLateFor(self, meeting):
        res = False
        if meeting and \
           (meeting.queryState() in self.meetingNotClosedStates) and \
           (meeting.UID() == self.context.getPreferredMeeting()):
            itemValidationDate = self._getDateOfAction(self.context, 'validate')
            meetingPublicationDate = self._getDateOfAction(meeting, 'publish')
            if itemValidationDate and meetingPublicationDate:
                if itemValidationDate > meetingPublicationDate:
                    res = True
        return res

InitializeClass(MeetingItemWorkflowConditions)

class MeetingItemWorkflowActions:
    '''Adapts a meeting item to interface IMeetingItemWorkflowActions.'''
    implements(IMeetingItemWorkflowActions)
    security = ClassSecurityInfo()

    # Possible states of "frozen" meetings
    meetingAlreadyFrozenStates = ('frozen', 'decided')

    def __init__(self, item):
        self.context = item

    security.declarePrivate('doPropose')
    def doPropose(self, stateChange): pass

    security.declarePrivate('doValidate')
    def doValidate(self, stateChange):
        # If it is a "late" item, we must potentially send a mail to warn
        # MeetingManagers.
        preferredMeeting = self.context.getPreferredMeeting()
        if preferredMeeting != 'whatever':
            # Get the meeting from its UID
            objs = self.context.uid_catalog.searchResults(UID=preferredMeeting)
            if objs:
                meeting = objs[0].getObject()
                if self.context.wfConditions().isLateFor(meeting):
                    sendMailIfRelevant(self.context, 'lateItem',
                                       'MeetingManager', isRole=True)

    security.declarePrivate('doPresent')
    def doPresent(self, stateChange):
        meeting = getCurrentMeetingObject(self.context)
        meeting.insertItem(self.context)
        # If the meeting is already frozen and thi item is a "late" item,
        # I must set automatically the item to "itempublished".
        meetingState = meeting.queryState()
        wTool = self.context.portal_workflow
        if meetingState in self.meetingAlreadyFrozenStates:
            wTool.doActionFor(self.context, 'itempublish')
            wTool.doActionFor(self.context, 'itemfreeze')

    security.declarePrivate('doItemPublish')
    def doItemPublish(self, stateChange): pass

    security.declarePrivate('doItemFreeze')
    def doItemFreeze(self, stateChange):
        """
         When we freeze the item, we close every contained advices...
        """
        for advice in self.context.getAdvices():
            #we close every MeetingAdvice
            wTool = self.context.portal_workflow
            if wTool.getInfoFor(advice, 'review_state') == 'advicecreated':
                wTool.doActionFor(advice, 'advicePublish')
                wTool.doActionFor(advice, 'adviceClose')
            elif wTool.getInfoFor(advice, 'review_state') == 'advicepublished':
                wTool.doActionFor(advice, 'adviceClose')

    security.declarePrivate('doAccept')
    def doAccept(self, stateChange): pass

    security.declarePrivate('doRefuse')
    def doRefuse(self, stateChange): pass

    security.declarePrivate('doDelay')
    def doDelay(self, stateChange): pass

    security.declarePrivate('doCorrect')
    def doCorrect(self, stateChange):
        # If we go back to "validated" we must remove the item from a meeting
        if stateChange.new_state.id == "validated":
            meeting = self.context.getMeeting()
            meeting.removeItem(self.context)
        # If we go back to "itempublished" we must set every contained advices
        # back to the "advicepublished" state
        if stateChange.new_state.id == "itempublished":
            for advice in self.context.getAdvices():
                #we set every MeetingAdvice to "advicepublished"
                wTool = self.context.portal_workflow
                if wTool.getInfoFor(advice, 'review_state') == 'adviceclosed':
                    wTool.doActionFor(advice, 'adviceBackToPublished')

    security.declarePrivate('doConfirm')
    def doConfirm(self, stateChange): pass

    security.declarePrivate('doItemArchive')
    def doItemArchive(self, stateChange): pass

    security.declarePrivate('doUpdateAnnexesSecurity')
    def doUpdateAnnexesSecurity(self, stateChange):
        for annexGroup in (self.context.getAnnexes(),
                           self.context.getAnnexesDecision()):
            for annex in annexGroup:
                annex.updateAnnexSecurity()

InitializeClass(MeetingItemWorkflowActions)
##/code-section module-header

schema = Schema((

    TextField(
        name='description',
        widget=RichWidget(
            label_msgid="meeting_item_description",
            label="Description",
            i18n_domain='PloneMeeting',
        ),
        default_content_type="text/html",
        searchable=True,
        allowable_content_types=('text/html',),
        default_output_type="text/html",
        accessor="Description",
    ),
    StringField(
        name='category',
        widget=SelectionWidget(
            condition="python: here.showCategory()",
            description="Category",
            description_msgid="item_category_descr",
            label='Category',
            label_msgid='PloneMeeting_label_category',
            i18n_domain='PloneMeeting',
        ),
        vocabulary='listCategories',
    ),
    ReferenceField(
        name='classifier',
        widget=ReferenceBrowserWidget(
            description="Classifier",
            description_msgid="item_classifier_descr",
            condition="python: here.attributeIsUsed('classifier')",
            allow_search=True,
            allow_browse=True,
            startup_directory="getCategoriesFolder",
            force_close_on_insert=True,
            label='Classifier',
            label_msgid='PloneMeeting_label_classifier',
            i18n_domain='PloneMeeting',
        ),
        allowed_types=('MeetingCategory',),
        optional=True,
        multiValued=False,
        relationship="ItemClassification",
    ),
    StringField(
        name='proposingGroup',
        widget=SelectionWidget(
            format="select",
            label='Proposinggroup',
            label_msgid='PloneMeeting_label_proposingGroup',
            i18n_domain='PloneMeeting',
        ),
        vocabulary='listProposingGroup',
    ),
    LinesField(
        name='associatedGroups',
        widget=MultiSelectionWidget(
            condition="python: here.attributeIsUsed('associatedGroups')",
            format="checkbox",
            label='Associatedgroups',
            label_msgid='PloneMeeting_label_associatedGroups',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        multiValued=1,
        vocabulary='listAssociatedGroups',
    ),
    StringField(
        name='preferredMeeting',
        default='whatever',
        widget=SelectionWidget(
            condition="python: not here.isDefinedInTool()",
            label='Preferredmeeting',
            label_msgid='PloneMeeting_label_preferredMeeting',
            i18n_domain='PloneMeeting',
        ),
        vocabulary='listMeetingsAcceptingItems',
    ),
    LinesField(
        name='itemTags',
        widget=MultiSelectionWidget(
            condition="python: here.attributeIsUsed('itemTags')",
            label='Itemtags',
            label_msgid='PloneMeeting_label_itemTags',
            i18n_domain='PloneMeeting',
        ),
        multiValued=1,
        vocabulary='listItemTags',
        searchable=True,
        enforceVocabulary=True,
        optional=True,
    ),
    StringField(
        name='itemKeywords',
        widget=StringField._properties['widget'](
            size= 100,
            condition="python: here.attributeIsUsed('itemKeywords')",
            label='Itemkeywords',
            label_msgid='PloneMeeting_label_itemKeywords',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        searchable=True,
    ),
    TextField(
        name='decision',
        widget=RichWidget(
            label='Decision',
            label_msgid='PloneMeeting_label_decision',
            i18n_domain='PloneMeeting',
        ),
        default_content_type="text/html",
        read_permission="PloneMeeting: Read decision",
        searchable=True,
        allowable_content_types=('text/html',),
        default_output_type="text/html",
        write_permission="PloneMeeting: Write decision",
    ),
    LinesField(
        name='mandatoryAdvisers',
        widget=MultiSelectionWidget(
            description="MandatoryAdvisersItem",
            description_msgid="mandatory_advisers_item_descr",
            condition='python: here.displayMandatoryAdvisersField()',
            label='Mandatoryadvisers',
            label_msgid='PloneMeeting_label_mandatoryAdvisers',
            i18n_domain='PloneMeeting',
        ),
        multiValued=1,
        vocabulary='listMandatoryAdvisers',
        enforceVocabulary= True,
        write_permission="PloneMeeting: Write mandatory advisers",
        read_permission="PloneMeeting: Read mandatory advisers",
    ),
    LinesField(
        name='optionalAdvisers',
        widget=MultiSelectionWidget(
            description="OptionalAdvisersItem",
            description_msgid="optional_advisers_item_descr",
            condition='python:here.isAdvicesEnabled() and len(here.listOptionalAdvisers())',
            label='Optionaladvisers',
            label_msgid='PloneMeeting_label_optionalAdvisers',
            i18n_domain='PloneMeeting',
        ),
        multiValued=1,
        vocabulary='listOptionalAdvisers',
        enforceVocabulary=True,
        write_permission="PloneMeeting: Write optional advisers",
        read_permission="PloneMeeting: Read optional advisers",
    ),
    TextField(
        name='observations',
        widget=RichWidget(
            label_msgid="PloneMeeting_itemObservations",
            condition="python: here.attributeIsUsed('observations')",
            label='Observations',
            i18n_domain='PloneMeeting',
        ),
        default_content_type="text/html",
        read_permission="PloneMeeting: Read item observations",
        searchable=True,
        allowable_content_types=('text/html',),
        default_output_type="text/html",
        optional=True,
        write_permission="PloneMeeting: Write item observations",
    ),
    ReferenceField(
        name='annexes',
        widget=ReferenceBrowserWidget(
            visible=False,
            label='Annexes',
            label_msgid='PloneMeeting_label_annexes',
            i18n_domain='PloneMeeting',
        ),
        multiValued=True,
        relationship="ItemAnnexes",
        write_permission="PloneMeeting: Add annex",
    ),
    ReferenceField(
        name='annexesDecision',
        widget=ReferenceBrowserWidget(
            visible=False,
            label='Annexesdecision',
            label_msgid='PloneMeeting_label_annexesDecision',
            i18n_domain='PloneMeeting',
        ),
        write_permission="PloneMeeting: Write decision annex",
        read_permission="PloneMeeting: Read decision annex",
        relationship="DecisionAnnexes",
        multiValued=True,
    ),
    IntegerField(
        name='itemNumber',
        widget=IntegerField._properties['widget'](
            visible="False",
            label='Itemnumber',
            label_msgid='PloneMeeting_label_itemNumber',
            i18n_domain='PloneMeeting',
        ),
    ),
    BooleanField(
        name='toDiscuss',
        widget=BooleanField._properties['widget'](
            visible="False",
            label='Todiscuss',
            label_msgid='PloneMeeting_label_toDiscuss',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        default_method="getDefaultToDiscuss",
    ),
    StringField(
        name='meetingTransitionInsertingMe',
        widget=SelectionWidget(
            condition='python: here.isDefinedInTool()',
            label='Meetingtransitioninsertingme',
            label_msgid='PloneMeeting_label_meetingTransitionInsertingMe',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        vocabulary='listMeetingTransitions',
    ),
    TextField(
        name='itemSignatures',
        widget=TextAreaWidget(
            label='Itemsignatures',
            label_msgid='PloneMeeting_label_itemSignatures',
            i18n_domain='PloneMeeting',
        ),
        schemata="metadata",
    ),
    LinesField(
        name='copyGroups',
        widget=MultiSelectionWidget(
            size=10,
            condition='python:here.isCopiesEnabled()',
            description="CopyGroupsItems",
            description_msgid="copy_groups_item_descr",
            label='Copygroups',
            label_msgid='PloneMeeting_label_copyGroups',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        multiValued=1,
        vocabulary='listCopyGroups',
    ),
    BooleanField(
        name='votesAreSecret',
        default=False,
        widget=BooleanField._properties['widget'](
            condition="python: here.isVotesEnabled() and (member.has_role('MeetingManager') or member.has_role('Manager'))",
            label='Votesaresecret',
            label_msgid='PloneMeeting_label_votesAreSecret',
            i18n_domain='PloneMeeting',
        ),
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingItem_schema = OrderedBaseFolderSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
# Integrate potential extensions from PloneMeeting sub-products
from Products.PloneMeeting.model.extender import ModelExtender
from BTrees.OOBTree import OOBTree
MeetingItem_schema = ModelExtender(MeetingItem_schema, 'item').run()
# Register the marshaller for DAV/XML export.
MeetingItem_schema.registerLayer('marshall', MeetingItemMarshaller())
##/code-section after-schema

class MeetingItem(OrderedBaseFolder, BrowserDefaultMixin):
    """
    """
    security = ClassSecurityInfo()

    implements(interfaces.IMeetingItem)

    meta_type = 'MeetingItem'
    _at_rename_after_creation = True

    schema = MeetingItem_schema

    ##code-section class-header #fill in your manual code here
    meetingTransitionsAcceptingRecurringItems = ('_init_', 'publish', 'freeze',
                                                 'decide')
    itemTransitionsForPresentingIt =  ('propose', 'validate', 'present')
    __dav_marshall__ = True # MeetingItem is folderish so normally it can't be
    # marshalled through WebDAV.
    # When 'present' action is triggered on an item, depending on the meeting
    # state, other transitions may be triggered automatically (itempublish,
    # itemfreeze)
    ##/code-section class-header

    # Methods

    # Manually created methods

    def __init__(self, *args, **kwargs):
        '''self.annexIndex stores info about annexes, such that it is not needed
           to access real annexes objects for doing things like displaying the
           "annexes icons" macro, for example.'''
        OrderedBaseFolder.__init__(self, *args, **kwargs)
        self.annexIndex = PersistentList()
        self.adviceIndex = OOBTree()

    def validate_category(self, value):
        '''Checks that, if we do not use groups as categories, a category is
           specified.'''
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        if (not meetingConfig.getUseGroupsAsCategories()) and \
           (value == '_none_'):
            return self.utranslate('category_required', domain='PloneMeeting')
        return None

    def validate_classifier(self, value):
        '''If classifiers are use, they are mandatory.'''
        if self.attributeIsUsed('classifier') and not value:
            return self.utranslate('category_required', domain='PloneMeeting')
        return None

    def updateAnnexIndex(self, annex=None, removeAnnex=False):
        '''This method updates self.annexIndex (see doc in
           MeetingItem.__init__). If p_annex is None, this method recomputes the
           whole annexIndex. If p_annex is not None:
           - if p_remove is False, info about the newly created p_annex is added
             to self.annexIndex;
           - if p_remove is True, info about the deleted p_annex is removed from
             self.annexIndex.'''
        if annex:
            if removeAnnex:
                # Remove p_annex-related info
                removeUid = annex.UID()
                for annexInfo in self.annexIndex:
                    if removeUid == annexInfo['uid']:
                        self.annexIndex.remove(annexInfo)
                        break
            else:
                # Add p_annex-related info
                self.annexIndex.append(annex.getAnnexInfo())
        else:
            if not hasattr(self, 'annexIndex'):
                self.annexIndex = PersistentList() # This is useful for
                # upgrading old MeetingItem objects that do not have annexIndex
                # yet (this was the case for PloneMeeting < 1.3)
            else:
                del self.annexIndex[:]
            sortableList = []
            for annex in self.getAnnexes():
                sortableList.append(annex.getAnnexInfo())
            for annex in self.getAnnexesDecision():
                sortableList.append(annex.getAnnexInfo())
            sortableList.sort(key = lambda x: x['modification_date'])
            for a in sortableList:
                self.annexIndex.append(a)

    def updateAdviceIndex(self, advice=None, removeAdvice=False):
        '''This method updates self.adviceIndex (see doc in
           MeetingItem.__init__). If p_advice is None, this method recomputes
           the whole adviceIndex. If p_advice is not None:
           - if p_remove is False, info about the newly created p_advice is
             added to self.adviceIndex;
           - if p_remove is True, info about the deleted p_advice is removed
             from self.adviceIndex.'''
        if not hasattr(self, 'adviceIndex'):
            self.adviceIndex = OOBTree() # This is useful for
            # upgrading old MeetingItem objects that do not have adviceIndex
            # yet (this was the case for PloneMeeting < 1.5)
        if advice:
            if removeAdvice:
                # Remove p_advice-related info
                del self.adviceIndex[advice.UID()]
            else:
                # Add p_advice-related info
                self.adviceIndex[advice.UID()] = advice.getAdviceInfo()
        else:
            self.adviceIndex.clear()
            # Add entries for existing advices
            for advice in self.getAdvices():
                self.adviceIndex[advice.UID()] = advice.getAdviceInfo()
            # Add special entry which references all advisers of the item
            # (in order to determine "missing advices" --> cf.
            # 'getAdvicesByAgreementLevel' and 'getAdvicesByAdviser' methods)
            self.adviceIndex[LIST_ADVISERS_KEY] = self.adapted().getAdvisers()
        #update the adviceIndex index...
        self.reindexObject()

    security.declarePublic('isDefinedInTool')
    def isDefinedInTool(self):
        '''Is this item being defined in the tool (portal_plonemeeting) ?
           Items defined like that are used as base for creating recurring
           items.'''
        return ('portal_plonemeeting' in self.absolute_url())

    security.declarePublic('isDefinedInToolOrTemp')
    def isDefinedInToolOrTemp(self):
        '''Returns True if this item is defined in tool or is being created
           in portal_factory. This method is used as a condition for showing
           or not some item-related actions.'''
        res = self.portal_factory.isTemporary(self) or self.isDefinedInTool()
        return res

    security.declarePublic('getItemNumber')
    def getItemNumber(self, relativeTo='itemsList'):
        '''This accessor for 'itemNumber' field is overridden in order to allow
           to get the item number in various flavours:
           - the item number relative to the items list into which it is
             included ("normal" or "late" items list): p_relativeTo="itemsList";
           - the item number relative to the whole meeting (no matter the item
             being "normal" or "late"): p_relativeTo="meeting";
           - the item number relative to the whole meeting config:
             p_relativeTo="meetingConfig"'''
        res = self.getField('itemNumber').get(self)
        if relativeTo == 'itemsList':
            pass
        elif relativeTo == 'meeting':
            if self.isLate():
                res += len(self.getMeeting().getRawItems())
        elif relativeTo == 'meetingConfig':
            if self.hasMeeting():
                meeting = self.getMeeting()
                meetingFirstItemNumber = meeting.getFirstItemNumber()
                if meetingFirstItemNumber != -1:
                    res = meetingFirstItemNumber + \
                        self.getItemNumber(relativeTo='meeting') -1
                else:
                    # Start from the last item number in the meeting config.
                    meetingConfig = self.portal_plonemeeting.getMeetingConfig(
                        self)
                    res = meetingConfig.getLastItemNumber()
                    # ... take into account all the meetings scheduled before
                    # this one...
                    meetingBrains = self.adapted().getMeetingsAcceptingItems()
                    for brain in meetingBrains:
                        m = brain._unrestrictedGetObject()
                        if m.getDate() < meeting.getDate():
                            res += len(m.getRawItems()) + \
                                   len(m.getRawLateItems())
                    # ...then add the position of this item relative to its
                    # meeting
                    res += self.getItemNumber(relativeTo='meeting')
        else:
            raise PloneMeetingError(NUMBERING_ERROR)
        return res

    security.declarePublic('getDefaultToDiscuss')
    def getDefaultToDiscuss(self):
        '''What is the default value for the "toDiscuss" field ? Look in the
           meeting config.'''
        res = True
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        if meetingConfig:
            # When creating a meeting through invokeFactory (like recurring
            # items), getMeetingConfig does not work because the Archetypes
            # object is not properly initialized yet (portal_type is not set
            # correctly yet)
            res = meetingConfig.getToDiscussDefault()
        return res

    security.declarePublic('getMeetingsAcceptingItems')
    def getMeetingsAcceptingItems(self):
        '''Check docstring in interfaces.py '''
        item = self.getSelf()
        meetingPortalType = item.portal_plonemeeting.getMeetingConfig(
            item).getMeetingTypeName()
        res = item.portal_catalog.unrestrictedSearchResults(
            portal_type=meetingPortalType,
            review_state=('created', 'published', 'frozen', 'decided'),
            sort_on='getDate')
        # Published, frozen and decided meetings may still accept "late" items.
        return res

    security.declarePublic('listMeetingsAcceptingItems')
    def listMeetingsAcceptingItems(self):
        '''Returns the (Display)list of meetings returned by
           m_getMeetingsAcceptingItems.'''
        res = [('whatever', 'Any meeting')]
        for meetingBrain in self.adapted().getMeetingsAcceptingItems():
            meeting = self.unrestrictedTraverse(meetingBrain.getPath())
            res.append((meeting.UID(), meeting.Title()))
        return DisplayList(tuple(res))

    security.declarePublic('listMeetingTransitions')
    def listMeetingTransitions(self):
        '''Lists the possible transitions for meetings of the same meeting
           config as this item.'''
        # I add here the "initial transition", that is not stored as a real
        # transition.
        res = [ ('_init_', self.utranslate('_init_')) ]
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        meetingWorkflowName = meetingConfig.getMeetingWorkflow()
        meetingWorkflow = getattr(self.portal_workflow, meetingWorkflowName)
        for transition in meetingWorkflow.transitions.objectValues():
            name = self.utranslate(transition.id) + ' (' + transition.id + ')'
            res.append( (transition.id, name) )
        return DisplayList(tuple(res))

    security.declarePublic('listProposingGroup')
    def listProposingGroup(self):
        '''Return the MeetingGroup(s) that may propose this item. If no group is
           set yet, this method returns the MeetingGroup(s) the user belongs
           to. If a group is already set, it is returned.

           If this item is being created or edited in portal_plonemeeting (as a
           recurring item), the list of active groups is returned.'''
        if not self.isDefinedInTool():
            groupId = self.getField('proposingGroup').get(self)
            tool = self.portal_plonemeeting
            userMeetingGroups = tool.getUserMeetingGroups(suffix="creators")
            res = []
            for group in userMeetingGroups:
                res.append( (group.id, group.Title()) )
            if groupId:
                # Try to get the corresponding meeting group
                group = getattr(tool, groupId, None)
                if group:
                    if group not in userMeetingGroups:
                        res.append( (groupId, group.Title()) )
                else:
                    res.append( (groupId, groupId) )
        else:
            res = []
            for group in self.portal_plonemeeting.getActiveGroups():
                res.append( (group.id, group.Title()) )
        return DisplayList(tuple(res))

    security.declarePublic('listAssociatedGroups')
    def listAssociatedGroups(self):
        '''Lists the groups that are associated to the proposing group(s) to
           propose this item.  Return groups that have at least one creator...'''
        res = []
        tool = self.portal_plonemeeting
        for group in tool.getActiveGroups(notEmptySuffix="creators"):
            res.append( (group.id, group.Title()) )
        return DisplayList( tuple(res) )

    security.declarePublic('listItemTags')
    def listItemTags(self):
        '''Lists the available tags from the meeting config.'''
        res = []
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        for tag in meetingConfig.getAllItemTags().split('\n'):
            res.append( (tag, tag) )
        return DisplayList( tuple(res) )

    security.declarePublic('getMeetingsAcceptingItems')
    def getMeeting(self, brain=False):
        '''Returns the linked meeting if it exists.'''
        # getBRefs returns linked *objects* through a relationship defined in
        # a ReferenceField, while reference_catalog.getBackReferences returns
        # *brains*.
        if brain: # Faster
            res = self.reference_catalog.getBackReferences(self, 'MeetingItems')
        else:
            res = self.getBRefs('MeetingItems')
        if res:
            res = res[0]
        else:
            if brain:
                res = self.reference_catalog.getBackReferences(
                    self, 'MeetingLateItems')
            else:
                res = self.getBRefs('MeetingLateItems')
            if res:
                res = res[0]
            else:
                res = None
        return res

    security.declarePublic('hasMeeting')
    def hasMeeting(self):
        '''Is there a meeting tied to me?'''
        return self.getMeeting(brain=True) != None

    security.declarePublic('isLateFor')
    def isLate(self):
        '''Am I included in a meeting as a late item?'''
        if self.reference_catalog.getBackReferences(self, 'MeetingLateItems'):
            return True
        else: return False

    security.declarePublic('userMayModify')
    def userMayModify(self):
        '''Checks if the user has the right to update me.'''
        return checkPermission(ModifyPortalContent, self)

    security.declarePublic('showCategory')
    def showCategory(self):
        '''I must not show the "category" field if I use groups for defining
           categories.'''
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        return not meetingConfig.getUseGroupsAsCategories()

    security.declarePublic('listCategories')
    def listCategories(self):
        '''Returns a DisplayList containing all available active categories in
           the meeting config that corresponds me.'''
        res = []
        meetingConfig = getToolByName(self, TOOL_ID).getMeetingConfig(self)
        for cat in meetingConfig.getCategories():
            res.append( (cat.id, cat.Title()) )
        if len(res) > 4:
            res.insert(0, ('_none_',
                self.utranslate('make_a_choice', domain='PloneMeeting')))
        return DisplayList(tuple(res))

    security.declarePublic('getCategory')
    def getCategory(self, theObject=False):
        '''Returns the category of this item. When used by Archetypes,
           this method returns the category Id; when used elsewhere in
           the PloneMeeting code (with p_theObject=True), it returns
           the true Category object (or Group object if groups are used
           as categories).'''
        tool = getToolByName(self, TOOL_ID)
        try:
            if tool.getMeetingConfig(self).getUseGroupsAsCategories():
                res = getattr(tool, self.getProposingGroup())
            else:
                categoryId = self.getField('category').get(self)
                res = getattr(tool.getMeetingConfig(self).categories,
                              categoryId)
            if not theObject:
                res = res.id
        except AttributeError:
            res = ''
        return res

    security.declarePublic('getProposingGroup')
    def getProposingGroup(self, theObject=False):
        '''This redefined accessor may return the proposing group id or the real
           group if p_theObject is True.'''
        res = self.getField('proposingGroup').get(self) # = group id
        if res and theObject:
            tool = getToolByName(self, TOOL_ID)
            res = getattr(tool, res)
        return res

    security.declarePublic('decisionFieldIsEmpty')
    def decisionFieldIsEmpty(self):
        '''Is the 'decision' field empty ? '''
        return kupuFieldIsEmpty(self.getDecision())

    security.declarePublic('descriptionFieldIsEmpty')
    def descriptionFieldIsEmpty(self):
        '''Is the 'description' field empty ? '''
        return kupuFieldIsEmpty(self.Description())

    security.declarePublic('observationsFieldIsEmpty')
    def observationsFieldIsEmpty(self):
        '''Is the 'observations' field empty ? '''
        return kupuFieldIsEmpty(self.getObservations())

    security.declarePublic('wfConditions')
    def wfConditions(self):
        '''Returns the adapter that implements the interface that proposes
           methods for use as conditions in the workflow associated with this
           item.'''
        return getWorkflowAdapter(self, conditions=True)

    security.declarePublic('wfActions')
    def wfActions(self):
        '''Returns the adapter that implements the interface that proposes
           methods for use as actions in the workflow associated with this
           item.'''
        return getWorkflowAdapter(self, conditions=False)

    security.declarePublic('adapted')
    def adapted(self):
        '''Gets the "adapted" version of myself. If no custom adapter is found,
           this method returns me.'''
        return getCustomAdapter(self)

    security.declarePublic('attributeIsUsed')
    def attributeIsUsed(self, name):
        '''Is the attribute named p_name used in this meeting config ?'''
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        return (name in meetingConfig.getUsedItemAttributes())

    security.declarePublic('getAnnexesByType')
    def getAnnexesByType(self, decisionRelated=False, makeSubLists=True,
                         typesIds=[]):
        '''Returns an annexInfo dict for every annex linked to me:
           - if p_decisionRelated is False, it returns item-related annexes
             only; if True, it returns decision-related annexes.
           - if p_makeSubLists is True, the result (a list) contains a
             subList containing all annexes of a given type; if False,
             the result is a single list containing all requested annexes,
             sorted by annex type.
           If p_typesIds in not empty, only annexes of types having ids
           listed in this param will be returned.
           In all cases, within each annex type annexes are sorted by
           creation date (more recent last).'''
        meetingFileTypes = self.portal_plonemeeting.getMeetingConfig(
            self).getFileTypes(decisionRelated, typesIds=typesIds)
        res = []
        if not hasattr(self, 'annexIndex'):
            self.updateAnnexIndex()
        for fileType in meetingFileTypes:
            annexes = []
            for annexInfo in self.annexIndex:
                if (annexInfo['decisionRelated'] == decisionRelated) and \
                   (annexInfo['fileTypeId'] == fileType.id):
                    annexes.append(annexInfo)
            if annexes:
                if makeSubLists:
                    res.insert(0, annexes)
                    # You have noticed that in this case we sort file types
                    # in reverse order. This is because of the Plone menu
                    # widget that must show annexes.
                else:
                    res += annexes
        return res

    security.declarePublic('getLastInsertedAnnex')
    def getLastInsertedAnnex(self):
        '''Gets the last inserted annex on this item, be it decision-related
           or not.'''
        res = None
        if self.annexIndex:
            annexUid = self.annexIndex[-1]['uid']
            res = self.uid_catalog(UID=annexUid)[0].getObject()
        return res

    security.declarePublic('hasAnnexesWhere')
    def hasAnnexesWhere(self, decisionRelated=False):
        '''Have I at least one item- or decision-related annex ?'''
        res = False
        allAnnexes = self.getAnnexes()
        if decisionRelated:
            allAnnexes = self.getAnnexesDecision()
        return allAnnexes

    security.declarePublic('hasAdvices')
    def hasAdvices(self, withMissing=True):
        '''Have I at least one item-related advice ?'''
        if not hasattr(self, 'adviceIndex'):
            self.updateAdviceIndex()
        if (withMissing and len(self.adviceIndex[LIST_ADVISERS_KEY]) > 0):
            return True
        # Actual users must have the "View" permission for at least one
        # existing advice
        member = self.portal_membership.getAuthenticatedMember()
        for adviceUid in self.adviceIndex.keys():
            if (adviceUid != LIST_ADVISERS_KEY and \
                member.has_permission(View,
                self.uid_catalog(UID=adviceUid)[0].getObject())):
                return True
        return False

    security.declarePublic('queryState')
    def queryState(self):
        '''In what state am I ?'''
        return self.portal_workflow.getInfoFor(self, 'review_state')

    security.declarePublic('getObject')
    def getObject(self):
        '''Some PT macros must work with either an object or a brain as input.
        '''
        return self

    security.declarePublic('getSelf')
    def getSelf(self):
        '''All MeetingItem methods that are overridable through a custom adapter
           can't make the assumption that p_self corresponds to a MeetingItem
           instance. Indeed, p_self may correspond to an adapter instance. Those
           methods can retrieve the MeetingItem instance through a call to
           m_getSelf.'''
        res = self
        if self.__class__.__name__ != 'MeetingItem':
            res = self.context
        return res

    security.declarePublic('getItemReference')
    def getItemReference(self):
        '''Gets the reference of this item. Returns an empty string if the
           meeting is not decided yet.'''
        res = ''
        item = self.getSelf()
        if item.hasMeeting():
            meetingConfig = item.portal_plonemeeting.getMeetingConfig(item)
            itemRefFormat = meetingConfig.getItemReferenceFormat()
            if itemRefFormat.strip():
                portal = getToolByName(item, 'portal_url').getPortalObject()
                ctx = createExprContext(item.getParentNode(), portal, item)
                try:
                    res = Expression(itemRefFormat)(ctx)
                except Exception, e:
                    raise PloneMeetingError(ITEM_REF_ERROR % str(e))
        return res

    security.declarePublic('mustShowItemReference')
    def mustShowItemReference(self):
        '''See doc in interfaces.py'''
        res = False
        item = self.getSelf()
        if item.hasMeeting() and (item.getMeeting().queryState() != 'created'):
            res = True
        return res

    security.declarePublic('isDelayed')
    def isDelayed(self):
        '''See doc in interfaces.py'''
        return self.getSelf().queryState() == 'delayed'

    security.declarePublic('isRefused')
    def isRefused(self):
        '''See doc in interfaces.py'''
        return self.getSelf().queryState() == 'refused'

    security.declarePublic('getSpecificDocumentContext')
    def getSpecificDocumentContext(self):
        '''See doc in interfaces.py.'''
        return {}

    security.declarePublic('getSpecificMailContext')
    def getSpecificMailContext(self, event, translationMapping):
        '''See doc in interfaces.py.'''
        return None

    security.declarePublic('includeMailRecipient')
    def includeMailRecipient(self, event, userId):
        '''See doc in interfaces.py.'''
        return True

    security.declarePrivate('addRecurringItemToMeeting')
    def addRecurringItemToMeeting(self, meeting):
        '''See doc in interfaces.py.'''
        item = self.getSelf()
        # Retrieve the meeting history of the workflow used for the meeting
        meetingHistory = meeting.getWorkflowHistory()
        if not meetingHistory:
            lastTransition = '_init_'
        else:
            lastTransition = meetingHistory[0]['action']
        transitions = item.meetingTransitionsAcceptingRecurringItems
        if lastTransition and (lastTransition not in transitions):
            # A strange transition was chosen for addding a recurring item (ie
            # when putting back the meeting from 'published' to 'created' in
            # order to correct an error). In those cases we do nothing but
            # sending a mail to the site administrator for telling him that he
            # should change the settings linked to recurring items in the
            # corresponding meeting config.
            logger.warn(REC_ITEM_ERROR % (item.id,
                                          WRONG_TRANSITION % lastTransition))
            sendMail(None, item, 'recurringItemBadTransition')
            # We do not use delete_givenuid here but deleteGivenObject
            # that has a Manager proxy role because the item could be
            # not accessible by the MeetingManager.  In the case for example
            # where a recurring item is created with a proposingGroup the
            # MeetingManager is not in as a creator...
            # we must be sure that the item is removed in every case.
            item.removeGivenObject(item)
        else:
            wfTool = item.portal_workflow
            try:
                # Hmm... the currently published object is p_meeting, right?
                item.REQUEST.set('PUBLISHED', meeting)
                item.setPreferredMeeting(meeting.UID()) # This way it will
                # be considered as "late item" for this meeting if relevant.
                # Ok, now let's present the item in the meeting.
                for tr in item.itemTransitionsForPresentingIt:
                    wfTool.doActionFor(item, tr)
            except WorkflowException, wfe:
                logger.warn(REC_ITEM_ERROR % (item.id, str(wfe)))
                sendMail(None, item, 'recurringItemWorkflowError')
                item.removeGivenObject(item)

    security.declarePublic('mayBeLinkedToTasks')
    def mayBeLinkedToTasks(self):
        '''See doc in interfaces.py.'''
        item = self.getSelf()
        res = False
        if (item.queryState() == 'confirmed'):
            res = True
        elif (item.queryState() == 'itemarchived'):
            meetingConfig = item.portal_plonemeeting.getMeetingConfig(item)
            itemWorkflow = meetingConfig.getItemWorkflow()
            workflow_history = None
            if item.workflow_history.has_key(itemWorkflow):
                previousState = item.workflow_history[itemWorkflow][-2][
                    'review_state']
                if previousState == 'confirmed':
                    res = True
        return res

    security.declareProtected('Modify portal content', 'transformRichTextField')
    def transformRichTextField(self, fieldName, richContent):
        '''See doc in interfaces.py.'''
        return richContent

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated):
        '''See doc in interfaces.py.'''
    security.declarePublic('getInsertOrder')
    security.declarePublic('getInsertOrder')
    def getInsertOrder(self, sortOrder):
        '''When inserting an item into a meeting, depending on the sort method
           chosen in the meeting config we must insert the item at a given
           position that depends on the "insert order", ie the order of the
           category or proposing group specified for this meeting. p_sortOrder
           specifies this order.'''
        res = None
        item = self.getSelf()
        if sortOrder == 'on_categories':
            res = item.getCategory(True).getOrder()
        elif sortOrder == 'on_proposing_groups':
            res = item.getProposingGroup(True).getOrder()
        elif sortOrder == 'on_all_groups':
            res = item.getProposingGroup(True).getOrder(
                item.getAssociatedGroups())
        if res == None:
            raise 'sortOrder should be one of %s' % str(itemSortMethods[1:])
        return res

    security.declarePublic('sendMailIfRelevant')
    def sendMailIfRelevant(self, event, permissionOrRole, isRole=False):
        return sendMailIfRelevant(self, event, permissionOrRole, isRole)

    security.declarePrivate('transformAllRichTextFields')
    def transformAllRichTextFields(self):
        '''Potentially, all richtext fields defined on an item (description,
           decision, etc) may be transformed via the method
           transformRichTextField that may be overridden by an adapter. This
           method calls it for every rich text field defined on this item, if
           the user has the permission to update the field.'''
        member = self.portal_membership.getAuthenticatedMember()
        for field in self.schema.fields():
            if field.widget.getName() == 'RichWidget':
                writePermission = 'Modify portal content'
                if hasattr(field, 'write_permission'):
                    writePermission = field.write_permission
                if member.has_permission(writePermission, self):
                    field.set(self, self.adapted().transformRichTextField(
                        field.getName(), field.get(self)))
    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self):
        # Add a custom modification_date that does not take into account some
        # events like state changes
        self.pm_modification_date = self.modification_date
        # Create a "black list" of annex names. Every time an annex will be
        # created for this item, the name used for it (=id) will be stored here
        # and will not be removed even if the annex is removed. This way, two
        # annexes (or two versions of it) will always have different URLs, so
        # we avoid problems due to browser caches.
        self.alreadyUsedAnnexNames = PersistentList()
        # The following field allows to store events that occurred in the life
        # of an item, like annex deletions or additions.
        self.itemHistory = PersistentList()
        # Add a dictionary that will store the votes on this item
        self.votes = PersistentMapping() # Keys are MeetingUser ids, values are
        # vote vales (strings). If votes are secret (self.votesAreSecret is
        # True), the structure is different: keys are vote values and values
        # are numbers of times the vote value has been chosen.
        # Compute mandatory advisors
        self.setMandatoryAdvisers(self.calculateMandatoryAdvisers())
        # Remove temp local role that allowed to create the item in
        # portal_factory
        user = self.portal_membership.getAuthenticatedMember()
        self.manage_delLocalRoles([user.getId()])
        self.manage_addLocalRoles(user.getId(), ('Owner',))
        self.updateLocalRoles()
        # Tell the color system that the current user has consulted this item.
        self.portal_plonemeeting.rememberAccess(self.UID(), commitNeeded=False)
        # Apply potential transformations to richtext fields
        self.transformAllRichTextFields()
        # Call sub-product-specific behaviour
        self.adapted().onEdit(isCreated=True)
        # Items that are created in the tool for creating recurring items
        # must not appear in searches.
        if self.isDefinedInTool():
            self.unindexObject()
        else:
            self.reindexObject()
        # Initialize the adviceIndex
        self.updateAdviceIndex()

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self):
        #now that we have every informations about the item, we can set the
        #mandatory advisers
        self.setMandatoryAdvisers(self.calculateMandatoryAdvisers())
        self.updateLocalRoles()
        # Tell the color system that the current user has consulted this item.
        self.portal_plonemeeting.rememberAccess(self.UID(), commitNeeded=False)
        # Apply potential transformations to richtext fields
        self.transformAllRichTextFields()
        # Call sub-product-specific behaviour
        self.adapted().onEdit(isCreated=False)
        # We set the adviceIndex property
        self.updateAdviceIndex()
        if self.isDefinedInTool():
            self.unindexObject()
        else:
            self.reindexObject()

    security.declarePublic('updateHistory')
    def updateHistory(self, action, subObj, **kwargs):
        '''Adds an event to the item history. p_action may be 'add' or 'delete'.
           p_subObj is the sub-object created or deleted (ie an annex). p_kwargs
           are additional entries that will be stored in the event within item's
           history.'''
        # Update history only if the item is in some states
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        if self.queryState() in meetingConfig.getRecordItemHistoryStates():
            # Create the event
            user = self.portal_membership.getAuthenticatedMember()
            event = {'action': action, 'type': subObj.meta_type,
                     'title': subObj.Title(), 'time': DateTime(),
                     'actor': user.id}
            event.update(kwargs)
            # Add the event to item's history
            self.itemHistory.append(event)

    security.declarePublic('isValidAnnexId')
    def isValidAnnexId(self, idCandidate):
        '''May p_idCandidate be used for a new annex that will be linked to
           this item?'''
        res = True
        if hasattr(self.aq_base, idCandidate) or \
           (idCandidate in self.alreadyUsedAnnexNames):
            res = False
        return res

    security.declareProtected('Delete objects', 'removeAllAnnexes')
    def removeAllAnnexes(self):
        '''Removes all annexes linked to this item.'''
        # We can use manage_delObjects because the container is a MeetingItem.
        # As much as possible, use delete_givenuid.
        self.manage_delObjects( [a.getId() for a in self.getAnnexes()])
        self.manage_delObjects( [a.getId() for a in self.getAnnexesDecision()])

    security.declareProtected('Delete objects', 'removeAllAdvices')
    def removeAllAdvices(self):
        '''Removes all advices linked to this item.'''
        # we can use manage_delObjects because the container is a MeetingItem
        # as much as possible, use delete_givenuid...
        self.manage_delObjects( [a.getId() for a in self.getAdvices()])

    security.declareProtected('Modify portal content', 'updateLocalRoles')
    def updateLocalRoles(self):
        '''Updates the local roles of this item, regarding the proposing
           group.'''
        tool = self.portal_plonemeeting
        # Remove first all local roles previously set on the item
        allRelevantGroupIds = []
        for meetingGroup in tool.objectValues('MeetingGroup'):
            for suffix in MEETINGROLES.iterkeys():
                allRelevantGroupIds.append(meetingGroup.getPloneGroupId(suffix))
        toRemove = []
        for principalId, localRoles in self.get_local_roles():
            if (principalId in allRelevantGroupIds):
                toRemove.append(principalId)
        self.manage_delLocalRoles(toRemove)
        # Add the local roles corresponding to the proposing group
        meetingGroup = getattr(tool, self.getProposingGroup(), None)
        if meetingGroup:
            for groupSuffix in MEETINGROLES.iterkeys():
                groupId = meetingGroup.getPloneGroupId(groupSuffix)
                ploneGroup = self.portal_groups.getGroupById(groupId)
                # If the corresponding Plone group does not exist anymore,
                # recreate it.
                if not ploneGroup:
                    meetingGroup._createPloneGroup(groupSuffix)
                meetingRole = ploneGroup.getProperties()['meetingRole']
                self.manage_addLocalRoles(groupId, (meetingRole,))

        # Add the local roles corresponding to the selected mandatory and
        # optional advisers
        if self.isAdvicesEnabled():
            advisers = self.adapted().getAdvisers()
            if advisers:
                for adviserId in advisers:
                    ploneGroup = self.portal_groups.getGroupById(adviserId)
                    # If the corresponding Plone group does not exist anymore,
                    # recreate it.
                    if not ploneGroup:
                        # we find the meeting group name by removing the suffix
                        meetingGroupId = adviserId[0:- len('_advisers')]
                        meetingGroup = getattr(tool.aq_inner, meetingGroupId,
                            None)
                        if meetingGroup:
                            meetingGroup._createPloneGroup('advisers')
                            continue
                    meetingRole = ploneGroup.getProperties()['meetingRole']
                    self.manage_addLocalRoles(adviserId, (meetingRole,))
            # Update advices local roles
            for advice in self.getAdvices():
                advice.updateLocalRoles()

        # Add the local roles corresponding to the selected copyGroups.
        # We give the MeetingObserverLocalCopy role to the selected groups
        # this will give them a read-only access to the item
        if self.isCopiesEnabled():
            copyGroups = self.getCopyGroups()
            if copyGroups:
                for copyGroup in copyGroups:
                    ploneGroup = self.portal_groups.getGroupById(copyGroup)
                    # If the corresponding Plone group does not exist anymore,
                    # recreate it.
                    if not ploneGroup:
                        # We find the meeting group name by removing the suffix
                        splitted_copyGroup = copyGroup.split('_')
                        meetingGroupSuffix = splitted_copyGroup.pop(-1)
                        # Do this if we have a '_' in the name of the
                        # meetingGroup.
                        meetingGroupId = '_'.join(splitted_copyGroup)
                        meetingGroup = getattr(tool.aq_inner, meetingGroupId,
                            None)
                        if meetingGroup:
                            meetingGroup._createPloneGroup(meetingGroupSuffix)
                            continue
                    # We give the MeetingObserverLocalCopy role to the groups
                    # this is a read-only view on the item
                    self.manage_addLocalRoles(copyGroup,
                        ('MeetingObserverLocalCopy',))

    security.declareProtected(ModifyPortalContent, 'processForm')
    def processForm(self, *args, **kwargs):
        '''We override this method in order to be able to set correctly our own
           pm_modification_date for this object: if a change occurred in the
           title or description, we update the modification date.

           Indeed, we need a PloneMeeting-specific modification date that does
           not take into account some changes like state changes. This is a
           special requirement for the PloneMeeting "color system", that allows
           users to see in a given color some changes that occurred on items and
           annexes.'''
        if self.Title() != self.REQUEST.get('title'):
            self.pm_modification_date = DateTime()
        if self.Description() != self.REQUEST.get('description'):
            self.pm_modification_date = DateTime()
        return BaseFolder.processForm(self, *args, **kwargs)

    security.declareProtected(ModifyPortalContent, 'calculateMandatoryAdvisers')
    def calculateMandatoryAdvisers(self):
        '''Calculate the mandatory advisers by evaluating the TAL expression
           on every active MeetingGroup where at least one user is in the
           '_advisers'-suffixed linked Plone group. WARNING, if the current
           logged in user is a 'Manager', we do not calculate the
           mandatoryAdvisers as this is the only role able to define particular
           advisers as mandatory.'''
        # If we are a 'Manager', do nothing.
        if self.portal_membership.getAuthenticatedMember().has_role('Manager'):
            return self.getMandatoryAdvisers()
        mGroups = self.portal_plonemeeting.getActiveGroups(
            notEmptySuffix='advisers')
        portal = getToolByName(self, 'portal_url').getPortalObject()
        groups = []
        for mGroup in mGroups:
            # Check that the TAL expression on the group returns True
            ctx = createExprContext(self.getParentNode(), portal, self)
            ctx.setGlobal('item', self)
            res = False
            try:
                res = Expression(mGroup.getGivesMandatoryAdviceOn())(ctx)
            except Exception, e:
                    raise PloneMeetingError(
                        GROUP_MANDATORY_CONDITION_ERROR % str(e))
            if res:
                groups.append('%s_advisers' % mGroup.id)
        return groups

    security.declarePublic('listMandatoryAdvisers')
    def listMandatoryAdvisers(self):
        '''Lists the default mandatory advisers as defined in the meeting
           configuration.'''
        mGroups = self.portal_plonemeeting.getActiveGroups(
            notEmptySuffix='advisers')
        pgp = self.portal_groups
        res = []
        for mGroup in mGroups:
            adviser_id = "%s_advisers" % (mGroup.id)
            group = pgp.getGroupById(adviser_id)
            res.append( (adviser_id, group.getProperty('title')) )
        return DisplayList(tuple(res))

    security.declarePublic('listOptionalAdvisers')
    def listOptionalAdvisers(self):
        '''Lists the optional advisers as defined in the meeting
           configuration.'''
        meetingconfig = self.portal_plonemeeting.getMeetingConfig(self)
        pgp = self.portal_groups
        res = []
        for adviser_id in meetingconfig.getOptionalAdvisers():
            group = pgp.getGroupById(adviser_id)
            res.append((adviser_id, group.getProperty('title')))
        return DisplayList(tuple(res))

    security.declarePublic('isAdvicesEnabled')
    def isAdvicesEnabled(self):
        '''Is the "advices" functionality enabled for this meeting config?'''
        meetingconfig = self.portal_plonemeeting.getMeetingConfig(self)
        return meetingconfig.getUseAdvices()

    security.declarePublic('isCopiesEnabled')
    def isCopiesEnabled(self):
        '''Is the "copies" functionality enabled for this meeting config?'''
        meetingconfig = self.portal_plonemeeting.getMeetingConfig(self)
        return meetingconfig.getUseCopies()

    security.declarePublic('isVotesEnabled')
    def isVotesEnabled(self):
        '''Returns True if the votes are enabled.'''
        meetingconfig = self.portal_plonemeeting.getMeetingConfig(self)
        return meetingconfig.getUseVotes()

    security.declarePublic('getSiblingItemUid')
    def getSiblingItemUid(self, whichItem):
        '''If this item is within a meeting, this method returns the UID of
           a sibling item that may be accessed by the current user. p_whichItem
           can be:
           - 'previous' (the previous item within the meeting)
           - 'next' (the next item item within the meeting)
           - 'first' (the first item of the meeting)
           - 'last' (the last item of the meeting).
           If there is no sibling (or if it has no sense to ask for this
           sibling), the method returns None. If there is a sibling, but the
           user can't see it, the method returns False.
        '''
        res = None
        sibling = None
        if self.hasMeeting():
            meeting = self.getMeeting()
            itemUids = meeting.getRawItems()
            if itemUids:
                lastItemNumber = len(meeting.getRawItems()) + \
                                 len(meeting.getRawLateItems())
                itemNumber = self.getItemNumber(relativeTo='meeting')
                if whichItem == 'previous':
                    # Is a previous item available ?
                    if itemNumber != 1:
                        sibling = meeting.getItemByNumber(itemNumber-1)
                elif whichItem == 'next':
                    # Is a next item available ?
                    if itemNumber != lastItemNumber:
                        sibling = meeting.getItemByNumber(itemNumber+1)
                elif whichItem == 'first':
                    sibling = meeting.getItemByNumber(1)
                elif whichItem == 'last':
                    sibling = meeting.getItemByNumber(lastItemNumber)
        if sibling:
            user = self.portal_membership.getAuthenticatedMember()
            if user.has_permission('View', sibling):
                res = sibling.UID()
            else:
                res = False
        return res

    security.declarePublic('getAdvicesSortedByAgreementLevel')
    def getAdvicesSortedByAgreementLevel(self, withMissing=True):
        '''Return advices ('adviceInfo' dicts) sorted by agreement level.

           (Because this method is based on 'adviceIndex' property, which keeps
           in memory infos about ALL advices registred in item folder, we have
           to check 'View' permission of actual user for each advice object.'''
        if not hasattr(self, 'adviceIndex'):
            self.updateAdviceIndex()
        res = []
        # Copy the advisers dict (in order to identify, after iterating
        # existing advices, advisers who haven't yet provided an advice)
        dictAdvisers = self.adviceIndex[LIST_ADVISERS_KEY].copy()
        # adding existing advices
        member = self.portal_membership.getAuthenticatedMember()
        for adviceUid, adviceInfo in self.adviceIndex.items():
            if (adviceUid != LIST_ADVISERS_KEY and \
                member.has_permission(View,
                self.uid_catalog(UID=adviceUid)[0].getObject())):
                res.append(adviceInfo)
                dictAdvisers.pop(adviceInfo['adviser_id'], 0)
        res.sort(key = lambda x: x['agLevel_id'])
        # if "withMissing" is true, we append a "missing advice" for each
        # adviser who haven't yet provided an advice
        if (withMissing and (len(dictAdvisers) > 0)):
            noAdviceLabel = self.utranslate('agreement_level_no_advices',
                domain='PloneMeeting')
            for adviserId, adviserTitle in dictAdvisers.items():
                res.append({'agLevel_id': MISSING_ADVICES_ID,
                            'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
                            'agLevel_Title': noAdviceLabel,
                            'adviser_id': adviserId,
                            'adviser_Title':adviserTitle})
        return res

    security.declarePublic('getAdvicesByAgreementLevel')
    def getAdvicesByAgreementLevel(self, withMissing=True):
        '''Return advices ('adviceInfo' dicts) grouped by agreement level:
           [ [[agLevel_id, agLevel_iconUrl], [adviceInfo, ...]], ... ].'''
        tmp = {}
        for adviceInfo in self.getAdvicesSortedByAgreementLevel(withMissing):
            agLevelId = adviceInfo['agLevel_id']
            if (not tmp.has_key(agLevelId)):
                tmp[agLevelId] = [[agLevelId,
                                   adviceInfo['agLevel_iconUrl']], []]
            tmp[agLevelId][1].append(adviceInfo)
        return tmp.values()

    security.declarePublic('getAdvicesSortedByAgreementLevel')
    def getAdvices(self):
        '''Return contained advices.'''
        return self.objectValues('MeetingAdvice')

    security.declarePublic('getAdvisers')
    def getAdvisers(self):
        '''Return dict of groups allowed to provide an advice (optional and
           mandatory advisers).'''
        item = self.getSelf()
        tool = item.portal_plonemeeting
        res = {}
        for idAdviser in item.getOptionalAdvisers():
            res[idAdviser] = tool.getMeetingGroup(idAdviser).Title()
        for idAdviser in item.getMandatoryAdvisers():
            res[idAdviser] = tool.getMeetingGroup(idAdviser).Title()
        return res

    security.declarePublic('indexAdvisers')
    def indexAdvisers(self):
        '''Return a list of advisers plone groups for indexing. This is used to
           index the advisers in portal_catalog.'''
        tool = self.portal_plonemeeting
        advisers = self.getOptionalAdvisers() + self.getMandatoryAdvisers()
        #check now if the advice has been given or not
        res = []
        for adviser in advisers:
            suffix = '0'
            for adviceType in self.adviceIndex.iteritems():
                if adviceType[1].has_key('adviser_id'):
                    if adviser ==  adviceType[1]['adviser_id']:
                        suffix = '1'
                        break
            res.append(adviser + suffix)
        return res

    security.declarePublic('listAdvisersForUser')
    def listAdvisersForUser(self):
        '''Returns a list containing the "adviser groups" on whose behalf a
           user may add an advice related to me.

           - If user has Manager or MeetingManager role on me, he may add an
             advice even if it does not belong to any 'advisers group' which
             has MeetingAdviser role on me, and although it is not part of
             any 'advisers group' defined in meetingconfig.
             So this user should have the freedom to determine the 'advisers
             group' on whose behalf he submit the advice, by selecting inside
             all existing 'advisers groups' defined in meetingconfig, but also
             to submit the advice in the name of the 'advisers group(s)' linked
             to the meetinggroup(s) which is eventually member.

           - Else the user may only add an advice in the name of "advisers
             group(s)" he's member, and which have 'MeetingAdviser' role on me.
        '''
        res = {}
        tool = self.portal_plonemeeting
        user = self.portal_membership.getAuthenticatedMember()
        # Add 'advisers group(s)' user is member, and which have
        # 'MeetingAdviser' role on me
        # (Note that an 'advisers group' may have 'MeetingAdviser' role on me
        # even when it isn't designated by the creator of the item; indeed,
        # at the creation of an item, 'advisers group' sub-group of item
        # creator meeting group also inherit this role.)
        for group in tool.getUserPloneGroups(userId=user.id):
            # If group is not an "advisers groups" sub-group, and/or hasn't
            # 'MeetingAdviser' local role on me, pass
            groupId = group.getId()
            if not (groupId.endswith("_advisers") \
                    and filter(lambda x:x=='MeetingAdviser',
                                self.get_local_roles_for_userid(groupId))):
                continue
            res[groupId] = tool.getMeetingGroup(groupId).Title()
        if (user.has_role('MeetingManager') or user.has_role('Manager')):
            # Add all "advisers groups" defined in meetingconfig
            meetingconfig = tool.getMeetingConfig(self)
            for idAdviser in self.listMandatoryAdvisers():
                if not res.has_key(idAdviser):
                    res[idAdviser] = tool.getMeetingGroup(idAdviser).Title()
            for idAdviser in meetingconfig.getOptionalAdvisers():
                if not res.has_key(idAdviser):
                    res[idAdviser] = tool.getMeetingGroup(idAdviser).Title()
            # Add the "advisers group(s)" of meetinggroup(s) which user is
            # eventually member
            for meetingGroup in tool.getUserMeetingGroups(userId=user.id):
                idAdviser = '%s_advisers' % meetingGroup.id
                if not res.has_key(idAdviser):
                    res[idAdviser] = tool.getMeetingGroup(idAdviser).Title()
        return DisplayList(tuple([(k, v) for k, v in res.items()]))

    security.declarePublic('isDesignatedAdviser')
    def isDesignatedAdviser(self, idAdviser):
        '''Check if p_idAdviser group is a "designated" adviser of me
           (ie if it does belong to "optional" or "mandatory" advisers prop.)
        '''
        return (idAdviser in self.adapted().getAdvisers().keys())

    security.declarePublic('mayReviewAdvice')
    def mayReviewAdvice(self):
        '''Return true if actual user has 'ReviewPortalContent' or
           'DeleteObjects'permission for at least one advice of me.
           (Used to know if we sould or should not display "actions" column in
           'advicesMacro' macro - see advices_macros.pt)'''
        if not hasattr(self, 'adviceIndex'):
            self.updateAdviceIndex()
        member = self.portal_membership.getAuthenticatedMember()
        for adviceUid in self.adviceIndex.keys():
            if (adviceUid != LIST_ADVISERS_KEY):
                advice = self.uid_catalog(UID=adviceUid)[0].getObject()
                if (member.has_permission(ReviewPortalContent, advice) \
                    or member.has_permission(DeleteObjects, advice)):
                    return True
        return False

    security.declarePublic('listCopyGroups')
    def listCopyGroups(self):
        '''Lists the groups that will be selectable to be in copy for this
           item.'''
        meetingconfig = self.portal_plonemeeting.getMeetingConfig(self)
        pgp = self.portal_groups
        res = []
        for groupId in meetingconfig.getSelectableCopyGroups():
            group = pgp.getGroupById(groupId)
            res.append((groupId, group.getProperty('title')))
        return DisplayList(tuple(res))

    security.declarePublic('showDuplicateItemAction')
    def showDuplicateItemAction(self):
        '''Condition for displaying the 'duplicate' action in the interface
           Return True if the user can duplicate the item.'''
        # Conditions for being able to see the "duplicate an item" action:
        # - portal_plonemeeting.getPloneDiskAware is False;
        # - the duplication is enabled in the config;
        # - the user is creator of the item.proposingGroup.
        # The user will duplicate the item in his own folder (the user having
        # just one single Large Plone Folder in this case).
        tool = self.portal_plonemeeting
        if tool.getPloneDiskAware() or \
            not tool.getMeetingConfig(self).getEnableDuplication():
            # The user is Plone disk aware, he should not see the action
            return False
        for meetingGroup in tool.getUserMeetingGroups(suffix="creators"):
            # Check if the user is creator for the proposing group
            if self.getProposingGroup() == meetingGroup.id:
                return True
        return False

    security.declarePublic('showCopyItemAction')
    def showCopyItemAction(self):
        '''Condition for displaying the 'copyitem' action in the interface.
           Return True if the user can copy the item.'''
        # Conditions for being able to see the "copy an item" action:
        # - portal_plonemeeting.getPloneDiskAware is True
        # - the duplication is enabled in the config
        # - the user is creator of the item.proposingGroup
        tool = self.portal_plonemeeting
        if not tool.getPloneDiskAware():
            return False
        if not tool.getMeetingConfig(self).getEnableDuplication():
            return False
        for meetingGroup in tool.getUserMeetingGroups(suffix="creators"):
            #check if the user is creator for the proposing group
            if self.getProposingGroup() == meetingGroup.id:
                return True
        return False

    security.declareProtected('Modify portal content', 'setClassifier')
    def setClassifier(self, value):
        if value:
            oldValue = self.getClassifier()
            self.getField('classifier').set(self, value)
            newValue = self.getClassifier()
            if not oldValue or (oldValue.id != newValue.id):
                # We must update the item count of the new classifier.
                # We do NOT decrement the item count of the old classifier if
                # it existed.
                newValue.incrementItemsCount()

    security.declareProtected('Modify portal content', 'setCategory')
    def setCategory(self, newValue):
        if newValue:
            oldValue = self.getCategory()
            self.getField('category').set(self, newValue)
            if not oldValue or (oldValue != newValue):
                # We must update the item count of the new category.
                # We do NOT decrement the item count of the old category if
                # it existed.
                try:
                    self.getCategory(True).incrementItemsCount()
                except AttributeError, ae:
                    # The category object has not been found. It probably
                    # means that the current category setter is called by
                    # Archetypes in the process of creating a temp object, so
                    # in this case we don't care about incrementing the items
                    # count.
                    pass

    security.declarePublic('clone')
    def clone(self, copyAnnexes=True, copyAdvices=True, newOwnerId=None):
        '''Clones in the PloneMeetingFolder of the current user, or p_newOwnerId
           if given (this guy will also become owner of this item).'''
        # Get the PloneMeetingFolder of the current user as destFolder
        tool = self.portal_plonemeeting
        meetingConfigId = tool.getMeetingConfig(self).getId()
        destFolder = tool.getPloneMeetingFolder(meetingConfigId, newOwnerId)
        # Copy/paste item into the folder
        sourceFolder = self.getParentNode()
        copiedData = sourceFolder.manage_copyObjects(ids=[self.id])
        return tool.pasteItems(destFolder, copiedData, copyAnnexes=copyAnnexes,
            copyAdvices=copyAdvices, newOwnerId=newOwnerId)[0]

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        '''This is a workaround to avoid a Plone design problem where it is
           possible to remove a folder containing objects you can not
           remove.'''
        # If we are here, everything has already been checked before.
        # Just check that the item is myself or a Plone Site.
        # We can remove an item directly, not "through" his container.
        if not item.meta_type in ['Plone Site', 'MeetingItem', ]:
            user = self.portal_membership.getAuthenticatedMember()
            logger.warn(BEFOREDELETE_ERROR % (user.getId(), self.id))
            raise BeforeDeleteException, "can_not_delete_meetingitem_container"
        # Before deleting me, unlink me from a meeting if necessary.
        if self.hasMeeting():
            self.getMeeting().removeItem(self)
        BaseFolder.manage_beforeDelete(self, item, container)

    security.declarePublic('getMeetingUsers')
    def getMeetingUsers(self, usages=('voter',)):
        '''Gets, among attendees for this item, the meeting users which have a
           usage among p_usages (voters, attendees, ...).'''
        res = []
        if self.hasMeeting():
            for meetingUser in self.getMeeting().getAttendees(
                True, includeDeleted=False):
                for usage in usages:
                    if usage in meetingUser.getUsages():
                        if meetingUser not in res:
                            res.append(meetingUser)
                            break
        return res

    security.declarePublic('displayMandatoryAdvisersField')
    def displayMandatoryAdvisersField(self):
        '''Return True if the mandatoryAdvisers field has to be
           displayed'''
        #check if the 'advices' functionnality is activated
        #in the meetingConfig
        if not self.isAdvicesEnabled():
            return False
        #check if at least one adviser is selectable
        if not len(self.listMandatoryAdvisers()):
            return False
        #this field is only displayed to Managers
        member = self.portal_membership.getAuthenticatedMember()
        if not member.has_role('Manager'):
            return False
        return True

    security.declarePublic('showVotes')
    def showVotes(self):
        '''Must I show the "votes" tab on this item?'''
        if self.hasMeeting() and self.getMeeting().adapted().showVotes():
            return True
        return False

    security.declarePublic('getVoteValue')
    def getVoteValue(self, userId):
        '''What is the vote value for user with id p_userId?'''
        if self.getVotesAreSecret():   raise 'Unusable when votes are secret.'
        if self.votes.has_key(userId): return self.votes[userId]
        else:
            meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
            return meetingConfig.getDefaultVoteValue()

    security.declarePublic('getVoteCount')
    def getVoteCount(self, voteValue):
        '''Gets the number of votes for p_voteValue.'''
        if not self.getVotesAreSecret(): raise 'Unsusable when votes are public'
        if self.votes.has_key(voteValue):return self.votes[voteValue]
        else:                            return 0

    security.declarePublic('updateVoteValues')
    def updateVoteValues(self, newVoteValues):
        '''p_newVoteValues is a dictionary that contains a bunch of new vote
           values.'''
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        user = self.portal_membership.getAuthenticatedMember()
        for ploneUserId in newVoteValues.iterkeys():
            # Check that the current user can update the vote of this user
            meetingUser = meetingConfig.getMeetingUserFromPloneUser(ploneUserId)
            if meetingUser.adapted().mayEditVote(user, self):
                self.votes[ploneUserId] = newVoteValues[ploneUserId]

    security.declarePublic('updateVoteCounts')
    def updateVoteCounts(self, newVoteCounts):
        '''p_newVoteCounts is a dictionary that contains, for every vote value,
           new vote counts.'''
        if not self.mayEditVotes(): raise "This user can't update votes."
        for voteValue, voteCount in newVoteCounts.iteritems():
            self.votes[voteValue] = voteCount

    security.declarePublic('getVotesByValue')
    def getVotesByValue(self):
        '''Returns a dict of all the votes on self, keyed by vote values.'''
        mConfig = self.portal_plonemeeting.getMeetingConfig(self)
        member = self.portal_membership.getAuthenticatedMember()
        newDict = {}
        # Retrieve users that can vote
        mUsers = self.getMeetingUsers()
        # Retrieve activated vote values from the configuration
        voteValues = mConfig.getUsedVoteValues()
        completeVoteValues = list(voteValues)
        # Add the 'not_yet' value by default
        if not NOT_ENCODED_VOTE_VALUE in completeVoteValues:
            completeVoteValues.append(NOT_ENCODED_VOTE_VALUE)
        # Add the 'not_consultable' value by default
        completeVoteValues.append(NOT_CONSULTABLE_VOTE_VALUE)
        # Initialize the new dict
        for voteValue in completeVoteValues:
            newDict[voteValue] = list()
        # Use a temporary dict for working.
        for mUser in mUsers:
            if not mUser.adapted().mayConsultVote(member, self):
                newDict[NOT_CONSULTABLE_VOTE_VALUE].append(mUser)
                continue
            if self.votes.has_key(mUser.ploneUserId):
                newDict[self.votes[mUser.ploneUserId]].append(mUser)
            else:
                # If we do not have this vote, it is that the voter
                # still did not vote.
                newDict[NOT_ENCODED_VOTE_VALUE].append(mUser)
        # Build a list with the dict to keep the order.
        newList = []
        for voteValue in completeVoteValues:
            newList.append((voteValue, newDict[voteValue]))
        return newList

    security.declarePublic('mayConsultVotes')
    def mayConsultVotes(self):
        '''Returns True if the current user may consult all votes for p_self.'''
        user = self.portal_membership.getAuthenticatedMember()
        for mUser in self.getMeetingUsers():
            if not mUser.adapted().mayConsultVote(user, self): return False
        return True

    security.declarePublic('mayEditVotes')
    def mayEditVotes(self):
        '''Returns True if the current user may edit all votes for p_self.'''
        user = self.portal_membership.getAuthenticatedMember()
        for mUser in self.getMeetingUsers():
            if not mUser.adapted().mayEditVote(user, self): return False
        return True



registerType(MeetingItem, PROJECTNAME)
# end of class MeetingItem

##code-section module-footer #fill in your manual code here
def onAddMeetingItem(item, event):
    '''This method is called every time a MeetingItem is created, even in
       portal_factory. Local roles defined on an item define who may view
       or edit it. But at the time the item is created in portal_factory,
       local roles are not defined yet. So here we add a temporary local
       role to the currently logged user that allows him to create the
       item. In item.at_post_create_script we will remove this temp local
       role.'''
    user = item.portal_membership.getAuthenticatedMember()
    item.manage_addLocalRoles(user.getId(), ('MeetingMember',))
##/code-section module-footer



