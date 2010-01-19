# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Copyright (c) 2007 PloneGov
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
# ------------------------------------------------------------------------------
from zope.interface import Interface

# Base interface realized by MeetingItem ---------------------------------------
class IMeetingItem(Interface):
    '''Represents an item that can be presented in a meeting. This interface is
       the base interface that is realized by MeetingItem.'''
    def getMeetingsAcceptingItems():
        '''Gets the meetings that can accept items.'''
    def isDelayed():
        '''Am I delayed ?'''
    def isRefused():
        '''Am I refused ?'''
    def getItemReference():
        '''Returns the reference associated to this item. If the format of your
           item references is simple, you should define it by a TAL expression,
           directly in the MeetingConfig (through the web or via a profile).
           Indeed, this is the default behaviour of getItemReference: to produce
           a reference based on a format specified as a TAL expression in the
           MeetingConfig. If your references are too complex, then override
           this method in a specific adapter.'''
    def mustShowItemReference():
        '''When must I show the item reference ? In the default implementation,
           item references are shown as soon as a meeting is published.'''
    def getSpecificDocumentContext():
        '''When a document is generated from an item, the POD template that is
           used (see http://appyframework.org/pod.html) receives some variables
           in its context (the item, the currently logged user, etc). If you
           want to give more elements in the context, you can override this
           method, that must return a dict whose keys will correspond to
           variables that you can use in the POD template, and whose values
           will be the values of those variables.'''
    def getSpecificMailContext(event, translationMapping):
        '''When a given p_event occurs on this meeting item, PloneMeeting will
           send mail. For defining the mail subject and body, PloneMeeting will
           use i18n labels <event>_mail_subject and <event>_mail_body in i18n
           domain 'PloneMeeting'. When writing translations for those labels in
           your i18n .po files, PloneMeeting will give you the following
           variables that you may insert with the syntax ${variableName}
             - portalUrl          The full URL of your Plone site
             - portalTitle        The title your Plone site
             - itemTitle          The title of the meeting item
             - lastAnnexTitle     The title of the last annex added to this item
                                  (be it desision-related or not)
             - lastAnnexTypeTitle The title of the annex type of the last annex
                                  added to this item
             - meetingTitle       The title of the meeting to which this item
                                  belongs (only when relevant)
             - meetingDavUrl      The WebDAV URL of the meeting to which this
                                  item belongs (only when relevant)
           If you want to have other variables than those provided by default,
           you can override this method: you will receive the default
           p_translationMapping and you can add variables in it (the
           p_translationMapping is a dict whose keys are variable names and
           values are variable values). If you want to define yourself custom
           mail subjects and bodies, simply return (mailSubject, mailBody). If
           this method returns nothing, the mail body and subject will be
           defined as described above.'''
    def includeMailRecipient(event, userId):
        '''This method is called when p_event occurs on this meeting item, and
           when PloneMeeting should normally send a notification to user
           p_userId (which has the necessary role or permission); user will
           actually be added to the list of recipients only if this method
           returns True. The default PloneMeeting behaviour for this method is
           to return True in all cases. (Adapt it if you want to filter the
           recipients of a notification belong other criteria than their role
           or permission.)'''
    def addRecurringItemToMeeting(meeting):
        '''This meeting item was just created (by copy/pasting a recurring item)
           in the folder that also contains the p_meeting into which it must
           be inserted. So in this method, we must trigger automatically some
           transitions on the workflow defined for meeting items, in order
           to insert this item into the p_meeting and set it at the correct
           state.'''
    def mayBeLinkedToTasks():
        '''This method returns True if this meeting item fulfills conditions
           such that it can be associated to tasks. In the default
           implementation, it is the case if the item is in state "confirmed"
           or is in state "itemarchived" and previous state was "confirmed".'''
    def transformRichTextField(fieldName, richContent):
        '''This method is called every time an item is created or updated. It
           allows you to modify the content of any "richtext" attribute
           (description, decision...) defined on the item (the field name is
           given in p_fieldName). The method must return the adapted version of
           p_richContent, which contains the XHTML content of the "richtext"
           field (a string). The default PloneMeeting behaviour for this method
           is to return p_richContent untouched.

           A current limitation of this mechanism: if you apply some
           transformation on the field named "description", you will get
           a conflict with the PloneMeeting "color system": this system will
           always detect that some change occurred if this method updates the
           field, and the pm_modification_date of the corresponding item will
           be updated. With the field named "decision" this problem does not
           occur because it is not taken into account by the PloneMeeting color
           system.'''
    def onEdit(isCreated):
        '''This method is called every time an item is created or updated.
           p_isCreated is True if the object was just created. It is called
           within Archetypes methods at_post_create_script and
           at_post_edit_script. You do not need to reindex the item. The
           default PloneMeeting implementation for this method does nothing.'''
    def getInsertOrder(insertMethod):
        '''When inserting an item into a meeting, several "methods" are
           available, built in PloneMeeting (follow category order, proposing
           group order, all groups order, at the end, etc). If you want to
           implement your own "method", you may want to propose an alternative
           behaviour here, by returning an "order", or "weight" that you assign
           to the current item. According to this "order", the item will be
           inserted at the right place. This method receives the p_insertMethod
           as specified in the meeting config, which may not be useful if you
           choose to implement your own one.'''
    def getAdvisers():
        '''Returns the groups of advisers that need to give their advice on this
           item. The result is a dict whose keys are ids of Plone advisers
           groups annd whose values are titles of corresponding
           MeetingGroups.'''

