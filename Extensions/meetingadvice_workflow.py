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
from Products.CMFCore.permissions import ModifyPortalContent, DeleteObjects, View, AccessContentsInformation, ReviewPortalContent
##/code-section create-workflow-module-header


productname = 'PloneMeeting'

def setupmeetingadvice_workflow(self, workflow):
    """Define the meetingadvice_workflow workflow.
    """
    # Add additional roles to portal
    portal = getToolByName(self,'portal_url').getPortalObject()
    data = list(portal.__ac_roles__)
    for role in ['MeetingAdviceEditor', 'MeetingManager']:
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
                                    "Added by product 'PloneMeeting'/workflow 'meetingadvice_workflow'")
                    except KeyError: # role already exists
                        pass
            except AttributeError:
                pass
    portal.__ac_roles__ = tuple(data)

    workflow.setProperties(title='meetingadvice_workflow')

    ##code-section create-workflow-setup-method-header #fill in your manual code here
    ##/code-section create-workflow-setup-method-header


    for s in ['advicecreated', 'advicepublished', 'adviceclosed']:
        workflow.states.addState(s)

    for t in ['advicePublish', 'adviceBackToCreated', 'adviceClose', 'adviceBackToPublished']:
        workflow.transitions.addTransition(t)

    for v in ['review_history', 'comments', 'time', 'actor', 'action']:
        workflow.variables.addVariable(v)

    workflow.addManagedPermission(ModifyPortalContent)
    workflow.addManagedPermission(DeleteObjects)
    workflow.addManagedPermission(AccessContentsInformation)
    workflow.addManagedPermission(View)
    workflow.addManagedPermission(ReviewPortalContent)

    for l in []:
        if not l in workflow.worklists.objectValues():
            workflow.worklists.addWorklist(l)

    ## Initial State

    workflow.states.setInitialState('advicecreated')

    ## States initialization

    stateDef = workflow.states['advicecreated']
    stateDef.setProperties(title="""advicecreated""",
                           description="""""",
                           transitions=['advicePublish'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingAdviceEditor', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingAdviceEditor', 'MeetingManager'])
    stateDef.setPermission(AccessContentsInformation,
                           0,
                           ['Manager', 'MeetingAdviceEditor', 'MeetingManager'])
    stateDef.setPermission(View,
                           0,
                           ['Manager', 'MeetingAdviceEditor', 'MeetingManager'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingAdviceEditor', 'MeetingManager'])

    stateDef = workflow.states['advicepublished']
    stateDef.setProperties(title="""advicepublished""",
                           description="""""",
                           transitions=['adviceBackToCreated', 'adviceClose'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager', 'MeetingManager'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager', 'MeetingManager'])

    stateDef = workflow.states['adviceclosed']
    stateDef.setProperties(title="""adviceclosed""",
                           description="""""",
                           transitions=['adviceBackToPublished'])
    stateDef.setPermission(ModifyPortalContent,
                           0,
                           ['Manager'])
    stateDef.setPermission(DeleteObjects,
                           0,
                           ['Manager'])
    stateDef.setPermission(ReviewPortalContent,
                           0,
                           ['Manager'])

    ## Transitions initialization

    ## Creation of workflow scripts
    for wf_scriptname in ['doPublish']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingadvice_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['advicePublish']
    transitionDef.setProperties(title="""advicePublish""",
                                new_state_id="""advicepublished""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doPublish""",
                                actbox_name="""advicePublish""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayPublish()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToCreated']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingadvice_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['adviceBackToCreated']
    transitionDef.setProperties(title="""adviceBackToCreated""",
                                new_state_id="""advicecreated""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToCreated""",
                                actbox_name="""adviceBackToCreated""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayBackToCreated()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doClose']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingadvice_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['adviceClose']
    transitionDef.setProperties(title="""adviceClose""",
                                new_state_id="""adviceclosed""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doClose""",
                                actbox_name="""adviceClose""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayClose()'},
                                )

    ## Creation of workflow scripts
    for wf_scriptname in ['doBackToPublished']:
        if not wf_scriptname in workflow.scripts.objectIds():
            workflow.scripts._setObject(wf_scriptname,
                ExternalMethod(wf_scriptname, wf_scriptname,
                productname + '.meetingadvice_workflow_scripts',
                wf_scriptname))

    transitionDef = workflow.transitions['adviceBackToPublished']
    transitionDef.setProperties(title="""adviceBackToPublished""",
                                new_state_id="""advicepublished""",
                                trigger_type=1,
                                script_name="""""",
                                after_script_name="""doBackToPublished""",
                                actbox_name="""adviceBackToPublished""",
                                actbox_url="""""",
                                actbox_category="""workflow""",
                                props={'guard_expr': 'python:here.wfConditions().mayBackToPublished()'},
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



def createmeetingadvice_workflow(self, id):
    """Create the workflow for PloneMeeting.
    """

    ob = DCWorkflowDefinition(id)
    setupmeetingadvice_workflow(self, ob)
    return ob

addWorkflowFactory(createmeetingadvice_workflow,
                   id='meetingadvice_workflow',
                   title='meetingadvice_workflow')

##code-section create-workflow-module-footer #fill in your manual code here
##/code-section create-workflow-module-footer

