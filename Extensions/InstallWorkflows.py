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
from Products.ExternalMethod.ExternalMethod import ExternalMethod

##code-section module-header #fill in your manual code here
##/code-section module-header

def installWorkflows(self, package, out):
    """Install the custom workflows for this product."""

    productname = 'PloneMeeting'
    workflowTool = getToolByName(self, 'portal_workflow')

    ourProductWorkflow = ExternalMethod('temp', 'temp',
                                        productname+'.'+'meetingitem_workflow',
                                        'createmeetingitem_workflow')
    workflow = ourProductWorkflow(self, 'meetingitem_workflow')
    if 'meetingitem_workflow' in workflowTool.listWorkflows():
        print >> out, 'meetingitem_workflow already in workflows.'
    else:
        workflowTool._setObject('meetingitem_workflow', workflow)
    workflowTool.setChainForPortalTypes(['MeetingItem'], workflow.getId())

    ourProductWorkflow = ExternalMethod('temp', 'temp',
                                        productname+'.'+'meeting_workflow',
                                        'createmeeting_workflow')
    workflow = ourProductWorkflow(self, 'meeting_workflow')
    if 'meeting_workflow' in workflowTool.listWorkflows():
        print >> out, 'meeting_workflow already in workflows.'
    else:
        workflowTool._setObject('meeting_workflow', workflow)
    workflowTool.setChainForPortalTypes(['Meeting'], workflow.getId())

    ourProductWorkflow = ExternalMethod('temp', 'temp',
                                        productname+'.'+'plonemeeting_onestate_workflow',
                                        'createplonemeeting_onestate_workflow')
    workflow = ourProductWorkflow(self, 'plonemeeting_onestate_workflow')
    if 'plonemeeting_onestate_workflow' in workflowTool.listWorkflows():
        print >> out, 'plonemeeting_onestate_workflow already in workflows.'
    else:
        workflowTool._setObject('plonemeeting_onestate_workflow', workflow)
    workflowTool.setChainForPortalTypes(['ToolPloneMeeting', 'ExternalApplication'], workflow.getId())

    ourProductWorkflow = ExternalMethod('temp', 'temp',
                                        productname+'.'+'plonemeeting_activity_workflow',
                                        'createplonemeeting_activity_workflow')
    workflow = ourProductWorkflow(self, 'plonemeeting_activity_workflow')
    if 'plonemeeting_activity_workflow' in workflowTool.listWorkflows():
        print >> out, 'plonemeeting_activity_workflow already in workflows.'
    else:
        workflowTool._setObject('plonemeeting_activity_workflow', workflow)
    workflowTool.setChainForPortalTypes(['Dummy', 'MeetingCategory', 'MeetingConfig', 'MeetingFileType', 'MeetingGroup', 'MeetingAdviceAgreementLevel', 'PodTemplate', 'MeetingUser'], workflow.getId())

    ourProductWorkflow = ExternalMethod('temp', 'temp',
                                        productname+'.'+'meetingitem_archive_workflow',
                                        'createmeetingitem_archive_workflow')
    workflow = ourProductWorkflow(self, 'meetingitem_archive_workflow')
    if 'meetingitem_archive_workflow' in workflowTool.listWorkflows():
        print >> out, 'meetingitem_archive_workflow already in workflows.'
    else:
        workflowTool._setObject('meetingitem_archive_workflow', workflow)
    workflowTool.setChainForPortalTypes(['Dummy'], workflow.getId())

    ourProductWorkflow = ExternalMethod('temp', 'temp',
                                        productname+'.'+'meeting_archive_workflow',
                                        'createmeeting_archive_workflow')
    workflow = ourProductWorkflow(self, 'meeting_archive_workflow')
    if 'meeting_archive_workflow' in workflowTool.listWorkflows():
        print >> out, 'meeting_archive_workflow already in workflows.'
    else:
        workflowTool._setObject('meeting_archive_workflow', workflow)
    workflowTool.setChainForPortalTypes(['Dummy'], workflow.getId())

    ourProductWorkflow = ExternalMethod('temp', 'temp',
                                        productname+'.'+'meetingadvice_workflow',
                                        'createmeetingadvice_workflow')
    workflow = ourProductWorkflow(self, 'meetingadvice_workflow')
    if 'meetingadvice_workflow' in workflowTool.listWorkflows():
        print >> out, 'meetingadvice_workflow already in workflows.'
    else:
        workflowTool._setObject('meetingadvice_workflow', workflow)
    workflowTool.setChainForPortalTypes(['MeetingAdvice'], workflow.getId())

    ##code-section after-workflow-install #fill in your manual code here
    ##/code-section after-workflow-install

    return workflowTool

def uninstallWorkflows(self, package, out):
    """Deinstall the workflows.

    This code doesn't really do anything, but you can place custom
    code here in the protected section.
    """

    ##code-section workflow-uninstall #fill in your manual code here
    ##/code-section workflow-uninstall

    pass