# Interfaces used for customizing the behaviour of meeting items ---------------
class IMeetingItemWorkflowConditions(Interface):
    '''Conditions that may be defined in the workflow associated with a meeting
       item are defined as methods in this interface.'''
    def mayPropose():
        '''May this item be proposed by a member to some reviewer ?'''
    def mayValidate():
        '''May this item be validated by a reviewer and proposed to a meeting
           owner ?'''
    def mayPresent():
        '''May this item be presented in a meeting ?'''
    def mayDecide():
        '''May a decision take place on this item (accept, reject...)?'''
    def mayDelay():
        '''May this item be delayed to another meeting ?'''
    def mayConfirm():
        '''May the decision be definitely confirmed?'''
    def mayCorrect():
        '''May the user cancel the previous action performed on me?'''
    def mayDelete():
        '''May one delete me? In the PloneMeeting default implementation, it is
           always True. This method is used to allow more fine-grained security
           than the "Delete objects" permission. Indeed, in some complex cases,
           even if the user has this permission on an item, it is not desirable
           to delete the item."'''
    def mayDeleteAnnex(annex):
        '''May I delete p_annex (p_annex is one of my annexes) ?. In the
           PloneMeeting default implementation, it is always True. This method
           is used to allow more fine-grained security than the "Delete objects"
           permission on p_annex.'''
    def mayPublish():
        '''May one publish me?'''
    def meetingIsPublished():
        '''Is the meeting where I am included published ?'''
    def mayFreeze():
        '''May one freeze me ?'''
    def mayArchive():
        '''May one archive me ?'''
    def isLateFor(meeting):
        '''Normally, when meeting agendas are published (and seen by everyone),
           we shouldn't continue to add items to it. But sometimes those things
           need to happen :-). This method allows to determine under which
           circumstances an item may still be "late-presented" to a p_meeting.

           Here is the default behaviour of this method as implemented into
           PloneMeeting: an item whose preferred meeting is p_meeting, and
           that was validated after the p_meeting has been published, may still
           be presented to the p_meeting if the meeting is still in "published"
           state (so in this case, m_isLateFor returns True).

           Note that when such items are presented into a meeting, they are
           added in a special section, below the items that were presented under
           "normal" circumstances. This way, people that consult meeting agendas
           know that there is a fixed part of items that were in the meeting
           when it was first published, and that there are additional "late"
           items that were added in a hurry.'''

