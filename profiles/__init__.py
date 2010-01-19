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

import os.path

# ------------------------------------------------------------------------------
class Descriptor:
    '''This abstract class represents Python data that will be used for
       initializing an Archetypes object.'''
    multiSelectFields = []
    excludedFields = ['active']
    def getData(self):
        '''Gets data in the format needed for initializing the corresponding
           Archetypes object.'''
        res = {}
        for k, v in self.__dict__.iteritems():
            if k in self.excludedFields: continue
            if type(v) not in (list, tuple):
                res[k] = v
            else:
                if k in self.multiSelectFields:
                    res[k] = v
        return res

# Concrete Descriptor classes --------------------------------------------------
class RecurringItemDescriptor(Descriptor):
    excludedFields = ['title']
    def __init__(self, id, title, proposingGroup, description='', category='',
                 associatedGroups=(), decision='', itemKeywords='', itemTags=(),
                 meetingTransitionInsertingMe='_init_'):
        self.id = id
        self.title = title
        self.proposingGroup = proposingGroup
        self.description = description
        self.category = category
        self.associatedGroups = associatedGroups
        self.decision = decision
        self.itemKeywords = itemKeywords
        self.itemTags = itemTags
        self.meetingTransitionInsertingMe = meetingTransitionInsertingMe

class CategoryDescriptor(Descriptor):
    def __init__(self, id, title, description='', active=True):
        self.id = id
        self.title = title
        self.description = description
        self.active = active

class MeetingFileTypeDescriptor(Descriptor):
    def __init__(self, id, title, iconFile, predefinedFileTitle,
                 decisionRelated=False, active=True):
        self.id = id
        self.title = title
        self.iconFile = iconFile
        self.predefinedFileTitle = predefinedFileTitle
        self.decisionRelated = decisionRelated # If True, the file type is used
        # to create annexes linked tdescriptiono a decision, no to an item
        self.active = active

class MeetingAdviceAgreementLevelDescriptor(Descriptor):
    def __init__(self, id, title, iconFile, active=True):
        self.id = id
        self.title = title
        self.iconFile = iconFile
        self.active = active

class PodTemplateDescriptor(Descriptor):
    def __init__(self, id, title, description='', active=True):
        self.id = id
        self.title = title
        self.description = description
        self.active = active
        # Filename of the POD template to use
        # This file must be present in the "templates" folder of a profile.
        self.podTemplate = None
        self.podFormat = 'odt'
        self.podCondition = 'python:True'
        self.podPermission = 'View'
        self.freezeEvent = ''

class PloneGroupDescriptor(Descriptor):
    def __init__(self, id, title, roles):
        self.id = id
        self.title = title
        self.roles = roles

class UserDescriptor(Descriptor):
    '''Useful for creating test users, so PloneMeeting may directly be tested
       after a profile has been imported.'''
    def __init__(self, id, globalRoles, email='user AT plonemeeting.org',
                 password='meeting', fullname=None):
        self.id = id
        self.globalRoles = globalRoles
        self.email = email.replace(' AT ', '@') # Anti-spam
        self.password = password
        self.fullname = fullname
        self.ploneGroups = [] #~[PloneGroupDescriptor]~

class MeetingUserDescriptor(Descriptor):
    def __init__(self, id, ploneUserId, duty=None, usages=['voter'],
                 signatureImage=None, signatureIsDefault=False, active=True):
        self.id = id
        self.duty = duty
        self.ploneUserId = ploneUserId
        self.usages = usages
        self.signatureImage = signatureImage
        self.signatureIsDefault = signatureIsDefault
        self.active = active

class GroupDescriptor(Descriptor):
    # The 'instance' static attribute stores an instance used for assigning
    # default values to a meeting config being created through-the-web.
    instance = None
    def get(klass):
        if not klass.instance:
            klass.instance = GroupDescriptor(None, None, None)
        return klass.instance
    get = classmethod(get)

    def __init__(self, id, title, acronym, description='', active=True,
                 givesMandatoryAdviceOn='python:False'):
        self.id = id
        self.title = title
        self.acronym = acronym
        self.description = description
        self.givesMandatoryAdviceOn = givesMandatoryAdviceOn
        self.creators = [] # ~[UserDescriptor]~
        self.observers = [] # ~[UserDescriptor]~
        self.reviewers = [] # ~[UserDescriptor]~
        self.advisers = [] # ~[UserDescriptor]~
        self.active = active

    def getUsers(self):
        res = []
        for users in (self.creators, self.observers, self.reviewers,
                      self.advisers):
            for user in users:
                if user not in res:
                    res.append(user)
        return res

    def getIdSuffixed(self, suffix='advisers'):
        return '%s_%s' % (self.id, suffix)

