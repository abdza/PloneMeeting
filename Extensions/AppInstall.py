# -*- coding: utf-8 -*-
#
# File: AppInstall.py
#
# Copyright (c) 2009 by PloneGov
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

__author__ = """Gauthier BASTIEN <gbastien@commune.sambreville.be>"""
__docformat__ = 'plaintext'

from BTrees.OOBTree import OOBTree
from Products.PloneMeeting.config import *
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression
from Products.CMFPlacefulWorkflow.PlacefulWorkflowTool import \
     WorkflowPolicyConfig_id
import logging
logger = logging.getLogger('PloneMeeting')

ploneFolderTypes = ('Folder', 'Large Plone Folder')
folderViews = ('meetingfolder_redirect_view', 'meetingfolder_view')
pmGroupProperties = ('meetingRole', 'meetingGroupId')
noSearchTypes = ('Folder',)

def install(self):
    # Add document action for document generation.
    for docAction in docActions:
        if not self.portal_actionicons.queryActionIcon('plone', docAction):
            self.portal_actionicons.addActionIcon(
                'plone', docAction, 'document_icon.gif', title=docAction)

    # Add icon for action "toggle descriptions"
    tgAction = 'toggleDescriptions'
    if not self.portal_actionicons.queryActionIcon('plone', tgAction):
        self.portal_actionicons.addActionIcon('plone', tgAction,
        'collapseDescrs.png', title='Toggle')

    # Add icon for action "duplicate"
    duplicateAction = 'duplicate'
    if not self.portal_actionicons.queryActionIcon(\
        'object_buttons', duplicateAction):
        self.portal_actionicons.addActionIcon('object_buttons', duplicateAction,
            'copy_icon.gif', title='Duplicate')

    # Add icon for action "copyitem"
    duplicateAction = 'copyitem'
    if not self.portal_actionicons.queryActionIcon(
        'object_buttons', duplicateAction):
        self.portal_actionicons.addActionIcon('object_buttons', duplicateAction,
            'copy_icon.gif', title='CopyItem')

    # Add our own "rename" icon to add an icon to the "rename" action
    if not self.portal_actionicons.queryActionIcon('object_buttons', 'rename'):
       self.portal_actionicons.addActionIcon(
           'object_buttons', 'rename', 'rename_icon.gif', title='Rename')

    # We add meetingfolder_redirect_view and meetingfolder_view to the list of
    # available views for types "Folder" and "Large Plone Folder"
    for ploneFolderType in ploneFolderTypes:
        portalType = getattr(self.portal_types, ploneFolderType)
        available_views = list(portalType.getAvailableViewMethods(None))
        for folderView in folderViews:
            if folderView not in available_views:
                available_views.append(folderView)
        portalType.manage_changeProperties(view_methods=available_views)

    # Change the url of the plonemeeting configuration panel action
    # We just verify that the action is in the actions list and we change the
    # action_url.
    for action in self.portal_controlpanel._actions:
        if action.id == "ToolPloneMeeting":
            # Removed trailing "/view"
            expression = "string:${portal_url}/portal_plonemeeting"
            action.action = Expression(text=str(expression))

    # Make "Unauthorized" exceptions appear in the error log.
    self.error_log.setProperties(
        25, copy_to_zlog=1, ignored_exceptions=('NotFound', 'Redirect'))

    # Enable WevDAV access for meeting archive observers
    self.manage_permission('WebDAV access', ('MeetingArchiveObserver',),
                           acquire=0)

    # Set a specific workflow policy for all objects created in the tool
    ppw = self.portal_placeful_workflow
    if not hasattr(ppw, 'portal_plonemeeting_policy'):
        ppw.manage_addWorkflowPolicy('portal_plonemeeting_policy',
            workflow_policy_type = 'default_workflow_policy (Simple Policy)',
            duplicate_id = 'empty')
        self.portal_plonemeeting.manage_addProduct[\
            'CMFPlacefulWorkflow'].manage_addWorkflowPolicyConfig()

    pol = ppw.portal_plonemeeting_policy
    pol.setTitle('PloneMeeting tool policy')
    pol.setChain('Topic', ('plonemeeting_activity_workflow',))
    pol.setChain('ExternalApplication', ('plonemeeting_onestate_workflow',))
    pol.setChainForPortalTypes(
        ('MeetingGroup', 'MeetingConfig', 'MeetingFileType',
         'MeetingCategory'), ('plonemeeting_activity_workflow',))
    pc = getattr(self.portal_plonemeeting, WorkflowPolicyConfig_id)
    pc.setPolicyIn('')
    pc.setPolicyBelow('portal_plonemeeting_policy')

    # Register PloneMeeting portlets
    leftPortlets = self.getProperty('left_slots')
    if leftPortlets == None:
        leftPortlets = []
    portletsToAdd = []
    for pmPortlet in ploneMeetingPortlets:
        if pmPortlet not in leftPortlets:
            portletsToAdd.append(pmPortlet)
    self.manage_changeProperties(left_slots=tuple(portletsToAdd) +
                                            tuple(leftPortlets))

    # Register PloneMeeting-specific properties on groups
    for groupProp in pmGroupProperties:
        if not self.portal_groupdata.hasProperty(groupProp):
             self.portal_groupdata.manage_addProperty(groupProp, '', 'string')

    self.portal_plonemeeting.at_post_create_script()

    # Register configlet icon
    self.portal_actionicons.updateActionIcon(
        'controlpanel', 'ToolPloneMeeting', 'ploneMeeting.png',
        title='PloneMeeting')

    # Add to the tool the dict allowing to remember user accesses to items and
    # annexes
    if not hasattr(self.portal_plonemeeting.aq_base, 'accessInfo'):
        self.portal_plonemeeting.accessInfo = OOBTree()

    # Manually add indexes not auto-added by Archetypes.
    # "indexAdvisers" is a method of MeetingItem that returns the list of
    # selected advisers.
    class _extra: pass
    if 'indexAdvisers' not in self.portal_catalog.indexes():
        extra = _extra
        extra.lexicon_id = "plone_lexicon"
        extra.index_type = 'Okapi BM25 Rank'
        self.portal_catalog.addIndex('indexAdvisers', 'ZCTextIndex',extra=extra)

    # Add a paste_plonemeeting action. We need to use our own paste action
    # because some after paste actions have to be implemented, especially for
    # items.
    actions = self.portal_actions.listActions()
    action_ids = [action.id for action in actions]
    if not 'paste_plonemeeting' in action_ids:
        self.portal_actions.addAction(id='paste_plonemeeting',
            name='Paste PloneMeeting', action='string:paste_items:method',
            condition='object/showPasteMeetingItemAction',
            permission=('View',), category='folder_buttons',
            visible=True)
    if not 'copy_plonemeeting' in action_ids:
        self.portal_actions.addAction(id='copy_plonemeeting',
            name='Copy PloneMeeting', action='string:folder_copyitems:method',
            condition='object/showFolderCopyMeetingItemAction',
            permission=('Copy or Move', ), category='folder_buttons',
            visible=True)

    # We use our own action category "folder_buttons_plonemeeting".
    # So we know that our actions will not be displayed anywhere else in Plone.
    if not 'plonemeeting_delete' in action_ids:
        self.portal_actions.addAction(id='plonemeeting_delete',
            name='PloneMeeting Delete',
            action='string:plonemeeting_delete:method', condition='',
            permission=('Delete objects',),
            category='folder_buttons_plonemeeting', visible=True)

    # Add action for accessing the PloneMeeting advanced search.
    if not 'pm_search' in action_ids:
        self.portal_actions.addAction(id='pm_search', name='pm_search',
            action='string:search_form', condition='python:member is not None',
            permission=('View',), category='user', visible=True)

    # Reload actions on every config-specific type
    for meetingConfig in self.portal_plonemeeting.objectValues('MeetingConfig'):
        meetingConfig.updatePortalTypes()

    # Remove some types from the standard Plone search (live and advanced).
    props = self.portal_properties.site_properties
    nsTypes = props.getProperty('types_not_searched')
    if not nsTypes: nsTypes = []
    else: nsTypes = list(nsTypes)
    for t in noSearchTypes:
        if t not in nsTypes: nsTypes.append(t)
    props.manage_changeProperties(types_not_searched=tuple(nsTypes))

    return "PloneMeeting installed."