class IMeetingItemWorkflowActions(Interface):
    '''Actions that may be triggered while the workflow linked to an item
       executes.'''
    def doPropose(stateChange):
        '''Executes when an item is proposed to a reviewer.'''
    def doValidate(stateChange):
        '''Executes when an action is validated by a reviewer and proposed to
           the meeting owner.'''
    def doPresent(stateChange):
        '''Executes when an item is presented in a meeting.'''
    def doItemPublish(stateChange):
        '''Executes when the meeting containing this item is published.'''
    def doItemFreeze(stateChange):
        '''Executes when the meeting containing this item is frozen (ie
           published, but without most people having the possibility to modify
           it).'''
    def doAccept(stateChange):
        '''Executes when an item is accepted.'''
    def doRefuse(stateChange):
        '''Executes when an item is refused.'''
    def doDelay(stateChange):
        '''Executes when an item is delayed.'''
    def doCorrect(stateChange):
        '''Executes when the user performs a wrong action and needs to undo
           it.'''
    def doConfirm(stateChange):
        '''Executes when an item is definitely confirmed.'''
    def doItemArchive(stateChange):
        '''Executes when the meeting containing this item is archived.'''
    def doUpdateAnnexesSecurity(stateChange):
        '''When an item goes in a new state, this method is called by
           PloneMeeting in order to update permissions/roles mappings defined
           on annexes.'''

class IMeetingItemCustom(IMeetingItem):
    '''If you want to propose your own implementations of IMeetingItem
       methods, you must define an adapter that adapts IMeetingItem to
       IMeetingItemCustom.'''

# Base interface realized by Meeting -------------------------------------------
class IMeeting(Interface):
    '''Represents a meeting, the central concept in PloneMeeting.'''
    def getDisplayableName(short=False, withHour=True, likeTitle=False):
        '''Returns the name of the meeting as will be displayed in a concise
           manner (or VERY concise if p_short=False) at several places in the
           GUI. If p_withHour is False, the part showing minutes and seconds is
           not displayed. If p_likeTitle is True, the other parameters will be
           ignored and the method will return the meeting title.'''
    def getAvailableItems():
        '''Returns the list of items that may be presented to me.'''
    def isDecided():
        '''Am I in a state such that decisions have all been taken?'''
    def getSpecificDocumentContext():
        '''Similar to the method of the same name in IMeetingItem.'''
    def getSpecificMailContext(event, translationMapping):
        '''Similar to the method of the same name in IMeetingItem. There is one
           diffence: for a meeting, the set of variables that one may use when
           writing translations is the following:
             - portalUrl          The full URL of your Plone site
             - portalTitle        The title your Plone site
             - meetingTitle       The title of this meeting
             - meetingDavUrl      The WebDAV URL of this meeting.'''
    def includeMailRecipient(event, userId):
        '''This method is called when p_event occurs on this meeting, and
           when PloneMeeting should normally send a notification to user
           p_userId (which has the necessary role or permission); user will
           actually be added to the list of recipients only if this method
           returns True. The default PloneMeeting behaviour for this method is
           to return True in all cases. (Adapt it if you want to filter the
           recipients of a notification belong other criteria than their role
           or permission.)'''
    def showVotes():
        '''Under what circumstances must I show the tab "Votes" for every item
           of this meeting? The default implementation for this method
           returns True when the meeting has started (based on meeting.date or
           meeting.startDate if used).'''


# Interfaces used for customizing the behaviour of meetings --------------------
class IMeetingWorkflowConditions(Interface):
    '''Conditions that may be defined in the workflow associated with a meeting
       are defined as methods in this interface.'''
    def mayPublish():
        '''May the user put me in a state where I am complete and I can be
           published and consulted by authorized persons before I begin?'''
    def mayFroze():
        '''May the user 'froze' the meeting? In this state, the meeting is
           published, is not decided yet but nobody may modify the meeting
           agenda anymore (at least in theory).'''
    def mayDecide():
        '''May the user put me in a state where all the decisions related to
           all my items are taken ?'''
    def mayClose():
        '''May the user put me in a state where all the decisions are completely
           finalized ?'''
    def mayArchive():
        '''May the user archive me ?'''
    def mayCorrect():
        '''May the user cancel the previous action performed on me?'''
    def mayRepublish():
        '''May the user publish me again ?'''

    # The following conditions are not workflow conditions in the strict sense,
    # but are conditions that depend on the meeting state.
    def mayAcceptItems():
        '''May I accept new items to be integrated to me ? (am I in a relevant
           state, is my date still in the future, ...)'''
    def mayChangeItemsOrder():
        '''May one change order of my list of items ?'''
    def mayDelete():
        '''May one delete me? In the PloneMeeting default implementation, a
           meeting may only be deleted if it contains no item.'''