class ExternalApplicationDescriptor(Descriptor):
    # Get a prototypical instances used for getting default values.
    instance = None
    def get(klass):
        if not klass.instance:
            klass.instance = ExternalApplicationDescriptor(None, None)
        return klass.instance
    get = classmethod(get)
    def __init__(self, id, title, notify=False, notifyUrl='', notifyEmail=''):
        self.id = id
        self.title = title
        self.notify = notify
        self.notifyUrl = notifyUrl
        self.notifyEmail = notifyEmail
        self.notifyProxy = ''
        self.notifyLogin = ''
        self.notifyPassword = ''
        self.loginHeaderKey = 'username'
        self.passwordHeaderKey = 'password'
        self.meetingParamName = 'meeting'
        self.notifyProtocol = 'httpGet'

class MeetingConfigDescriptor(Descriptor):
    multiSelectFields = ('usedItemAttributes', 'usedMeetingAttributes',
        'itemsListVisibleColumns', 'mailItemEvents', 'mailMeetingEvents',
        'mandatoryAdvisers', 'optionalAdvisers', 'selectableCopyGroups',
        'votesEncoder', 'itemTopicStates', 'meetingTopicStates',
        'decisionTopicStates')
    fieldsWithCustomValidators = ('itemConditionsInterface',
        'itemActionsInterface', 'meetingConditionsInterface',
        'meetingActionsInterface', 'adviceConditionsInterface',
        'adviceActionsInterface')

    # The 'instance' static attribute stores an instance used for assigning
    # default values to a meeting config being created through-the-web.
    instance = None
    def get(klass):
        if not klass.instance:
            klass.instance = MeetingConfigDescriptor(None, None, None)
        return klass.instance
    get = classmethod(get)

    def __init__(self, id, title, folderTitle, isDefault=False, active=True):
        self.id = id # Identifier of the meeting config.
        self.title = title
        self.active = active

        # General parameters ---------------------------------------------------
        self.assembly = 'Person 1, Person 2'
        self.signatures = 'Person 1, Person 2, Person 3'
        self.folderTitle = folderTitle
        self.shortName = '' # Will be used for deducing content types specific
        # to this MeetingConfig (item, meeting)
        self.isDefault = isDefault
        # What is the number of the last item for this meeting config ?
        self.lastItemNumber = 0
        # What is the number of the last meeting for this meeting config ?
        self.lastMeetingNumber = 0
        self.configVersion = '' # If this meeting config corresponds to an
        # organization that identifies its successive forms (ie 5th Parliament,
        # City council 2000-2006, etc), the identifier of the current form may
        # be specified here (ie 'P5', 'CC00_06'...)

        # Data-related parameters ----------------------------------------------
        # Some attributes on an item are optional. In the field
        # "usedItemAttributes", you specify which of those optional attributes
        # you will use in your meeting configuration.
        self.usedItemAttributes = []
        # Some attributes on a meeting are optional, too.
        self.usedMeetingAttributes = ['assembly']
        # Do you want to use MeetingGroups as categories ? In this case, you
        # do not need to define categories anymore.
        self.useGroupsAsCategories = True
        # What must be the default value for the "toDiscuss" field for normal
        # items ?
        self.toDiscussDefault = True
        # What must be the default value for the "toDiscuss" field for late
        # items ?
        self.toDiscussLateDefault = True
        # What is the format of the item references ?
        self.itemReferenceFormat = "python: 'Ref. ' + str(here.getItemNumber(" \
                                   "relativeTo='meetingConfig'))"
        # When adding items to a meeting, must I add the items at the end of
        # the items list or at the end of the items belonging to the same
        # category or proposing group ?
        self.sortingMethodOnAddItem = "at_the_end"
        # List if item tags defined for this meeting config
        self.allItemTags = '' # Must be terms separated by carriage returns in
        # a string.
        # Must we sort the tags in alphabetic order ?
        self.sortAllItemTags = False
        # Item states into which item events will be stored in item's history.
        self.recordItemHistoryStates = ('itempublished', 'itemfrozen',
            'accepted', 'refused', 'confirmed', 'delayed', 'itemarchived')

        # POD templates --------------------------------------------------------
        self.podTemplates = []
        # MeetingUsers --------------------------------------------------------
        self.meetingUsers = [] # ~[MeetingUserDescriptor]~

        # Workflow- and security-related parameters ----------------------------
        self.itemWorkflow = 'meetingitem_workflow'
        self.itemConditionsInterface = 'Products.PloneMeeting.interfaces.' \
                                       'IMeetingItemWorkflowConditions'
        self.itemActionsInterface = 'Products.PloneMeeting.interfaces.' \
                                    'IMeetingItemWorkflowActions'
        self.meetingWorkflow = 'meeting_workflow'
        self.meetingConditionsInterface = 'Products.PloneMeeting.interfaces.' \
                                          'IMeetingWorkflowConditions'
        self.meetingActionsInterface = 'Products.PloneMeeting.interfaces.' \
                                       'IMeetingWorkflowActions'
        self.adviceConditionsInterface = 'Products.PloneMeeting.interfaces.' \
                                       'IMeetingAdviceWorkflowConditions'
        self.adviceActionsInterface = 'Products.PloneMeeting.interfaces.' \
                                    'IMeetingAdviceWorkflowActions'
        self.useCopies = False
        self.selectableCopyGroups = []

        # GUI-related parameters -----------------------------------------------
        # In the "items" portlet, item-related topics will only search items
        # that are in one of the states listed in itemTopicStates
        self.itemTopicStates = ('itemcreated', 'proposed', 'validated',
                                'presented')
        # When the system displays the list of all meetings (the "all meetings"
        # topic), only meetings having one of the stated listed in
        # meetingTopicStates will be shown.
        self.meetingTopicStates = ('created', 'published', 'frozen')
        # In the "decisions" portlet, the "all decisions" portlet will only show
        # meetings having one of the states listed in decisionTopicStates.
        self.decisionTopicStates = ('decided', 'closed', 'archived')
        # Maximum number of meetings or decisions shown in the meeting and
        # decision portlets. If overflow, a combo box is shown instead of a
        # list of links.
        self.maxShownMeetings = 4
        # If a decision if maxDaysDecisions old (or older), it is not shown
        # anymore in the "decisions" portlet. This decision may still be
        # consulted by clicking on "all decisions" in the same portlet.
        self.maxDaysDecisions = 14
        # Which view do you want to select when entering a PloneMeeting folder ?
        self.meetingAppDefaultView = 'topic_searchallmeetings'
        # In the meetingitems_list.pt, you can choose which columns are shown
        self.itemsListVisibleColumns = ('state', 'categoryOrProposingGroup')
        # Item duplication functionnality
        self.enableDuplication = False
        # Lists of available, meeting and late-items are paginated. What are
        # the maximum number of items to show at once?
        self.maxShownAvailableItems = 50
        self.maxShownMeetingItems = 50
        self.maxShownLateItems = 50
        # When showing paginated lists of items, two functions may be visible:
        # go to the page where a given item lies, and go to the meetingitem_view
        # of a given item.
        self.enableGotoPage = False
        self.enableGotoItem = True
        # When opening annexes, some users want to get them in separate windows.
        self.openAnnexesInSeparateWindows = False

        # Mail-related parameters -----------------------------------------------
        # What are the item-related events that trigger mail sending ?
        self.mailItemEvents = []
        # What are the meeting-related events that trigger mail sending?
        self.mailMeetingEvents = []

        # MeetingConfig sub-objects --------------------------------------------
        self.categories = [] # ~[CategoryDescriptor]~
        self.classifiers = [] # ~[CategoryDescriptor]~
        self.recurringItems = [] # ~[RecurringItemDescriptor]~
        self.meetingFileTypes = []

        # Tasks-related parameters ---------------------------------------------
        # Macro that will be called within meetingitem_view.pt for displaying
        # tasks linked to the shown item.
        self.tasksMacro = ''
        # What role is provided by the external task module for creating tasks?
        self.taskCreatorRole = ''

        # Advices parameters ---------------------------------------------------
        # Use advice functionality
        self.useAdvices = False
        self.optionalAdvisers = []
        self.agreementLevels = []

        # Votes parameters -----------------------------------------------------
        self.useVotes = False
        self.votesEncoder = ('theVoterHimself',)
        self.usedVoteValues = ('not_yet', 'yes', 'no', 'abstain')
        self.defaultVoteValue = 'not_yet'

