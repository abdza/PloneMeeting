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


# Workflow Scripts for: meeting_workflow

##code-section workflow-script-header #fill in your manual code here
from Products.PloneMeeting.utils import sendMailIfRelevant, \
                                        addRecurringItemsIfRelevant
from Products.PloneMeeting.PodTemplate import freezePodDocumentsIfRelevant

def do(action, state_change):
    '''What must I do when a transition is triggered on a meeting ?'''
    actionsAdapter = state_change.object.wfActions()
    # Execute first some actions defined in the corresponding adapter
    actionMethod = getattr(actionsAdapter, action)
    actionMethod(state_change)
    # Add recurring items to the meeting if relevant
    addRecurringItemsIfRelevant(state_change.object, state_change.transition.id)
    # Send mail if relevant
    sendMailIfRelevant(state_change.object, state_change.transition.id, 'View')
    podTransition = 'pod_meeting_%s' % state_change.transition.id
    freezePodDocumentsIfRelevant(state_change.object, podTransition)
##/code-section workflow-script-header


def doBackToDecided(self, state_change, **kw):
    do('doBackToDecided', state_change)



def doClose(self, state_change, **kw):
    do('doClose', state_change)



def doRepublish(self, state_change, **kw):
    do('doRepublish', state_change)



def doDecide(self, state_change, **kw):
    do('doDecide', state_change)



def doBackToCreated(self, state_change, **kw):
    do('doBackToCreated', state_change)



def doBackToFrozen(self, state_change, **kw):
    do('doBackToFrozen', state_change)



def doArchive(self, state_change, **kw):
    do('doArchive', state_change)



def doPublish(self, state_change, **kw):
    do('doPublish', state_change)



def doBackToPublished(self, state_change, **kw):
    do('doBackToPublished', state_change)



def doFreeze(self, state_change, **kw):
    do('doFreeze', state_change)



def doBackToClosed(self, state_change, **kw):
    do('doBackToClosed', state_change)


