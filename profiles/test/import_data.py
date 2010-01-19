# -*- coding: utf-8 -*-
# Copyright (c) 2008 by PloneGov
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

from Products.PloneMeeting.profiles import *

# First meeting type: a fictitious PloneGov assembly ---------------------------

# Categories
deployment = CategoryDescriptor('deployment', 'Deployment topics')
maintenance = CategoryDescriptor('maintenance', 'Maintenance topics')
development = CategoryDescriptor('development', 'Development topics')
events = CategoryDescriptor('events', 'Events')
research = CategoryDescriptor('research', 'Research topics')
projects = CategoryDescriptor('projects', 'Projects')
# A vintage category
marketing = CategoryDescriptor('marketing', 'Marketing', active=False)

# File types
financialAnalysis = MeetingFileTypeDescriptor(
    'financial-analysis', 'Financial analysis', 'financialAnalysis.png',
    'Predefined title for financial analysis')
legalAnalysis = MeetingFileTypeDescriptor(
    'legal-analysis', 'Legal analysis', 'legalAnalysis.png', '')
budgetAnalysis = MeetingFileTypeDescriptor(
    'budget-analysis', 'Budget analysis', 'budgetAnalysis.png', '')
itemAnnex = MeetingFileTypeDescriptor(
    'item-annex', 'Other annex(es)', 'itemAnnex.png', '')
decision = MeetingFileTypeDescriptor(
    'decision', 'Decision', 'decision.png', '', True) # Could be used once we
    # will digitally sign decisions ? Indeed, once signed, we will need to
    # store them (together with the signature) as separate files.
decisionAnnex = MeetingFileTypeDescriptor(
    'decision-annex', 'Decision annex(es)', 'decisionAnnex.png', '', True)
# A vintage file type
marketingAnalysis = MeetingFileTypeDescriptor(
    'marketing-annex', 'Marketing annex(es)', 'legalAnalysis.png', '', True,
    active=False)

# AgremmentLevels
positive = MeetingAdviceAgreementLevelDescriptor('positive', 'Positive',
                                                 'positive.png')
remarks = MeetingAdviceAgreementLevelDescriptor(
    'remarks', 'Positive with remarks', 'remarks.png')
negative = MeetingAdviceAgreementLevelDescriptor('negative', 'Negative',
                                                 'negative.png')
notused = MeetingAdviceAgreementLevelDescriptor('notused', 'NotUsed',
                                                 'negative.png', active=False)

# Pod templates
agendaTemplate = PodTemplateDescriptor('agendaTemplate', 'Meeting agenda')
agendaTemplate.podTemplate = 'Agenda.odt'
agendaTemplate.podCondition = 'python:here.meta_type=="Meeting"'

decisionsTemplate = PodTemplateDescriptor('decisionsTemplate',
                                          'Meeting decisions')
decisionsTemplate.podTemplate = 'Decisions.odt'
decisionsTemplate.podCondition = 'python:here.meta_type=="Meeting" and ' \
                                 'here.adapted().isDecided()'

itemTemplate = PodTemplateDescriptor('itemTemplate', 'Meeting item')
itemTemplate.podTemplate = 'Item.odt'
itemTemplate.podCondition = 'python:here.meta_type=="MeetingItem"'

# Test users and groups
pmManager = UserDescriptor('pmManager', ['MeetingManager'])
pmCreator1 = UserDescriptor('pmCreator1', [])
pmCreator1b = UserDescriptor('pmCreator1b', [])
pmReviewer1 = UserDescriptor('pmReviewer1', [])
pmCreator2 = UserDescriptor('pmCreator2', [])
pmReviewer2 = UserDescriptor('pmReviewer2', [])
pmAdviser1 = UserDescriptor('pmAdviser1', [])

developers = GroupDescriptor('developers', 'Developers', 'Devel', givesMandatoryAdviceOn='python:True')
developers.creators.append(pmCreator1)
developers.creators.append(pmCreator1b)
developers.creators.append(pmManager)
developers.reviewers.append(pmReviewer1)
developers.reviewers.append(pmManager)
developers.observers.append(pmReviewer1)
developers.observers.append(pmManager)
developers.advisers.append(pmAdviser1)
developers.advisers.append(pmManager)

vendors = GroupDescriptor('vendors', 'Vendors', 'Devil')
vendors.creators.append(pmCreator2)
vendors.reviewers.append(pmReviewer2)
vendors.observers.append(pmReviewer2)
vendors.advisers.append(pmReviewer2)
vendors.advisers.append(pmManager)