class PloneMeetingConfiguration(Descriptor):
    # The 'instance' static attribute stores an instance used for assigning
    # default values to the portal_plonemeeting tool when it is not initialized
    # through a profile.
    instance = None
    def get(klass):
        if not klass.instance:
            klass.instance = PloneMeetingConfiguration('My meetings', [], [])
        return klass.instance
    get = classmethod(get)

    multiSelectFields = ('availableOcrLanguages',)

    def __init__(self, meetingFolderTitle, meetingConfigs, groups):
        self.meetingFolderTitle = meetingFolderTitle
        self.ploneDiskAware = False
        self.unoEnabledPython = ''
        self.openOfficePort = 2002
        self.navigateLocally = False
        self.functionalAdminEmail = ''
        self.functionalAdminName = ''
        self.usedColorSystem = 'no_color'
        self.colorSystemDisabledFor = ''
        self.restrictUsers = False
        self.unrestrictedUsers = ''
        self.dateFormat = '%d %mt %Y'
        self.extractTextFromFiles = False
        self.availableOcrLanguages = ('eng',)
        self.defaultOcrLanguage = 'eng'
        self.maxSearchResults = 50
        self.maxShownFoundItems = 10
        self.maxShownFoundMeetings = 10
        self.maxShownFoundAnnexes = 10
        self.meetingConfigs = meetingConfigs # ~[MeetingConfigDescriptor]~
        self.groups = groups #~[GroupDescriptor]~
        self.usersOutsideGroups = [] #~[UserDescriptor]~
        self.externalApplications = [] #~[ExternalApplicationDescriptor]~
# ------------------------------------------------------------------------------
