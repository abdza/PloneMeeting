# -*- coding: utf-8 -*-
#
# File: Meeting.py
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
from StringIO import StringIO
from xml.dom import minidom
from persistent.mapping import PersistentMapping
from zope.interface import implements
from Globals import InitializeClass
from DateTime import DateTime
from OFS.ObjectManager import BeforeDeleteException
from Products.CMFPlone.utils import normalizeString
from Products.CMFCore.permissions import ReviewPortalContent,ModifyPortalContent
from Products.validation.interfaces.IValidator import IValidator
from Products.validation import validation
import Products.PloneMeeting
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.interfaces import IMeetingWorkflowConditions, \
                                             IMeetingWorkflowActions
from Products.PloneMeeting.utils import \
     getWorkflowAdapter, getCustomAdapter, kupuFieldIsEmpty, \
     KUPU_EMPTY_VALUES, checkPermission, getCurrentMeetingObject, \
     HubSessionsMarshaller, sendMail, addRecurringItemsIfRelevant, \
     clonePermissions, kupuEquals, replaceHtmlEntities
from Products.PloneMeeting.MeetingUser import DummyMeetingUser
import logging
logger = logging.getLogger('PloneMeeting')
#import xml.sax
#newparser = xml.sax.make_parser(["xml.sax.drivers2.drv_xmlproc"])
#newparser = xml.sax.make_parser(["appy.pod.xhtml2odt.XhtmlParser"])

# PloneMeetingError-related constants -----------------------------------------
BEFOREDELETE_ERROR = 'A BeforeDeleteException was raised by "%s" while ' \
    'trying to delete a meeting with id "%s"'

# Marshaller -------------------------------------------------------------------
class MeetingMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a meeting into a XML file that one may get through
       WebDAV.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all_with_metadata'
    fieldsToExclude = ['allItemsAtOnce', 'allowDiscussion']
    rootElementName = 'meeting'
InitializeClass(MeetingMarshaller)