class IMeetingWorkflowActions(Interface):
    '''Actions that may be triggered while the workflow linked to a meeting
       executes.'''
    def doPublish(stateChange):
        '''Executes when the meeting is "published" (=becomes visible by every
           authorized user). In the default PloneMeeting implementation,
           Meeting.doPublish calls Item.doPublish for every "presented" item
           contained in the meeting. It does so on the sorted list of items, so
           Item.doPublish methods are called in the item order. The default
           implementation also attributes a meeting number to the
           meeting (a sequence number within the meeting configuration).'''
    def doDecide(stateChange):
        '''Executes when all items contained in me are "decided". In the default
           PloneMeeting implementation, Meeting.doDecide calls Item.doAccept
           for every "frozen" item contained in the meeting. It does so on the
           sorted list of items because we use getItemsInOrder.'''
    def doClose(stateChange):
        '''Executes when all decisions are finalized. In the default
           PloneMeeting implementation, Meeting.doClose calls Item.doConfirm
           for every "accepted" item contained in the meeting. It does so on the
           sorted list of items because we use getItemsInOrder.'''
    def doArchive(stateChange):
        '''Executes when the meeting is archived.'''
    def doRepublish(stateChange):
        '''Executes when I am published again.'''
    def doBackToDecided(stateChange):
        '''Executes when I undo a "close" transition.'''
    def doBackToCreated(stateChange):
        '''Executes when I undo a "publish" transition.'''
    def doBackToPublished(stateChange):
        '''Executes when I undo a "decide" transition.'''
    def doBackToClosed(stateChange):
        '''Executes when I undo a "archive" transition.'''

class IMeetingCustom(IMeeting):
    '''If you want to propose your own implementations of IMeeting methods,
       you must define an adapter that adapts IMeeting to IMeetingCustom.'''

# Interfaces used for customizing the behaviour of meeting advices -------------
class IMeetingAdvice(Interface):
    '''Represents a meeting advice'''
    def onEdit(isCreated):
        '''This method is called every time an advice is created or updated.
           p_isCreated is True if the object was just created. It is called
           within Archetypes methods at_post_create_script and
           at_post_edit_script. You do not need to reindex the item. The
           default PloneMeeting implementation for this method does nothing.'''

class IMeetingAdviceCustom(IMeetingAdvice):
    '''If you want to propose your own implementations of IMeetingAdvice
       methods, you must define an adapter that adapts IMeetingAdvice to
       IMeetingAdviceCustom.'''

class IMeetingAdviceWorkflowConditions(Interface):
    '''Conditions that may be defined in the workflow associated with a meeting
       advice are defined as methods in this interface.'''
    def mayPublish():
        '''May this advice be published ?'''
    def mayClose():
        '''May this advice be closed ?'''
    def mayBackToPublished():
        '''May this advice be corrected ?'''
    def mayBackToCreated():
        '''May this advice be corrected ?'''

class IMeetingAdviceWorkflowActions(Interface):
    '''Actions that may be triggered while the workflow linked to a meeting
       advice executes.'''
    def doPublish(stateChange):
        '''Executes when the advice is published'''
    def doClose(stateChange):
        '''Executes when the advice is closed'''
    def doBackToPublished(stateChange):
        '''Executes when the advice is back to published'''
    def doBackToCreated(stateChange):
        '''Executes when the advice is back to created'''

# Interfaces used for customizing the behaviour of meeting categories ----------
class IMeetingCategory(Interface):
    '''Represents a meeting category.'''
    def onEdit(isCreated):
        '''This method is called every time a category is created or updated.
           p_isCreated is True if the object was just created. It is called
           within Archetypes methods at_post_create_script and
           at_post_edit_script. You do not need to reindex the category. The
           default PloneMeeting implementation for this method does nothing.'''
    def isSelectable():
        '''When creating or updating a meeting item, the user may choose a
           category for this item in a popup (at least if you use field
           "classifier" in the corresponding meeting configuration). Available
           categories are those residing if folder "classifiers" of the meeting
           configuration, for which method isSelectable returns True. The
           default implementation of isSelectable returns True if the workflow
           state is "active" for the category.'''

