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

def setupmeeting_archive_workflow(self, workflow):
    """Define the meeting_archive_workflow workflow.
    """
    # Add additional roles to portal
    portal = getToolByName(self,'portal_url').getPortalObject()
    data = list(portal.__ac_roles__)
    for role in ['MeetingManager', 'MeetingObserverGlobal', 'MeetingArchiveObserver']:
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
                                    "Added by product 'PloneMeeting'/workflow 'meeting_archive_workflow'")
                    except KeyError: # role already exists
                        pass
            except AttributeError:
                pass
    portal.__ac_roles__ = tuple(data)

    workflow.setProperties(title='meeting_archive_workflow')

    ##code-section create-workflow-setup-method-header #fill in your manual code here
    ##/code-section create-workflow-setup-method-header


    for s in ['archived']:
        workflow.states.addState(s)

    for t in []:
        workflow.transitions.addTransition(t)

    for v in ['review_history', 'comments', 'time', 'actor', 'action']:
        workflow.variables.addVariable(v)

    workflow.addManagedPermission(View)
    workflow.addManagedPermission(AccessContentsInformation)
    workflow.addManagedPermission(ReviewPortalContent)
    workflow.addManagedPermission(ModifyPortalContent)
    workflow.addManagedPermission(DeleteObjects)

    for l in []:
        if not l in workflow.worklists.objectValues():
            workflow.worklists.addWorklist(l)

    ## Initial State

    workflow.states.setInitialState('archived')

    ## States initialization

    stateDef = workflow.states['archived']
    stateDef.setProperties(title="""archived""",
                           description="""""",
                           transitions=[])
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



def createmeeting_archive_workflow(self, id):
    """Create the workflow for PloneMeeting.
    """

    ob = DCWorkflowDefinition(id)
    setupmeeting_archive_workflow(self, ob)
    return ob

addWorkflowFactory(createmeeting_archive_workflow,
                   id='meeting_archive_workflow',
                   title='meeting_archive_workflow')

##code-section create-workflow-module-footer #fill in your manual code here
##/code-section create-workflow-module-footer