# Adapters ---------------------------------------------------------------------
class MeetingWorkflowConditions:
    '''Adapts a meeting to interface IMeetingWorkflowConditions.'''
    implements(IMeetingWorkflowConditions)
    security = ClassSecurityInfo()

    # Item states when a decision was not take yet.
    notDecidedStates = ('presented', 'itempublished', 'itemfrozen')
    notDecidedStatesPlusDelayed = notDecidedStates + ('delayed',)
    # Item states when a final decision is taken
    archivableStates = ('confirmed', 'delayed', 'refused')

    # Meeting states for meetings accepting items
    acceptItemsStates = ('created', 'published', 'frozen', 'decided')

    def __init__(self, meeting):
        self.context = meeting

    def _atLeastOneDecisionIsTaken(self):
        '''Returns True if at least one decision was taken on an item (excepted
           the decision to delay an item, which is a "non-decision").'''
        res = False
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() not in self.notDecidedStatesPlusDelayed:
                res = True
                break
        return res

    def _decisionsAreTakenForEveryItem(self):
        '''Returns True if a decision is taken for every item.'''
        res = True
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() in self.notDecidedStates:
                res = False
                break
        return res

    def _decisionsAreArchivable(self):
        '''Returns True all the decisions may be archived.'''
        res = True
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() not in self.archivableStates:
                res = False
                break
        return res

    def _decisionsWereConfirmed(self):
        '''Returns True if at least one decision was taken on an item'''
        res = False
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() == 'confirmed':
                res = True
                break
        return res

    def _allItemsAreDelayed(self):
        '''Are all items contained in this meeting delayed ?'''
        res = True
        for item in self.context.getAllItems(ordered=True):
            if not item.adapted().isDelayed():
                res = False
                break
        return res

    security.declarePublic('mayAcceptItems')
    def mayAcceptItems(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           (self.context.queryState() in self.acceptItemsStates):
            res = True
        return res

    security.declarePublic('mayPublish')
    def mayPublish(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           self.context.getRawItems():
            res = True
        return res

    security.declarePublic('mayFreeze')
    def mayFreeze(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayDecide')
    def mayDecide(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           self.context.getDate().isPast():
            res = True # At least at present
            for item in self.context.getAllItems(ordered=True):
                if (item.queryState() == 'itemfrozen') and \
                   (not item.wfConditions().mayDecide()):
                    res = False
                    break
        return res

    security.declarePublic('mayCorrect')
    def mayCorrect(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context):
            currentState = self.context.queryState()
            if currentState == 'published':
                res = True
                publishedObject = getCurrentMeetingObject(self.context)
                if self._atLeastOneDecisionIsTaken() or \
                   self.context.getRawLateItems() or \
                   (not isinstance(publishedObject, Meeting)):
                    res = False
                    # For the latter condition, if we are not on the 'Meeting'
                    # page and we try to 'go back to created', we will also
                    # try to change presented items' states, which will not be
                    # possible if the published object is not the Meeting.
            elif currentState == 'frozen':
                res = True
                publishedObject = getCurrentMeetingObject(self.context)
                if self._atLeastOneDecisionIsTaken() or \
                   (not isinstance(publishedObject, Meeting)):
                    res = False
            elif currentState == 'decided':
                res = True
                if self._decisionsWereConfirmed():
                    res = False
                # Going back from "decided" to "published" is not a true "undo".
                # Indeed, when a meeting is "decided", all items for which no
                # decision was taken are set in "accepted". Going back to
                # "published" does not set them back in their previous state
                # ("published").
            elif currentState == 'closed':
                res = True
            elif currentState == 'archived':
                res = True
            else:
                res = True
        return res

    security.declarePublic('mayClose')
    def mayClose(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           self._decisionsAreTakenForEveryItem():
            res = True
        return res

    security.declarePublic('mayArchive')
    def mayArchive(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           self._decisionsAreArchivable():
            res = True
        return res

    security.declarePublic('mayRepublish')
    def mayRepublish(self):
        res = False
        if checkPermission(ReviewPortalContent, self.context) and \
           (not self.context.getDate().isFuture()):
            res = True
        return res

    security.declarePublic('mayChangeItemsOrder')
    def mayChangeItemsOrder(self):
        res = False
        if checkPermission(ModifyPortalContent, self.context) and \
           self.context.queryState() in ('created', 'published', 'frozen', \
                                         'decided'):
            res = True
        return res

    security.declarePublic('mayDelete')
    def mayDelete(self):
        res = False
        user = self.context.portal_membership.getAuthenticatedMember()
        if user.has_role('Manager') or not self.context.getRawItems():
            res = True
        return res

InitializeClass(MeetingWorkflowConditions)

class MeetingWorkflowActions:
    '''Adapts a meeting to interface IMeetingWorkflowActions.'''
    implements(IMeetingWorkflowActions)
    security = ClassSecurityInfo()

    def __init__(self, meeting):
        self.context = meeting

    security.declarePrivate('doPublish')
    def doPublish(self, stateChange):
        '''When publishing the meeting, I must set automatically all items
           to "published", too.'''
        for item in self.context.getItemsInOrder():
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itempublish')
        # When a meeting is published, we attribute him a sequence number
        # (within the meeting config)
        if self.context.getMeetingNumber() == -1:
            tool = self.context.portal_plonemeeting
            meetingConfig = tool.getMeetingConfig(self.context)
            meetingNumber = meetingConfig.getLastMeetingNumber()+1
            self.context.setMeetingNumber(meetingNumber)
            meetingConfig.setLastMeetingNumber(meetingNumber)

    security.declarePrivate('doFreeze')
    def doFreeze(self, stateChange):
        '''When freezing the meeting, I must set automatically all items
           to "itemfrozen", too.'''
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() == 'presented':
                self.context.portal_workflow.doActionFor(item, 'itempublish')
            if item.queryState() == 'itempublished':
                self.context.portal_workflow.doActionFor(item, 'itemfreeze')

    security.declarePrivate('doDecide')
    def doDecide(self, stateChange):
        # All items for which a decision was not taken yet are automatically
        # set to "accepted".
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() == 'itemfrozen':
                self.context.portal_workflow.doActionFor(item, 'accept')

    security.declarePrivate('doClose')
    def doClose(self, stateChange):
        # All items in state "accepted" (that were thus not confirmed yet)
        # are automatically set to "confirmed".
        for item in self.context.getAllItems(ordered=True):
            if item.queryState() == 'accepted':
                self.context.portal_workflow.doActionFor(item, 'confirm')
        # For this meeting, what is the number of the first item ?
        meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(
            self.context)
        self.context.setFirstItemNumber(meetingConfig.getLastItemNumber()+1)
        # Update the item counter which is global to the meeting config
        meetingConfig.setLastItemNumber(meetingConfig.getLastItemNumber() +\
                                        len(self.context.getItems()) + \
                                        len(self.context.getLateItems()))

    security.declarePrivate('doArchive')
    def doArchive(self, stateChange):
        tool = self.context.portal_plonemeeting
        # All items must go to 'itemarchived' state.
        for item in self.context.getAllItems(ordered=True):
            self.context.portal_workflow.doActionFor(item, 'itemarchive')
        for extApp in tool.objectValues('ExternalApplication'):
            extApp.notifyExternalApplication(self.context)

    security.declarePrivate('doRepublish')
    def doRepublish(self, stateChange):
        pass

    security.declarePrivate('doBackToFrozen')
    def doBackToFrozen(self, stateChange):
        pass

    security.declarePrivate('doBackToDecided')
    def doBackToDecided(self, stateChange):
        # Oups when closing a meeting we have updated the item counter (which
        # is global to the meeting config). So here we must reverse our action.
        meetingConfig = self.context.portal_plonemeeting.getMeetingConfig(
            self.context)
        meetingConfig.setLastItemNumber(meetingConfig.getLastItemNumber() -\
                                        len(self.context.getItems()) - \
                                        len(self.context.getLateItems()))
        self.context.setFirstItemNumber(-1)

    security.declarePrivate('doBackToCreated')
    def doBackToCreated(self, stateChange):
        for item in self.context.getItems():
            # I do it only for "normal" items (not for "late" items)
            # because we can't put a meeting back in "created" state if it
            # contains "late" items (so here there will be no "late" items
            # for this meeting). If we want to do it, we will need to
            # unpresent each "late" item first.
            if item.queryState() == 'itempublished':
                self.context.portal_workflow.doActionFor(item,'backToPresented')

    security.declarePrivate('doBackToPublished')
    def doBackToPublished(self, stateChange):
        do = self.context.portal_workflow.doActionFor
        for item in self.context.getItems():
            if item.queryState() == 'itemfrozen':
                do(item, 'backToItemPublished')
        for item in self.context.getLateItems():
            if item.queryState() == 'itemfrozen':
                do(item, 'backToItemPublished')
                do(item, 'backToPresented') # This way we "hide" again all late
                # items

    security.declarePrivate('doBackToClosed')
    def doBackToClosed(self, stateChange):
        # Every item must go back to its previous state: confirmed, delayed or
        # refused.
        wfTool = self.context.portal_workflow
        for item in self.context.getAllItems(ordered=True):
            itemHistory = item.workflow_history['meetingitem_workflow']
            previousState = itemHistory[-2]['review_state']
            previousState = previousState[0].upper() + previousState[1:]
            wfTool.doActionFor(item, 'backTo' + previousState)

InitializeClass(MeetingWorkflowActions)

# Validators -------------------------------------------------------------------
class MeetingDateValidator:
    '''Checks that the meeting date is correct, and that no other meeting has
       the same date and hour.'''
    __implements__ = (IValidator, )
    def __init__(self, name):
        self.name = name
    def __call__(self, value, *args, **kwargs):
        # Check that the date was filled in
        dateSep = '-'
        if value.find('/') != -1:
            dateSep = '/'
        if value.find(':') == -1:
            return 'no_meeting_hour'
        theDate = value.split(' ')[0].split(dateSep)
        for dateElem in theDate:
            if int(dateElem) == 0:
                return 'bad_meeting_date'
        # Check that no other meeting has the same date and hour
        meeting = kwargs['instance']
        meetingConfig = meeting.portal_plonemeeting.getMeetingConfig(meeting)
        otherMeetings = meeting.portal_catalog(
            portal_type=meetingConfig.getMeetingTypeName(),
            getDate=DateTime(value))
        if otherMeetings:
            for m in otherMeetings:
                if m.getObject() != meeting:
                    return 'meeting_with_same_date_exists'
        return True

validation.register(MeetingDateValidator('meetingDateValidator'))

class AllItemsParserError(Exception):
    '''Raised when the AllItemsParser encounters a problem.'''

class AllItemsParser:
    '''Parses the 'allItemsAtOnce' field.'''
    def __init__(self, fieldContent, meeting):
#        doc = minidom.parseString("<x>%s</x>" % fieldContent, parser=newparser)
        newContent = replaceHtmlEntities(fieldContent)
        doc = minidom.parseString("<x>%s</x>" % newContent)
        self.root = doc.firstChild
        # We remove empty nodes added by Firefox
        self.removeSpaceTextNodes()
        self.meeting = meeting
        # Some parser error messages
        self.CORRUPTED_BODY = meeting.utranslate('corruptedBody',
                                                 domain='PloneMeeting')
        self.CORRUPTED_TITLE = meeting.utranslate('corruptedTitle',
                                                  domain='PloneMeeting')
    def removeSpaceTextNodes(self):
        '''Removes emtpy nodes added by Firefox'''
        # Position on the first node
        child = self.root.firstChild
        while child:
            # We save the next node
            next = child.nextSibling
            if child.nodeType == child.TEXT_NODE:
                # Is is an empty node ?
                if child.toxml().isspace():
                    # Remove it
                    child.parentNode.removeChild(child)
            # Go to the next child
            child = next

    def parse(self, onItem=None):
        '''Parses (DOM parsing) the XHTML content of a Kupu field. Raises
           AllItemsParserError exceptions if parsing fails. Each time an item
           is parsed, a method p_onItem (if given) is called with args:
           itemNumber, itemTitle, itemBody.'''
        itemNumbers = []
        child = self.root.firstChild
        while child:
            # Parse the item's number and title
            if (child.nodeType == child.TEXT_NODE) or \
               (not child.hasAttribute('id')) or \
               (child.attributes['id'].value != 'itemTitle'):
                raise AllItemsParserError(self.CORRUPTED_BODY)
            if (not child.firstChild) or \
               (child.firstChild.nodeType <> child.TEXT_NODE):
                raise AllItemsParserError(self.CORRUPTED_TITLE)
            # Field must have the form "<number>. <title>"
            numberedTitle = child.firstChild.data
            # Parse number
            number = None
            dotIndex = numberedTitle.find('.')
            if dotIndex == -1:
                raise AllItemsParserError(self.CORRUPTED_TITLE)
            try:
                number = int(numberedTitle[:dotIndex])
                itemNumbers.append(number)
            except ValueError:
                raise AllItemsParserError(self.CORRUPTED_TITLE)
            # Parse title
            title = numberedTitle[dotIndex+1:].strip()
            if not title:
                raise AllItemsParserError(self.CORRUPTED_TITLE)
            # Parse body (description or decision)
            child = child.nextSibling
            if (not child) or (child.nodeType == child.TEXT_NODE) or \
               (not child.hasAttribute('id')) or \
               (child.attributes['id'].value != 'itemBody'):
                raise AllItemsParserError(self.CORRUPTED_BODY)
            body = ''
            bodyChild = child.firstChild
            while bodyChild:
                body += bodyChild.toxml().strip()
                bodyChild = bodyChild.nextSibling
            if self.meeting.adapted().isDecided() and kupuFieldIsEmpty(body):
                raise AllItemsParserError(self.meeting.utranslate(
                    'corruptedContent', domain='PloneMeeting'))
            child = child.nextSibling
            # Call callback method if defined.
            if onItem:
                onItem(number, title, body)
        nbOfItems = len(self.meeting.getRawItems()) + \
                    len(self.meeting.getRawLateItems())
        if set(itemNumbers) != set(range(1, nbOfItems+1)):
            raise AllItemsParserError(
                self.meeting.utranslate(
                    'corruptedNumbers', domain='PloneMeeting'))

class AllItemsValidator:
    '''Checks that the 'allItemsAtOnce' Kupu field is correct.

       The 'allItemsAtOnce' field is a temporary buffer (Kupu field) that
       contains numbers, titles and descriptions (or decisions) of all the items
       of a meeting. This allows a MeetingManager to modify all those things
       at once.

       This validator ensures that the user does not break things like the
       structure of each item, the numbering scheme, etc.'''
    __implements__ = (IValidator, )

    def __init__(self, name):
        self.name =name

    def __call__(self, value, *args, **kwargs):
        try:
            AllItemsParser(value, kwargs['instance']).parse()
            return True
        except AllItemsParserError, aipe:
            return aipe.args[0]

validation.register(AllItemsValidator('checkAllItemsAtOnce'))
##/code-section module-header

schema = Schema((

    StringField(
        name='title',
        widget=StringWidget(
            visible=False,
            label='Title',
            label_msgid='PloneMeeting_label_title',
            i18n_domain='PloneMeeting',
        ),
        accessor="Title"
    ),

    DateTimeField(
        name='date',
        index="FieldIndex",
        widget=CalendarWidget(
            label='Date',
            label_msgid='PloneMeeting_label_date',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        validators=('meetingDateValidator',)
    ),

    DateTimeField(
        name='startDate',
        widget=CalendarWidget(
            condition="python: here.attributeIsUsed('startDate')",
            label='Startdate',
            label_msgid='PloneMeeting_label_startDate',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        validators=('meetingDateValidator',)
    ),

    DateTimeField(
        name='endDate',
        widget=CalendarWidget(
            condition="python: here.attributeIsUsed('endDate')",
            label='Enddate',
            label_msgid='PloneMeeting_label_endDate',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        validators=('meetingDateValidator',)
    ),

    TextField(
        name='assembly',
        widget=TextAreaWidget(
            condition="python: here.attributeIsUsed('assembly')",
            label='Assembly',
            label_msgid='PloneMeeting_label_assembly',
            i18n_domain='PloneMeeting',
        ),
        default_output_type="text/html",
        optional=True,
        default_method="getDefaultAssembly"
    ),

    LinesField(
        name='attendees',
        widget=MultiSelectionWidget(
            condition="python: here.attributeIsUsed('attendees')",
            format="checkbox",
            label='Attendees',
            label_msgid='PloneMeeting_label_attendees',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        multiValued=1,
        vocabulary='listAssemblyMembers',
        default_method="getDefaultAttendees"
    ),

    LinesField(
        name='absents',
        widget=MultiSelectionWidget(
            condition="python: here.attributeIsUsed('absents')",
            format="checkbox",
            label='Absents',
            label_msgid='PloneMeeting_label_absents',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        multiValued=1,
        vocabulary='listAssemblyMembers'
    ),

    LinesField(
        name='excused',
        widget=MultiSelectionWidget(
            condition="python: here.attributeIsUsed('excused')",
            format="checkbox",
            label='Excused',
            label_msgid='PloneMeeting_label_excused',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        multiValued=1,
        vocabulary='listAssemblyMembers'
    ),

    StringField(
        name='place',
        widget=StringWidget(
            condition="python: here.attributeIsUsed('place')",
            label='Place',
            label_msgid='PloneMeeting_label_place',
            i18n_domain='PloneMeeting',
        ),
        optional=True,
        searchable=True
    ),

    TextField(
        name='observations',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            condition="python: here.attributeIsUsed('observations')",
            label_msgid="PloneMeeting_meetingObservations",
            label='Observations',
            i18n_domain='PloneMeeting',
        ),
        default_content_type="text/html",
        searchable=True,
        default_output_type="text/html",
        optional=True
    ),

    ReferenceField(
        name='items',
        widget=ReferenceField._properties['widget'](
            visible=False,
            label='Items',
            label_msgid='PloneMeeting_label_items',
            i18n_domain='PloneMeeting',
        ),
        allowed_types="('MeetingItem',)",
        multiValued=True,
        relationship="MeetingItems"
    ),

    ReferenceField(
        name='lateItems',
        widget=ReferenceField._properties['widget'](
            visible=False,
            label='Lateitems',
            label_msgid='PloneMeeting_label_lateItems',
            i18n_domain='PloneMeeting',
        ),
        allowed_types="('MeetingItem',)",
        multiValued=True,
        relationship="MeetingLateItems"
    ),

    TextField(
        name='allItemsAtOnce',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            condition="python: here.showAllItemsAtOnce()",
            parastyles=[["h2|itemTitle","Title"],["div|itemBody","Body"]],
            description_msgid="all_items_explanation",
            description="AllItemsAtOnce",
            label='Allitemsatonce',
            label_msgid='PloneMeeting_label_allItemsAtOnce',
            i18n_domain='PloneMeeting',
        ),
        default_content_type="text/html",
        validators=('checkAllItemsAtOnce',),
        default_output_type="text/html",
        edit_accessor="getAllItemsAtOnce"
    ),

    IntegerField(
        name='meetingNumber',
        default=-1,
        widget=IntegerField._properties['widget'](
            label='Meetingnumber',
            label_msgid='PloneMeeting_label_meetingNumber',
            i18n_domain='PloneMeeting',
        ),
        schemata="metadata"
    ),

    IntegerField(
        name='firstItemNumber',
        default=-1,
        widget=IntegerField._properties['widget'](
            label='Firstitemnumber',
            label_msgid='PloneMeeting_label_firstItemNumber',
            i18n_domain='PloneMeeting',
        ),
        schemata="metadata"
    ),

    StringField(
        name='meetingConfigVersion',
        widget=StringWidget(
            label='Meetingconfigversion',
            label_msgid='PloneMeeting_label_meetingConfigVersion',
            i18n_domain='PloneMeeting',
        ),
        schemata="metadata"
    ),

    TextField(
        name='signatures',
        widget=TextAreaWidget(
            label='Signatures',
            label_msgid='PloneMeeting_label_signatures',
            i18n_domain='PloneMeeting',
        ),
        schemata="metadata"
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

Meeting_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
# Integrate potential extensions from PloneMeeting sub-products
from Products.PloneMeeting.model.extender import ModelExtender
Meeting_schema = ModelExtender(Meeting_schema, 'meeting').run()
# Register the marshaller for DAV/XML export.
Meeting_schema.registerLayer('marshall', MeetingMarshaller())
##/code-section after-schema

class Meeting(BaseContent):
    """ A meeting made of items """
    security = ClassSecurityInfo()
    __implements__ = (getattr(BaseContent,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'Meeting'

    meta_type = 'Meeting'
    portal_type = 'Meeting'
    allowed_content_types = []
    filter_content_types = 0
    global_allow = 1
    content_icon = 'meeting.gif'
    immediate_view = 'meeting_view'
    default_view = 'meeting_view'
    suppl_views = ()
    typeDescription = "Meeting"
    typeDescMsgId = 'description_edit_meeting'


    actions =  (


       {'action': "string:$object_url/base_metadata",
        'category': "object",
        'id': 'metadata',
        'name': 'Properties',
        'permissions': ("Manage portal",),
        'condition': 'python:1'
       },


       {'action': "string:${object_url}/meeting_view",
        'category': "object",
        'id': 'view',
        'name': 'View',
        'permissions': ("View",),
        'condition': 'python:not here.portal_factory.isTemporary(here)'
       },


       {'action': "string:javascript:toggleMeetingDescriptions();",
        'category': "document_actions",
        'id': 'toggleDescriptions',
        'name': 'show_or_hide_details',
        'permissions': ("View",),
        'condition': 'python:("meeting_view" in here.REQUEST.get("ACTUAL_URL")) or (object_url == here.REQUEST.get("ACTUAL_URL"))'
       },


    )

    _at_rename_after_creation = True

    schema = Meeting_schema

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePublic('listAssemblyMembers')
    def listAssemblyMembers(self):
        '''Returns the active MeetingUsers having usage "assemblyMember".'''
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        res = ((u.id, u.Title()) for u in meetingConfig.getActiveMeetingUsers())
        return DisplayList(res)

    security.declarePublic('getDefaultAttendees')
    def getDefaultAttendees(self):
        '''The default attendees are the active MeetingUsers in the
           corresponding meeting configuration.'''
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        return [u.id for u in meetingConfig.getActiveMeetingUsers()]

    security.declarePublic('getAttendees')
    def getAttendees(self, theObjects=False, includeDeleted=True):
        '''Returns the attendees in this meeting. When used by Archetypes,
           this method returns a list of attendee ids; when used elsewhere in
           the PloneMeeting code (with p_theObjects=True), it returns
           a list of true MeetingUser objects. If p_includeDeleted is True,
           it includes a DummyMeetingUser instance for every MeetingUser that
           has been deleted (works only when p_theObjects is True).'''
        res = self.getField('attendees').get(self)
        if theObjects:
            meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
            mUsersFolder = getattr(meetingConfig, TOOL_FOLDER_MEETING_USERS)
            newRes = []
            for id in res:
                mUser = getattr(mUsersFolder, id, DummyMeetingUser(id))
                if isinstance(mUser, DummyMeetingUser):
                    if includeDeleted: newRes.append(mUser)
                else:
                    newRes.append(mUser)
            res = newRes
        return res

    security.declarePublic('getAbsents')
    def getAbsents(self, theObjects=False):
        '''See docstring in previous method.'''
        res = self.getField('absents').get(self)
        if theObjects:
            meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
            mUsersFolder = getattr(meetingConfig, TOOL_FOLDER_MEETING_USERS)
            res= [getattr(mUsersFolder, id, DummyMeetingUser(id)) for id in res]
        return res

    def getExcused(self, theObjects=False):
        '''See docstring in previous method.'''
        res = self.getField('excused').get(self)
        if theObjects:
            meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
            mUsersFolder = getattr(meetingConfig, TOOL_FOLDER_MEETING_USERS)
            res= [getattr(mUsersFolder, id, DummyMeetingUser(id)) for id in res]
        return res

    security.declarePublic('getAllItems')
    def getAllItems(self, uids=[], ordered=False):
        '''Gets all items presented to this meeting ("normal" and "late" items)
           If p_uids is not empty, only items whose uids are in it are returned
           (it will work only when returning an ordered list).'''
        if not ordered:
            res = self.getItems() + self.getLateItems()
        else:
            res = self.getItemsInOrder(uids=uids) + \
                  self.getItemsInOrder(late=True, uids=uids)
        return res

    security.declarePublic('getItemsInOrder')
    def getItemsInOrder(self, late=False, uids=[],
                        batchSize=None, startNumber=1):
        '''Get items in order. If p_late is True, gets the "late" items, and
           not the "normal" items. If p_uids is not empty, only items whose
           uids are in it are returned. If p_batchSize is not None, this method
           will return maximum p_batchSize items, starting at number
           p_startNumber.'''
        itemsGetter = self.getItems
        if late:
            itemsGetter = self.getLateItems
        items = itemsGetter()
        res = [None] * len(items)
        for item in items:
            res[item.getItemNumber()-1] = item
        if uids:
            user = self.portal_membership.getAuthenticatedMember()
            # Keep only items whose uid is in p_uids, and ensure the current
            # user has the right to view them (uids filtering is used within POD
            # templates)
            res = [item for item in res if (item.UID() in uids) and \
                                           user.has_permission('View', item)]
        if batchSize and (len(res)>batchSize):
            if startNumber > len(res): startNumber = 1
            endNumber = startNumber + batchSize - 1
            newRes = []
            for item in res:
                itemNb = item.getItemNumber()
                if (itemNb >= startNumber) and (itemNb <= endNumber):
                    newRes.append(item)
            res = newRes
        return res

    security.declarePublic('getJsItemUids')
    def getJsItemUids(self):
        '''Returns Javascript code for initializing a Javascript variable with
           all item UIDs.'''
        res = ''
        for uid in self.getRawItems():
            res += 'itemUids["%s"] = true;\n' % uid
        for uid in self.getRawLateItems():
            res += 'itemUids["%s"] = true;\n' % uid
        return res

    security.declarePublic('getItemByNumber')
    def getItemByNumber(self, number):
        '''Gets the item thas has number p_number.'''
        # It is a "normal" or "late" item ?
        itemsGetter = self.getItems
        itemNumber = number
        if number > len(self.getRawItems()):
            itemsGetter = self.getLateItems
            itemNumber -= len(self.getRawItems())
        # Find the item.
        res = None
        for item in itemsGetter():
            if item.getItemNumber() == itemNumber:
                res = item
                break
        return res

    security.declareProtected("Modify portal content", 'insertItem')
    def insertItem(self, item):
        '''Inserts p_item into my list of "normal" items or my list of "late"
           items.'''
        # First, determine if we must insert the item into the "normal"
        # list of items or to the list of "late" items. Note that I get
        # the list of items *in order* in the case I need to insert the item
        # at another place than at the end.
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        if item.wfConditions().isLateFor(self):
            items = self.getItemsInOrder(late=True)
            itemsSetter = self.setLateItems
            toDiscussValue = meetingConfig.getToDiscussLateDefault()
        else:
            items = self.getItemsInOrder(late=False)
            itemsSetter = self.setItems
            toDiscussValue = meetingConfig.getToDiscussDefault()
        # Set the correct value for the 'toDiscuss' field
        item.setToDiscuss(toDiscussValue)
        # At what place must we insert the item in the list ?
        insertMethod = meetingConfig.getSortingMethodOnAddItem()
        insertAtTheEnd = False
        if insertMethod != 'at_the_end':
            # We must insert it according to category or proposing group order
            # (at the end of the items belonging to the same category or
            # proposing group). We will insert the p_item just before the first
            # item whose category/group immediately follows p_item's category/
            # group (or at the end if inexistent). Note that the MeetingManager,
            # in subsequent manipulations, may completely change items order.
            itemOrder = item.adapted().getInsertOrder(insertMethod)
            higherItemFound = False
            insertIndex = 0 # That's where I will insert the item
            for anItem in items:
                if higherItemFound:
                    # Ok I already know where to insert the item. I just
                    # continue to visit the items in order to increment their
                    # number.
                    anItem.setItemNumber(anItem.getItemNumber()+1)
                elif anItem.adapted().getInsertOrder(insertMethod) > itemOrder:
                    higherItemFound = True
                    insertIndex = anItem.getItemNumber()-1
                    anItem.setItemNumber(anItem.getItemNumber()+1)
            if higherItemFound:
                items.insert(insertIndex, item)
                item.setItemNumber(insertIndex+1)
            else:
                insertAtTheEnd = True
        if (insertMethod == 'at_the_end') or insertAtTheEnd:
            # Add the item at the end of the items list
            items.append(item)
            item.setItemNumber(len(items))
        itemsSetter(items)

    security.declareProtected("Modify portal content", 'removeItem')
    def removeItem(self, item):
        '''Removes p_item from me.'''
        itemsGetter = self.getItems
        itemsSetter = self.setItems
        items = itemsGetter()
        if item not in items:
            itemsGetter = self.getLateItems
            itemsSetter = self.setLateItems
            items = itemsGetter()
        items.remove(item)
        itemsSetter(items)
        # Update item numbers
        for anItem in itemsGetter():
            if anItem.getItemNumber() > item.getItemNumber():
                anItem.setItemNumber(anItem.getItemNumber()-1)

    security.declarePublic('getAvailableItems')
    def getAvailableItems(self):
        '''Check docstring in IMeeting.'''
        meeting = self.getSelf()
        meetingConfig = meeting.portal_plonemeeting.getMeetingConfig(meeting)
        # First, get meetings accepting items for which the date is lower or
        # equal to the date of this meeting (self)
        meetings = meeting.portal_catalog(
            portal_type=meetingConfig.getMeetingTypeName(),
            review_state=('created', 'published', 'frozen', 'decided'),
            getDate={'query': meeting.getDate(), 'range': 'max'},
            )
        meetingUids = [b.getObject().UID() for b in meetings]
        meetingUids.append(ITEM_NO_PREFERRED_MEETING_VALUE)
        # Then, get the items whose preferred meeting is None or is among
        # those meetings.
        itemsUids = meeting.portal_catalog(
            portal_type=meetingConfig.getItemTypeName(),
            review_state='validated',
            getPreferredMeeting=meetingUids,
            sort_on="modified")
        if meeting.queryState() in ('published', 'frozen', 'decided'):
            # Oups. I can only take items which are "late" items.
            res = []
            for uid in itemsUids:
                if uid.getObject().wfConditions().isLateFor(meeting):
                    res.append(uid)
        else:
            res = itemsUids
        return res

    security.declarePublic('getDisplayableName')
    def getDisplayableName(self, short=False, withHour=True, likeTitle=False):
        '''Check doc in interfaces.py.'''
        meeting = self.getSelf()
        if likeTitle:
            res = meeting.Title()
        else:
            if withHour:
                hour = ' (%H:%M)'
            else:
                hour = ''
            if short:
                res = meeting.getDate().strftime('%d/%m/%Y' + hour)
            else:
                res = meeting.portal_plonemeeting.getFormattedDate(
                    meeting.getDate()) + meeting.getDate().strftime(hour)
        return res

    security.declarePrivate('getDefaultAssembly')
    def getDefaultAssembly(self):
        return self.portal_plonemeeting.getMeetingConfig(self).getAssembly()

    security.declarePrivate('updateTitle')
    def updateTitle(self):
        '''The meeting title is generated by this method, based on the meeting
           date.'''
        meetingOf = self.utranslate('meeting_of', domain='PloneMeeting')
        self.setTitle(meetingOf + ' ' + self.adapted().getDisplayableName())

    security.declarePublic('getItemsCount')
    def getItemsCount(self):
        '''Returns the amount of MeetingItems in a Meeting'''
        return len(self.getRawItems()) + len(self.getRawLateItems())

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self):
        '''Initializes the meeting title and inserts recurring items if
           relevant.'''
        self.updateTitle()
        meetingConfig = self.portal_plonemeeting.getMeetingConfig(self)
        self.setMeetingConfigVersion(meetingConfig.getConfigVersion())
        self.setSignatures(meetingConfig.getSignatures())
        addRecurringItemsIfRelevant(self, '_init_')
        # Make a readable title
        #self.setId(normalizeString(self.Title(), context=self))
        self.reindexObject()

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self):
        '''Updates the meeting title.'''
        self.updateTitle()
        self.reindexObject()

    security.declarePublic('wfConditions')
    def wfConditions(self):
        '''Returns the adapter that implements the interface that proposes
           methods for use as conditions in the workflow associated with this
           meeting.'''
        return getWorkflowAdapter(self, conditions=True)

    security.declarePublic('wfActions')
    def wfActions(self):
        '''Returns the adapter that implements the interface that proposes
           methods for use as actions in the workflow associated with this
           meeting.'''
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
        return (name in meetingConfig.getUsedMeetingAttributes())

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
        '''Similar to MeetingItem.getSelf. Check MeetingItem.py for more
           info.'''
        res = self
        if self.__class__.__name__ != 'Meeting':
            res = self.context
        return res

    security.declarePublic('isDecided')
    def isDecided(self):
        meeting = self.getSelf()
        return meeting.queryState() in ('decided', 'closed', 'archived')

    security.declarePublic('i18n')
    def i18n(self, msg, domain="PloneMeeting"):
        '''Shortcut for translating p_msg in domain PloneMeeting.'''
        return self.utranslate(msg, domain=domain)

    security.declarePublic('showAllItemsAtOnce')
    def showAllItemsAtOnce(self):
        '''Must I show the Kupu field that allows to edit all "normal" and
           "late" items at once ?'''
        # I must have 'write' permissions on every item in order to do this.
        if self.getItems():
            if self.adapted().isDecided():
                writePerms = (ModifyPortalContent, WriteDecision)
            else:
                writePerms = (ModifyPortalContent,)
            currentUser = self.portal_membership.getAuthenticatedMember()
            for item in self.getAllItems():
                for perm in writePerms:
                    if not currentUser.has_permission(perm, item):
                        return False
            return True
        else:
            return False

    security.declarePublic('getAllItemsAtOnce')
    def getAllItemsAtOnce(self):
        '''Creates the content of the "allItemsAtOnce" field from "normal" and
           "late" meeting items presented in this meeting.'''
        text = []
        itemNumber = 0
        for itemsList in (self.getItemsInOrder(),
                          self.getItemsInOrder(late=True)):
            for item in itemsList:
                itemNumber += 1
                text.append('<h2 id="itemTitle">%d. %s</h2>' % \
                            (itemNumber, item.Title()))
                text.append('<div id="itemBody">')
                if self.adapted().isDecided():
                    itemBody = item.getDecision()
                else:
                    itemBody = item.Description()
                if not itemBody:
                    itemBody = KUPU_EMPTY_VALUES[0]
                text.append(itemBody)
                text.append('</div>')
        text = "\n".join(text)
        self.getField('allItemsAtOnce').set(self, text)
        return text

    security.declarePublic('updateItem')
    def updateItem(self, itemNumber, itemTitle, itemBody):
        '''Updates the item having number p_itemNumber with new p_itemTitle and
           p_itemBody that come from the 'allItemsAtOnce' field.'''
        item = self.getItemByNumber(itemNumber)
        itemChanged = False
        if not kupuEquals(item.Title(), itemTitle):
            item.setTitle(itemTitle)
            itemChanged = True
        if self.adapted().isDecided():
            # I must update the decision.
            item.setDecision(itemBody)
        else:
            if not kupuEquals(item.Description(), itemBody):
                item.setDescription(itemBody)
                itemChanged = True
        if itemChanged:
            item.pm_modification_date = DateTime() # Now
            item.at_post_edit_script()
        if (not itemChanged) and self.adapted().isDecided():
            # In this case, I must not call at_post_edit_script (which will a.o.
            # remember access on this item) but I must still transform rich text
            # fields because the decison field was updated.
            item.transformAllRichTextFields()

    security.declarePublic('setAllItemsAtOnce')
    def setAllItemsAtOnce(self, value):
        '''p_value is the content of the 'allItemsAtOnce' field, with all items
           numbers, titles and descriptions/decisions in one Kupu field. This
           method updates all the corresponding MeetingItem objects.'''
        try:
            AllItemsParser(value, self).parse(onItem=self.updateItem)
        except AllItemsParserError, bpe:
            pass # Normally it should never happen because the validator parsed
                 # p_value some milliseconds earlier.
        # Re-initialise the "allItemsAtOnce" field to blank (the next time it
        # will be shown to the user, it will be updated at this moment).
        self.getField('allItemsAtOnce').set(self, '')

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

    security.declarePrivate('addRecurringItems')
    def addRecurringItems(self, recurringItems):
        '''Inserts into this meeting some p_recurringItems. The newly created
           items are copied from recurring items (contained in the meeting
           config) to the folder containing this meeting.'''
        if recurringItems:
            sourceFolder = recurringItems[0].getParentNode()
            copiedData = sourceFolder.manage_copyObjects(
                ids=[ri.id for ri in recurringItems])
            destFolder = self.getParentNode()
            # Paste the items in the Meeting folder
            pastedItems = self.portal_plonemeeting.pasteItems(
                destFolder, copiedData, copyAnnexes=True, copyAdvices=True)
            for newItem in pastedItems:
                # Put the new item in the correct state
                newItem.adapted().addRecurringItemToMeeting(self)
                newItem.reindexObject()

    security.declarePublic('observationsFieldIsEmpty')
    def observationsFieldIsEmpty(self):
        '''Is the 'decision' field empty ? '''
        return kupuFieldIsEmpty(self.getObservations())

    security.declarePublic('mustShowLateItems')
    def mustShowLateItems(self, itemStart, maxShownItems):
        '''When consulting a meeting, we need to display the late items if we
           are on the last page of the normal items and if there are late
           items. p_itemStart is the number of the first normal item currently
           displayed; p_maxShownItems is the maximum number of normal items
           shown at once.'''
        onLastPage = (itemStart + maxShownItems) > len(self.getRawItems())
        if onLastPage and (len(self.getRawLateItems()) > 0):
            return True
        else:
            return False

    security.declarePublic('numberOfItems')
    def numberOfItems(self, late=False):
        '''How much items in this meeting ?'''
        if late: return len(self.getRawLateItems())
        else: return len(self.getRawItems())

    security.declarePublic('getBatchStartNumber')
    def getBatchStartNumber(self, late=False):
        '''When displaying meeting_view, I need to now the start number of the
           normal and late items lists. If they are in the request, I take it
           from there, excepted if they are wrong (ie an item has been deleted
           or removed from a list and as a consequence the page I must show
           does not exist anymore.'''
        res = 1
        rq = self.REQUEST
        if late:
            reqKey = 'lStartNumber'
            nbOfItems = len(self.getRawLateItems())
        else:
            reqKey = 'iStartNumber'
            nbOfItems = len(self.getRawItems())
        if rq.has_key(reqKey) and (int(rq[reqKey]) <= nbOfItems):
            res = int(rq[reqKey])
        return res

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        '''This is a workaround to avoid a Plone design problem where it is
           possible to remove a folder containing objects you can not remove.'''
        # If we are here, everything has already been checked before.
        # Just check that the item is myself or a Plone Site.
        # We can remove an item directly but not "through" his container.
        if not item.meta_type in ['Plone Site', 'Meeting', ]:
            user = self.portal_membership.getAuthenticatedMember()
            logger.warn(BEFOREDELETE_ERROR % (user.getId(), self.id))
            raise BeforeDeleteException, "can_not_delete_meeting_container"
        BaseContent.manage_beforeDelete(self, item, container)

    security.declarePublic('showVotes')
    def showVotes(self):
        '''See doc in interfaces.py.'''
        res = False
        meeting = self.getSelf()
        meetingConfig = meeting.portal_plonemeeting.getMeetingConfig(meeting)
        if meetingConfig.getUseVotes():
            # The meeting must have started. But what date to take into account?
            now = DateTime()
            meetingStartDate = meeting.getDate()
            if meeting.attributeIsUsed('startDate') and meeting.getStartDate():
                meetingStartDate = meeting.getStartDate()
            if meetingStartDate < now:
                res = True
        return res



registerType(Meeting, PROJECTNAME)
# end of class Meeting

##code-section module-footer #fill in your manual code here
##/code-section module-footer



