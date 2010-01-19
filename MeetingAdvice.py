# -*- coding: utf-8 -*-
#
# File: MeetingAdvice.py
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
from zope.interface import implements
from Globals import InitializeClass
from Products.PloneMeeting.interfaces import IMeetingAdviceWorkflowConditions, \
                                             IMeetingAdviceWorkflowActions
from Products.PloneMeeting.utils import \
     getWorkflowAdapter, getCustomAdapter, kupuFieldIsEmpty, \
     checkPermission, HubSessionsMarshaller, sendMailIfRelevant
from Products.CMFCore.permissions import ReviewPortalContent, ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _

# Marshaller -------------------------------------------------------------------
class AdviceMarshaller(HubSessionsMarshaller):
    '''Allows to marshall an advice into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all_with_metadata'
    fieldsToExclude = ['allowDiscussion']
    rootElementName = 'advice'

    def marshallSpecificElements(self, advice, res):
        HubSessionsMarshaller.marshallSpecificElements(self, advice, res)
        self.dumpField(res, 'pm_modification_date', advice.pm_modification_date)

InitializeClass(AdviceMarshaller)

# Adapters ---------------------------------------------------------------------
class MeetingAdviceWorkflowConditions:
    '''Adapts a MeetingAdvice to interface IMeetingAdviceWorkflowConditions.'''
    implements(IMeetingAdviceWorkflowConditions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    # Implementation of methods from the interface I realize -------------------
    security.declarePublic('mayPublish')
    def mayPublish(self):
        res = False
        # We check if the current user has the Review portal content permission
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayClose')
    def mayClose(self):
        '''When a meeting is frozen, we will automatically close every
           advice.'''
        res = False
        if self.context.hasMeeting() and \
           (self.context.getMeeting().queryState() == "frozen"):
            res = True
        return res

    security.declarePublic('mayBackToCreated')
    def mayBackToCreated(self):
        res = False
        # We check if the current user has the Review portal content permission
        if checkPermission(ReviewPortalContent, self.context):
            res = True
        return res

    security.declarePublic('mayBackToPublished')
    def mayBackToPublished(self):
        '''Here, the user need the Manage portal permission. Indeed, this is
           not a normal case and only the Manager should be able to do that.'''
        res = False
        # We check if the current user has the Manage portal permission
        # or we check that the MeetingItem is in 'itempublished'.
        # In this case, we just put the item back to 'itempublished' and the
        # 'meetingItem.doCorrect' after_script will 'adviceBackToPublished'
        # every contained advice.
        if checkPermission(ManagePortal, self.context) or \
           (self.context.getMeetingItem().queryState() == 'itempublished'):
            res = True
        return res

InitializeClass(MeetingAdviceWorkflowConditions)

class MeetingAdviceWorkflowActions:
    '''Adapts a MeetingAdvice to interface IMeetingAdviceWorkflowActions.'''
    implements(IMeetingAdviceWorkflowActions)
    security = ClassSecurityInfo()

    def __init__(self, item):
        self.context = item

    # Implementation of methods from the interface I realize -------------------
    security.declarePrivate('doBackToCreated')
    def doBackToCreated(self, state_change):
        """
        """
        #need to update the adviceIndex where the review_state is stored...
        self.context.getMeetingItem().updateAdviceIndex(advice=self.context)


    security.declarePrivate('doBackToPublished')
    def doBackToPublished(self, state_change):
        """
        """
        #need to update the adviceIndex where the review_state is stored...
        self.context.getMeetingItem().updateAdviceIndex(advice=self.context)

    security.declarePrivate('doClose')
    def doClose(self, state_change):
        """
        """
        #need to update the adviceIndex where the review_state is stored...
        self.context.getMeetingItem().updateAdviceIndex(advice=self.context)

    security.declarePrivate('doPublish')
    def doPublish(self, state_change):
        """
        """
        #need to update the adviceIndex where the review_state is stored...
        self.context.getMeetingItem().updateAdviceIndex(advice=self.context)
        # Warn users Check if we must warn users
        sendMailIfRelevant(self.context, 'adviceAdded', 'View', isRole=False)

InitializeClass(MeetingAdviceWorkflowActions)

##/code-section module-header

schema = Schema((

    StringField(
        name='title',
        visible=False,
        widget=StringWidget(
            label='Title',
            label_msgid='PloneMeeting_label_title',
            i18n_domain='PloneMeeting',
        ),
        accessor="Title"
    ),

    StringField(
        name='agreementLevel',
        widget=SelectionWidget(
            description="AgreementLevel",
            description_msgid="agreement_level_descr",
            label='Agreementlevel',
            label_msgid='PloneMeeting_label_agreementLevel',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        vocabulary='listAgreementLevels',
        required=True
    ),

    TextField(
        name='description',
        allowable_content_types=('text/html',),
        widget=RichWidget(
            label="MeetingAdviceDescription",
            label_msgid="advice_description",
            description="Enter a relevant advice if necessary",
            description_msgid="advice_description_descr",
            i18n_domain='PloneMeeting',
        ),
        default_content_type="text/html",
        searchable=True,
        default_output_type="text/html",
        accessor="Description"
    ),

    StringField(
        name='adviserName',
        required=True,
        widget=SelectionWidget(
            description="Select the adviser name for which you will give an advice",
            description_msgid="adviser_name_desc",
            condition='python: here.showAdviserName()',
            label='Advisername',
            label_msgid='PloneMeeting_label_adviserName',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        vocabulary='listAdvisersNames',
        default_method='getDefaultAdviserName'
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingAdvice_schema = OrderedBaseFolderSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
# Integrate potential extensions from PloneMeeting sub-products
from Products.PloneMeeting.model.extender import ModelExtender
MeetingAdvice_schema = ModelExtender(MeetingAdvice_schema, 'advice').run()
MeetingAdvice_schema.moveField('agreementLevel', pos=2)
# Register the marshaller for DAV/XML export.
MeetingAdvice_schema.registerLayer('marshall', AdviceMarshaller())
##/code-section after-schema

class MeetingAdvice(OrderedBaseFolder):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(OrderedBaseFolder,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'MeetingAdvice'

    meta_type = 'MeetingAdvice'
    portal_type = 'MeetingAdvice'
    allowed_content_types = []
    filter_content_types = 1
    global_allow = 1
    #content_icon = 'MeetingAdvice.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "MeetingAdvice"
    typeDescMsgId = 'description_edit_meetingadvice'


    actions =  (


       {'action': "string:$object_url/base_metadata",
        'category': "object",
        'id': 'metadata',
        'name': 'Properties',
        'permissions': ("Manage portal",),
        'condition': 'python:1'
       },


       {'action': "string:${object_url}/meetingadvice_view",
        'category': "object",
        'id': 'view',
        'name': 'View',
        'permissions': ("View",),
        'condition': 'python:not here.portal_factory.isTemporary(here)'
       },


    )

    _at_rename_after_creation = True

    schema = MeetingAdvice_schema

    ##code-section class-header #fill in your manual code here
    __dav_marshall__ = True # MeetingAdvice is folderish so normally it can't be
    # marshalled through WebDAV.
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePublic('wfConditions')
    def wfConditions(self):
        '''Returns the adapter that implements the interface that proposes
           methods for use as conditions in the workflow associated with this
           advice.'''
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
           this methods returns me.'''
        return getCustomAdapter(self)

    security.declarePublic('queryState')
    def queryState(self):
        '''In what state am I ?'''
        return self.portal_workflow.getInfoFor(self, 'review_state')

    security.declarePublic('at_post_create_script')
    def at_post_create_script(self):
        '''After the advice creation, we perform some tasks:
            - define PloneMeeting-specific modification date,
            - remember actual user access (see coloration system),
            - update 'adviceIndex' property,
            - update advice security,
            - call sub-product-specific behaviour.'''
        self.pm_modification_date = self.modification_date
        self.portal_plonemeeting.rememberAccess(self.UID(), commitNeeded=False)
        self.getMeetingItem().updateAdviceIndex(advice=self)
        self.updateLocalRoles()
        self.adapted().onEdit(isCreated=True)

    security.declarePublic('at_post_edit_script')
    def at_post_edit_script(self):
        self.pm_modification_date = self.modification_date
        self.portal_plonemeeting.rememberAccess(self.UID(), commitNeeded=False)
        self.getMeetingItem().updateAdviceIndex(advice=self)
        self.updateLocalRoles()
        self.adapted().onEdit(isCreated=False)

    security.declarePrivate('updateLocalRoles')
    def updateLocalRoles(self):
        '''Since we inherit local roles from MeetingItem, we had to use the
           'MeetingAdviceEditor' role for advisers group on whose behalf the
           advice is registered ('adviserName' field).'''
        # First remove 'MeetingAdviceEditor' local role(s) previously set
        for principalId, localRoles in self.get_local_roles():
            self.manage_delLocalRoles([principalId])
            relevantLocalRoles = filter(
                lambda x:x!='MeetingAdviceEditor', localRoles)
            if relevantLocalRoles:
                self.manage_addLocalRoles(principalId, relevantLocalRoles)
        # Then add the 'MeetingAdviceEditor' local role corresponding to the
        # advisers group on whose behalf the advice is registered
        self.manage_addLocalRoles(
            self.getAdviserName(), ('MeetingAdviceEditor',))

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated):
        '''See doc in interfaces.py.'''
    security.declarePublic('listAgreementLevels')
    def listAgreementLevels(self):
        '''Returns a list containing the active agreementLevels.'''
        tool = self.portal_plonemeeting
        meetingConfig = tool.getMeetingConfig(self.aq_parent)
        res = []
        for agreementLevel in tool.getAdviceAgreementLevels(\
            meetingConfig, onStates=['active']):
            res.append((agreementLevel.getId(), agreementLevel.Title()))
        return DisplayList(tuple(res))

    security.declarePublic('listAdvisersNames')
    def listAdvisersNames(self):
        '''Returns a list containing the "adviser" groups in which the creator
           is.'''
        return self.getMeetingItem().listAdvisersForUser()

    security.declarePublic('getDefaultAdviserName')
    def getDefaultAdviserName(self):
        '''Returns id of the "adviser" group in which the creator is - if he's
           member of only one group, else returns None.'''
        res = None
        listAdvisers = self.listAdvisersNames()
        if (len(listAdvisers)==1):
            res = listAdvisers[0]
        return res

    security.declarePublic('showAdviserName')
    def showAdviserName(self):
        '''Check if we can show the adviserName field. We show it if the adviser
           is in more than one adviser group.'''
        # If we have more than one adviserName, the user is part of more than
        # one adviser group. We show him the choice box.
        # listAdvisersNames returns a DisplayList.
        if self.listAdvisersNames().index > 1: return True
        return False

    security.declarePublic('getAdviceInfo')
    def getAdviceInfo(self):
        '''Produces a dict with some useful info about this advice. This is
           used for indexing purposes (see method updateAdviceIndex in
           MeetingItem.py).'''
        agree_lev_id = self.getAgreementLevel()
        tool = self.portal_plonemeeting
        meetingConfig = tool.getMeetingConfig(self.aq_parent)
        agree_lev = tool.getAdviceAgreementLevelById(
            meetingConfig, agree_lev_id)
        adviser_title = tool.getMeetingGroup(self.getAdviserName()).Title()
        advice_title = adviser_title
        if self.Title().strip():
            advice_title += ' : '
            advice_title += self.Title()
        res = {'agLevel_id': agree_lev_id,
               'agLevel_Title': agree_lev.Title(),
               'agLevel_iconUrl': agree_lev.absolute_url_path() + '/theIcon',
               'adviser_id': self.getAdviserName(),
               'adviser_Title': adviser_title,
               'uid': self.UID(),
               'creator': self.Creator(),
               'Title': advice_title,
               'advice_Title': self.Title(),
               'url': self.absolute_url_path(),
               'description': self.Description(),
               'modification_date': self.pm_modification_date,
               'review_state': self.queryState()
              }
        return res

    security.declarePublic('descriptionFieldIsEmpty')
    def descriptionFieldIsEmpty(self):
        '''Is the 'description' field empty ? '''
        return kupuFieldIsEmpty(self.Description())

    security.declarePublic('getMeetingItem')
    def getMeetingItem(self):
        '''Return the MeetingItem container'''
        return self.aq_inner.aq_parent

    security.declarePublic('isPublished')
    def isPublished(self):
        '''Return if the advice is viewable by others (published or closed)'''
        return not self.portal_workflow.getInfoFor(self, 'review_state') == "advicecreated"



registerType(MeetingAdvice, PROJECTNAME)
# end of class MeetingAdvice

##code-section module-footer #fill in your manual code here
def onAddMeetingAdvice(advice, event):
    '''This method is called every time a MeetingAdvice is created, even in
       portal_factory. Local roles defined on an advice define who may view
       or edit it. But at the time the advice is created in portal_factory,
       local roles are not defined yet. So here we add a temporary local
       role to the currently logged user that allows him to create the
       advice. In advice.at_post_create_script we will remove this role, and
       assign it to the advisers group on whose behalf the advice is registered
       (designated by the 'adviserName' field).'''
    user = advice.portal_membership.getAuthenticatedMember()
    advice.manage_addLocalRoles(user.getId(), ('MeetingAdviceEditor',))
##/code-section module-footer



