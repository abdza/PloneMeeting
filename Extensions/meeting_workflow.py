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
     ModifyPortalContent, ReviewPortalContent, DeleteObjects
##/code-section create-workflow-module-header


productname = 'PloneMeeting'

def setupmeeting_workflow(self, workflow):
    """Define the meeting_workflow workflow.
    """
    # Add additional roles to portal
    portal = getToolByName(self,'portal_url').getPortalObject()
    data = list(portal.__ac_roles__)
    for role in ['MeetingManager', 'MeetingObserverLocal', 'MeetingObserverUnpublished', 'MeetingObserverGlobal', 'MeetingArchiveObserver']:
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
                                    "Added by product 'PloneMeeting'/workflow 'meeting_workflow'")
                    except KeyError: # role already exists
                        pass
            except AttributeError:
                pass
    portal.__ac_roles__ = tuple(data)

    workflow.setProperties(title='meeting_workflow')

    ##code-section create-workflow-setup-method-header #fill in your manual code here
    ##/code-section create-workflow-setup-method-header


    for s in ['created', 'published', 'decided', 'closed', 'frozen', 'archived']:
        workflow.states.addState(s)

    for t in ['backToFrozen', 'backToPublished', 'republish', 'backToCreated', 'publish', 'freeze', 'decide', 'close', 'backToClosed', 'backToDecided', 'archive']:
        workflow.transitions.addTransition(t)

    for v in ['review_history', 'comments', 'time', 'actor', 'action']:
        workflow.variables.addVariable(v)

    workflow.addManagedPermission(View)
    workflow.addManagedPermission(AccessContentsInformation)
    workflow.addManagedPermission(ModifyPortalContent)
    workflow.addManagedPermission(ReviewPortalContent)
    workflow.addManagedPermission(DeleteObjects)

    for l in []:
        if not l in workflow.worklists.objectValues():
            workflow.worklists.addWorklist(l)

    ## Initial State

    workflow.states.setInitialState('created')

    ## States initialization

    stateDef = workflow.states['created']
    stateDef.setProperties(title="""created""",
                           description="""""",
                           transitions=['publish'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverUnpublished'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverLocal', 'MeetingObserverUnpublished'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['published']
    stateDef.setProperties(title="""published""",
                           description="""""",
                           transitions=['backToCreated', 'republish', 'freeze'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager'])

    stateDef = workflow.states['decided']
    stateDef.setProperties(title="""decided""",
                           description="""""",
                           transitions=['close', 'backToFrozen'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager'])

    stateDef = workflow.states['closed']
    stateDef.setProperties(title="""closed""",
                           description="""""",
                           transitions=['backToDecided', 'archive'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager'])

    stateDef = workflow.states['frozen']
    stateDef.setProperties(title="""frozen""",
                           description="""""",
                           transitions=['backToPublished', 'decide'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager'])

    stateDef = workflow.states['archived']
    stateDef.setProperties(title="""archived""",
                           description="""""",
                           transitions=['backToClosed'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal', 'MeetingArchiveObserver'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingManager', 'MeetingObserverGlobal', 'MeetingArchiveObserver'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager'])

    ## Transitions initialization

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToFrozen']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToFrozen']
    transitionDef.setProperties(title="""backToFrozen""",
                                new_state_id="""frozen""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToFrozen""",
                                actbox_name="""backToFrozen""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToPublished']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToPublished']
    transitionDef.setProperties(title="""backToPublished""",
                                new_state_id="""published""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToPublished""",
                                actbox_name="""backToPublished""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doRepublish']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['republish']
    transitionDef.setProperties(title="""republish""",
                                new_state_id="""published""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doRepublish""",
                                actbox_name="""republish""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayRepublish()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToCreated']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToCreated']
    transitionDef.setProperties(title="""backToCreated""",
                                new_state_id="""created""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToCreated""",
                                actbox_name="""backToCreated""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doPublish']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['publish']
    transitionDef.setProperties(title="""publish""",
                                new_state_id="""published""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doPublish""",
                                actbox_name="""publish""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayPublish()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doFreeze']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['freeze']
    transitionDef.setProperties(title="""freeze""",
                                new_state_id="""frozen""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doFreeze""",
                                actbox_name="""freeze""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayFreeze()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doDecide']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['decide']
    transitionDef.setProperties(title="""decide""",
                                new_state_id="""decided""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doDecide""",
                                actbox_name="""decide""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayDecide()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doClose']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['close']
    transitionDef.setProperties(title="""close""",
                                new_state_id="""closed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doClose""",
                                actbox_name="""close""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayClose()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToClosed']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToClosed']
    transitionDef.setProperties(title="""backToClosed""",
                                new_state_id="""closed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToClosed""",
                                actbox_name="""backToClosed""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToDecided']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['backToDecided']
    transitionDef.setProperties(title="""backToDecided""",
                                new_state_id="""decided""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToDecided""",
                                actbox_name="""backToDecided""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayCorrect()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doArchive']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meeting_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['archive']
    transitionDef.setProperties(title="""archive""",
                                new_state_id="""archived""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doArchive""",
                                actbox_name="""archive""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayArchive()'},
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



def createmeeting_workflow(self, id):
    """Create the workflow for PloneMeeting.
    """

    ob = DCWorkflowDefinition(id)
    setupmeeting_workflow(self, ob)
    return ob

addWorkflowFactory(createmeeting_workflow,
                   id='meeting_workflow',
                   title='meeting_workflow')

##code-section create-workflow-module-footer #fill in your manual code here
##/code-section create-workflow-module-footer