class IMeetingCategoryCustom(IMeetingCategory):
    '''If you want to propose your own implementations of IMeetingCategory
       methods, you must define an adapter that adapts IMeetingCategory to
       IMeetingCategoryCustom.'''

# Interfaces used for customizing the behaviour of external applications -------
# See docstring of previous classes for understanding this section.
class IExternalApplication(Interface):
    def onEdit(isCreated): '''Called when an object p_isCreated or edited.'''
class IExternalApplicationCustom(IExternalApplication): pass

# Interfaces used for customizing the behaviour of agreement levels ------------
# See docstring of previous classes for understanding this section.
class IMeetingAdviceAgreementLevel(Interface):
    def onEdit(isCreated): '''Called when an object p_isCreated or edited.'''
class IMeetingAdviceAgreementLevelCustom(IMeetingAdviceAgreementLevel): pass

# Interfaces used for customizing the behaviour of meeting configs -------------
# See docstring of previous classes for understanding this section.
class IMeetingConfig(Interface):
    def onEdit(isCreated): '''Called when an object p_isCreated or edited.'''
class IMeetingConfigCustom(IMeetingConfig): pass

# Interfaces used for customizing the behaviour of meeting files ---------------
# See docstring of previous classes for understanding this section.
class IMeetingFile(Interface):
    def onEdit(isCreated): '''Called when an object p_isCreated or edited.'''
class IMeetingFileCustom(IMeetingFile): pass

# Interfaces used for customizing the behaviour of meeting file types ----------
# See docstring of previous classes for understanding this section.
class IMeetingFileType(Interface):
    def onEdit(isCreated): '''Called when an object p_isCreated or edited.'''
    def isSelectable():
        '''When adding an annex to an item, the user may choose a file type for
           this annex, among all file types defined in the corresponding meeting
           config for which this method isSelectable returns True. The
           default implementation of isSelectable returns True if the workflow
           state is "active" for the meeting file type.'''
class IMeetingFileTypeCustom(IMeetingFileType): pass

# Interfaces used for customizing the behaviour of meeting groups --------------
# See docstring of previous classes for understanding this section.
class IMeetingGroup(Interface):
    def onEdit(isCreated): '''Called when an object p_isCreated or edited.'''
class IMeetingGroupCustom(IMeetingGroup): pass

# Interfaces used for customizing the behaviour of pod templates ---------------
# See docstring of previous classes for understanding this section.
class IPodTemplate(Interface):
    def onEdit(isCreated): '''Called when an object p_isCreated or edited.'''
class IPodTemplateCustom(IPodTemplate): pass

# Interfaces used for customizing the behaviour of the PloneMeeting tool -------
# See docstring of previous classes for understanding this section.
class IToolPloneMeeting(Interface):
    def onEdit(isCreated): '''Called when the tool p_isCreated or edited.'''
class IToolPloneMeetingCustom(IToolPloneMeeting): pass

# Interfaces used for customizing the behaviour of meeting users ---------------
# See docstring of previous classes for understanding this section.
class IMeetingUser(Interface):
    def onEdit(isCreated):
        '''Called when an object p_isCreated or edited.'''
    def mayConsultVote(loggedUser, item):
        '''May the currently logged user (p_loggedUser) see the vote from this
           meeting user on p_item?

           The default implementation returns True if the logged user is the
           voter, a Manager or a MeetingManager or if the meeting was decided
           (result of meeting.isDecided()).'''
    def mayEditVote(loggedUser, item):
        '''May the currently logged user (p_loggedUser) edit the vote from this
           meeting user on p_item?

           The default implementation returns True if the meeting has not been
           decided yet (result of meeting.isDecided()), and if the logged user
           is the voter himself (provided voters encode votes according to the
           meeting configuration) or if the logged user is a meeting manager
           (provided meeting managers encode votes according to the meeting
           configuration) or if the logged user is a Manager.'''

class IMeetingUserCustom(IMeetingUser): pass
# ------------------------------------------------------------------------------
