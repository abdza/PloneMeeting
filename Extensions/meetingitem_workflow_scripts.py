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


# Workflow Scripts for: meetingitem_workflow

##code-section workflow-script-header #fill in your manual code here
from Products.PloneMeeting.PodTemplate import freezePodDocumentsIfRelevant

def do(action, state_change):
    '''What must I do when a transition is triggered on a Meeting item?'''
    actionsAdapter = state_change.object.wfActions()
    # 1. Execute some actions defined in the corresponding adapter
    actionMethod = getattr(actionsAdapter, action)
    actionMethod(state_change)
    # 2. Update the security of all annexes linked to this meeting item.
    #    Indeed, annexes but have exactly the same "permissions/roles" mapping
    #    as their linked item. Calling "doUpdateAnnexesSecurity" ensures that.
    actionsAdapter.doUpdateAnnexesSecurity(state_change)
    podTransition = 'pod_item_%s' % state_change.transition.id
    freezePodDocumentsIfRelevant(state_change.object, podTransition)
##/code-section workflow-script-header


def doConfirm(self, state_change, **kw):
    do('doConfirm', state_change)



def doDelay(self, state_change, **kw):
    do('doDelay', state_change)



def doBackToRefused(self, state_change, **kw):
    do('doCorrect', state_change)



def doBackToDelayed(self, state_change, **kw):
    do('doCorrect', state_change)



def doAccept(self, state_change, **kw):
    do('doAccept', state_change)



def doBackToPresented(self, state_change, **kw):
    do('doCorrect', state_change)



def doPropose(self, state_change, **kw):
    do('doPropose', state_change)



def doRefuse(self, state_change, **kw):
    do('doRefuse', state_change)



def doItemFreeze(self, state_change, **kw):
    do('doItemFreeze', state_change)



def doBackToItemFrozen(self, state_change, **kw):
    do('doCorrect', state_change)



def doPresent(self, state_change, **kw):
    do('doPresent', state_change)



def doBackToPropose(self, state_change, **kw):
    do('doCorrect', state_change)



def doItemArchive(self, state_change, **kw):
    do('doItemArchive', state_change)



def doBackToValidated(self, state_change, **kw):
    do('doCorrect', state_change)



def doValidate(self, state_change, **kw):
    do('doValidate', state_change)



def doBackToConfirmed(self, state_change, **kw):
    do('doCorrect', state_change)



def doBackToItemPublished(self, state_change, **kw):
    do('doCorrect', state_change)



def doBackToAccepted(self, state_change, **kw):
    do('doCorrect', state_change)



def doItemPublish(self, state_change, **kw):
    do('doItemPublish', state_change)



def doBackToItemCreated(self, state_change, **kw):
    do('doCorrect', state_change)