# Add a vintage group
endUsers = GroupDescriptor('endUsers', 'End users', 'EndUsers', active=False)

# Add an external user
cadranel = UserDescriptor('cadranel', [], fullname='M. Benjamin Cadranel')

# Add meeting users (voting purposes)
pmReviewer1_voter = MeetingUserDescriptor('pmReviewer1_voter', 'pmReviewer1')

pmManager_observer = MeetingUserDescriptor('pmManager_observer', 'pmManager',
                                           duty='Secrétaire de la Chancellerie',
                                           usages=['assemblyMember'])

cadranel_signer = MeetingUserDescriptor('cadranel_signer', 'cadranel',
                                       duty='Secrétaire',
                                       usages=['assemblyMember', 'signer'],
                                       signatureImage='SignatureCadranel.jpg',
                                       signatureIsDefault=True)

# Meeting configuration
meetingPga = MeetingConfigDescriptor(
    'plonegov-assembly', 'PloneGov assembly', 'PloneGov assembly',
    isDefault=True)
meetingPga.shortName = 'Pga'
meetingPga.assembly = 'Bill Gates, Steve Jobs'
meetingPga.signatures = meetingPga.assembly
meetingPga.categories = [deployment, maintenance, development, events,
                         research, projects, marketing]
meetingPga.meetingFileTypes = [
    financialAnalysis, legalAnalysis, budgetAnalysis, itemAnnex,
    decisionAnnex]
meetingPga.agreementLevels = [ positive, remarks, negative, notused ]
meetingPga.usedItemAttributes = ('toDiscuss', 'associatedGroups')
meetingPga.sortingMethodOnAddItem = 'on_categories'
meetingPga.useGroupsAsCategories = True
meetingPga.useAdvices = True
meetingPga.optionalAdvisers = [vendors.getIdSuffixed()]
meetingPga.enableDuplication = True
# Second meeting type: a fictitious PloneMeeting assembly ----------------------

# Recurring items
#this recurring item cause a problem while creating a Meeting
#because pmManager is not in the vendors creators and can not propose
#this recurring item...  Let this like that to check that it fails...
recItem = RecurringItemDescriptor('recItem1', 'Recurring item #1',
    'vendors', description='<p>This is the first recurring item.</p>',
    decision='Recurring Item approuved')

# Categories
subproducts = CategoryDescriptor('subproducts', 'Subproducts wishes')

# File types
overheadAnalysis = MeetingFileTypeDescriptor(
    'overhead-analysis', 'Administrative overhead analysis',
    'overheadAnalysis.png', '')

meetingPma = MeetingConfigDescriptor(
    'plonemeeting-assembly', 'PloneMeeting assembly', 'PloneMeeting assembly')
meetingPma.shortName = 'Pma'
meetingPma.assembly = 'Gauthier Bastien, Gilles Demaret, Kilian Soree, ' \
                      'Arnaud Hubaux, Jean-Michel Abe, Stephan Geulette, ' \
                      'Godefroid Chapelle, Gaetan Deberdt, Gaetan Delannay'
meetingPma.signatures = meetingPga.assembly
meetingPma.categories = [development, subproducts, research]
meetingPma.meetingFileTypes = [
    financialAnalysis, overheadAnalysis, itemAnnex, marketingAnalysis]
meetingPma.agreementLevels = [ positive, remarks, negative, notused ]
meetingPma.usedItemAttributes = ('toDiscuss', 'itemTags')
meetingPma.usedMeetingAttributes = ('place',)
meetingPma.sortingMethodOnAddItem = 'on_proposing_groups'
meetingPma.allItemTags = '\n'.join(
    ('Strategic decision','Genericity mechanism', 'User interface') )
meetingPma.sortAllItemTags = True
meetingPma.recurringItems.append(recItem)
# This does not seem to work (adding the rec item).
meetingPma.optionalAdvisers = [vendors.getIdSuffixed()]
meetingPma.meetingUsers = [pmReviewer1_voter, pmManager_observer, cadranel_signer]
meetingPma.podTemplates = [agendaTemplate, decisionsTemplate, itemTemplate]
meetingPma.enableDuplication = False
# The whole configuration object -----------------------------------------------
data = PloneMeetingConfiguration('My meetings', (meetingPga, meetingPma),
                                 (developers, vendors, endUsers))
data.usersOutsideGroups = [cadranel]
# ------------------------------------------------------------------------------
