# -*- coding: utf-8 -*-
#
# File: PloneMeeting.py
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


from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowTool import addWorkflowFactory
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.ExternalMethod.ExternalMethod import ExternalMethod
from Products.PloneMeeting.config import *

##code-section create-workflow-module-header #fill in your manual code here
from Products.CMFCore.permissions import View, AccessContentsInformation, \
     ModifyPortalContent, ReviewPortalContent, DeleteObjects, AddPortalContent
AddMeetingFile = ADD_CONTENT_PERMISSIONS['MeetingFile']
AddMeetingAdvice = ADD_CONTENT_PERMISSIONS['MeetingAdvice']
##/code-section create-workflow-module-header


productname = 'PloneMeeting'

def setupmeetingitem_workflow(self, workflow):
    """Define the meetingitem_workflow workflow.
    """
    # Add additional roles to portal
    portal = getToolByName(self,'portal_url').getPortalObject()
    data = list(portal.__ac_roles__)
    for role in ['MeetingMember', 'MeetingObserverLocalCopy', 'MeetingManager', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingAdviser', 'MeetingObserverUnpublished', 'MeetingArchiveObserver']:
        if not role in data:
            data.append(role)
            # add to portal_role_manager
            # first try to fetch it. if its not there, we probaly have no PAS 
            # or another way to deal with roles was configured.            
            try:
                prm = portal.acl_users.get('portal_role_manager', None)
                if prm is not None:
                    try:
                        prm.addRole(role, role, 
                                    "Added by product 'PloneMeeting'/workflow 'meetingitem_workflow'")
                    except KeyError: # role already exists
                        pass
            except AttributeError:
                pass
    portal.__ac_roles__ = tuple(data)

    workflow.setProperties(title='meetingitem_workflow')

    ##code-section create-workflow-setup-method-header #fill in your manual code here
    ##/code-section create-workflow-setup-method-header


    for s in ['itemcreated', 'proposed', 'delayed', 'validated', 'refused', 'accepted', 'itemfrozen', 'confirmed', 'presented', 'itempublished', 'itemarchived']:
        workflow.states.addState(s)

    for t in ['backToItemPublished', 'backToItemFrozen', 'refuse', 'backToProposed', 'confirm', 'propose', 'itemfreeze', 'backToRefused', 'accept', 'delay', 'backToConfirmed', 'backToAccepted', 'itemarchive', 'backToValidated', 'itempublish', 'backToItemCreated', 'validate', 'backToDelayed', 'present', 'backToPresented']:
        workflow.transitions.addTransition(t)

    for v in ['review_history', 'comments', 'time', 'actor', 'action']:
        workflow.variables.addVariable(v)

    workflow.addManagedPermission(View)
    workflow.addManagedPermission(AccessContentsInformation)
    workflow.addManagedPermission(ReviewPortalContent)
    workflow.addManagedPermission(ModifyPortalContent)
    workflow.addManagedPermission(DeleteObjects)
    workflow.addManagedPermission(AddAnnex)
    workflow.addManagedPermission(WriteDecision)
    workflow.addManagedPermission(ReadDecision)
    workflow.addManagedPermission(AddPortalContent)
    workflow.addManagedPermission(AddMeetingFile)
    workflow.addManagedPermission(AddMeetingAdvice)
    workflow.addManagedPermission('PloneMeeting: Read mandatory advisers')
    workflow.addManagedPermission('PloneMeeting: Write mandatory advisers')
    workflow.addManagedPermission('PloneMeeting: Read optional advisers')
    workflow.addManagedPermission('PloneMeeting: Write optional advisers')
    workflow.addManagedPermission('PloneMeeting: Write decision annex')
    workflow.addManagedPermission('PloneMeeting: Read decision annex')
    workflow.addManagedPermission('PloneMeeting: Read item observations')
    workflow.addManagedPermission('PloneMeeting: Write item observations')

    for l in []:
        if not l in workflow.worklists.objectValues():
            workflow.worklists.addWorklist(l)

    ## Initial State

    workflow.states.setInitialState('itemcreated')

    ## States initialization

    stateDef = workflow.states['itemcreated']
    stateDef.setProperties(title="""itemcreated""",
                           description="""""",
                           transitions=['propose'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingMember'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['proposed']
    stateDef.setProperties(title="""proposed""",
                           description="""""",
                           transitions=['backToItemCreated', 'validate'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingReviewer'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingReviewer'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingReviewer'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingReviewer'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['delayed']
    stateDef.setProperties(title="""delayed""",
                           description="""""",
                           transitions=['backToItemFrozen', 'itemarchive'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['validated']
    stateDef.setProperties(title="""validated""",
                           description="""""",
                           transitions=['backToProposed', 'present'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingMember', 'MeetingObserverUnpublished', 'MeetingAdviser', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingMember', 'MeetingObserverUnpublished', 'MeetingAdviser', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingManager', 'MeetingAdviser'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingAdviser'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['refused']
    stateDef.setProperties(title="""refused""",
                           description="""""",
                           transitions=['backToItemFrozen', 'itemarchive'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['accepted']
    stateDef.setProperties(title="""accepted""",
                           description="""""",
                           transitions=['backToItemFrozen', 'confirm'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['itemfrozen']
    stateDef.setProperties(title="""itemfrozen""",
                           description="""""",
                           transitions=['refuse', 'accept', 'delay', 'backToItemPublished'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['confirmed']
    stateDef.setProperties(title="""confirmed""",
                           description="""""",
                           transitions=['backToAccepted', 'itemarchive'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager'])

    stateDef = workflow.states['presented']
    stateDef.setProperties(title="""presented""",
                           description="""""",
                           transitions=['backToValidated', 'itempublish'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingMember', 'MeetingObserverUnpublished', 'MeetingAdviser', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingMember', 'MeetingObserverUnpublished', 'MeetingAdviser', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingManager', 'MeetingAdviser'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingAdviser'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['itempublished']
    stateDef.setProperties(title="""itempublished""",
                           description="""""",
                           transitions=['itemfreeze', 'backToPresented'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingAdviser', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingAdviser', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingAdviser'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingAdviser'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['itemarchived']
    stateDef.setProperties(title="""itemarchived""",
                           description="""""",
                           transitions=['backToRefused', 'backToConfirmed', 'backToDelayed'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingArchiveObserver', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingArchiveObserver', 'MeetingObserverLocalCopy'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager'])
    stateDef.setPermission(AddAnnex,
                           0,
                           ['Manager'])
    stateDef.setPermission(WriteDecision,
                           0,
                           ['Manager'])
    stateDef.setPermission(ReadDecision,
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingArchiveObserver'])
    stateDef.setPermission(AddPortalContent,
                           0,
                           ['Manager'])
    stateDef.setPermission(AddMeetingFile,
                           0,
                           ['Manager'])
    stateDef.setPermission(AddMeetingAdvice,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission('PloneMeeting: Read mandatory advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write mandatory advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read optional advisers',
                           0,
                           ['Manager', 'MeetingMember', 'MeetingReviewer', 'MeetingObserverLocal', 'MeetingAdviser', 'MeetingObserverGlobal'])
    stateDef.setPermission('PloneMeeting: Write optional advisers',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read decision annex',
                           0,
                           ['Manager', 'MeetingReviewer', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverGlobal', 'MeetingMember', 'MeetingArchiveObserver'])
    stateDef.setPermission('PloneMeeting: Write decision annex',
                           0,
                           ['Manager'])
    stateDef.setPermission('PloneMeeting: Read item observations',
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal', 'MeetingArchiveObserver'])
    stateDef.setPermission('PloneMeeting: Write item observations',
                           0,
                           ['Manager'])

    ## Transitions initialization

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToItemPublished']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToItemPublished']
    transitionDef.setProperties(title="""backToItemPublished""",
                                new_state_id="""itempublished""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToItemPublished""",
                                actbox_name="""backToItemPublished""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToItemFrozen']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToItemFrozen']
    transitionDef.setProperties(title="""backToItemFrozen""",
                                new_state_id="""itemfrozen""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToItemFrozen""",
                                actbox_name="""backToItemFrozen""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doRefuse']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['refuse']
    transitionDef.setProperties(title="""refuse""",
                                new_state_id="""refused""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doRefuse""",
                                actbox_name="""refuse""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayDecide()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToPropose']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToProposed']
    transitionDef.setProperties(title="""backToProposed""",
                                new_state_id="""proposed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToPropose""",
                                actbox_name="""backToProposed""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doConfirm']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['confirm']
    transitionDef.setProperties(title="""confirm""",
                                new_state_id="""confirmed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doConfirm""",
                                actbox_name="""confirm""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayConfirm()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doPropose']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['propose']
    transitionDef.setProperties(title="""propose""",
                                new_state_id="""proposed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doPropose""",
                                actbox_name="""propose""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayPropose()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doItemFreeze']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['itemfreeze']
    transitionDef.setProperties(title="""itemfreeze""",
                                new_state_id="""itemfrozen""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doItemFreeze""",
                                actbox_name="""itemfreeze""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayFreeze()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToRefused']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToRefused']
    transitionDef.setProperties(title="""backToRefused""",
                                new_state_id="""refused""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToRefused""",
                                actbox_name="""backToRefused""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doAccept']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['accept']
    transitionDef.setProperties(title="""accept""",
                                new_state_id="""accepted""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doAccept""",
                                actbox_name="""accept""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayDecide()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doDelay']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['delay']
    transitionDef.setProperties(title="""delay""",
                                new_state_id="""delayed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doDelay""",
                                actbox_name="""delay""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayDelay()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToConfirmed']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToConfirmed']
    transitionDef.setProperties(title="""backToConfirmed""",
                                new_state_id="""confirmed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToConfirmed""",
                                actbox_name="""backToConfirmed""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToAccepted']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToAccepted']
    transitionDef.setProperties(title="""backToAccepted""",
                                new_state_id="""accepted""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToAccepted""",
                                actbox_name="""backToAccepted""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doItemArchive']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['itemarchive']
    transitionDef.setProperties(title="""itemarchive""",
                                new_state_id="""itemarchived""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doItemArchive""",
                                actbox_name="""itemarchive""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayArchive()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToValidated']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToValidated']
    transitionDef.setProperties(title="""backToValidated""",
                                new_state_id="""validated""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToValidated""",
                                actbox_name="""backToValidated""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doItemPublish']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['itempublish']
    transitionDef.setProperties(title="""itempublish""",
                                new_state_id="""itempublished""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doItemPublish""",
                                actbox_name="""itempublish""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayPublish()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToItemCreated']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToItemCreated']
    transitionDef.setProperties(title="""backToItemCreated""",
                                new_state_id="""itemcreated""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToItemCreated""",
                                actbox_name="""backToItemCreated""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doValidate']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['validate']
    transitionDef.setProperties(title="""validate""",
                                new_state_id="""validated""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doValidate""",
                                actbox_name="""validate""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayValidate()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToDelayed']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToDelayed']
    transitionDef.setProperties(title="""backToDelayed""",
                                new_state_id="""delayed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToDelayed""",
                                actbox_name="""backToDelayed""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doPresent']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['present']
    transitionDef.setProperties(title="""present""",
                                new_state_id="""presented""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doPresent""",
                                actbox_name="""present""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayPresent()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToPresented']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingitem_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToPresented']
    transitionDef.setProperties(title="""backToPresented""",
                                new_state_id="""presented""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToPresented""",
                                actbox_name="""backToPresented""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## State Variable
    workflow.variables.setStateVar('review_state')

    ## Variables initialization
    variableDef = workflow.variables['review_history']
    variableDef.setProperties(description="""Provides access to workflow history""",
                              default_value="""""",
                              default_expr="""state_change/getHistory""",
                              for_catalog=0,
                              for_status=0,
                              update_always=0,
                              props={'guard_permissions': 'Request review; Review portal content'})

    variableDef = workflow.variables['comments']
    variableDef.setProperties(description="""Comments about the last transition""",
                              default_value="""""",
                              default_expr="""python:state_change.kwargs.get('comment', '')""",
                              for_catalog=0,
                              for_status=1,
                              update_always=1,
                              props=None)

    variableDef = workflow.variables['time']
    variableDef.setProperties(description="""Time of the last transition""",
                              default_value="""""",
                              default_expr="""state_change/getDateTime""",
                              for_catalog=0,
                              for_status=1,
                              update_always=1,
                              props=None)

    variableDef = workflow.variables['actor']
    variableDef.setProperties(description="""The ID of the user who performed the last transition""",
                              default_value="""""",
                              default_expr="""user/getId""",
                              for_catalog=0,
                              for_status=1,
                              update_always=1,
                              props=None)

    variableDef = workflow.variables['action']
    variableDef.setProperties(description="""The last transition""",
                              default_value="""""",
                              default_expr="""transition/getId|nothing""",
                              for_catalog=0,
                              for_status=1,
                              update_always=1,
                              props=None)

    ## Worklists Initialization


    # WARNING: below protected section is deprecated.
    # Add a tagged value 'worklist' with the worklist name to your state(s) instead.

    ##code-section create-workflow-setup-method-footer #fill in your manual code here
    ##/code-section create-workflow-setup-method-footer



def createmeetingitem_workflow(self, id):
    """Create the workflow for PloneMeeting.
    """

    ob = DCWorkflowDefinition(id)
    setupmeetingitem_workflow(self, ob)
    return ob

addWorkflowFactory(createmeetingitem_workflow,
                   id='meetingitem_workflow',
                   title='meetingitem_workflow')

##code-section create-workflow-module-footer #fill in your manual code here
##/code-section create-workflow-module-footer

