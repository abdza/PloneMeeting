# -*- coding: utf-8 -*-
#
# File: testMeetingItem.py
#
# Copyright (c) 2007 by PloneGov
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

from AccessControl import Unauthorized
from Products.PloneMeeting.config import *
from Products.PloneMeeting.MeetingItem import \
    LIST_ADVISERS_KEY, MISSING_ADVICES_ID, MISSING_ADVICES_ICON_URL
from Products.PloneMeeting.tests.PloneMeetingTestCase import \
    PloneMeetingTestCase
from sets import Set
from Products.Archetypes.utils import DisplayList

class testMeetingItem(PloneMeetingTestCase):
    '''Tests the MeetingItem class methods.'''

    def afterSetUp(self):
        PloneMeetingTestCase.afterSetUp(self)

    def testUpdateAdviceIndex(self):
        '''This method updates self.adviceIndex (see doc in
           MeetingItem.__init__). If p_advice is None, this method recomputes the
           whole adviceIndex. If p_advice is not None:
           - if p_remove is False, info about the newly created p_advice is added
             to self.adviceIndex;
           - if p_remove is True, info about the deleted p_advice is removed from
             self.adviceIndex.'''
        self.login('pmManager')
        item = self.create('MeetingItem')
        ret = [x for x in item.adviceIndex.items()]
        self.assertEquals(ret,
            [(LIST_ADVISERS_KEY,
              {'developers_advisers':'Developers'})])
        self.setAttributes(item,
            **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        ret = [x for x in item.adviceIndex.items()]
        self.assertEquals(ret,
            [(LIST_ADVISERS_KEY,
              {'developers_advisers':'Developers',
               'vendors_advisers':'Vendors'})])
        self.do(item, 'propose')
        self.do(item, 'validate')
        advice = self.create('MeetingAdvice', folder=item,
            **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        self.setAttributes(advice, **{'adviserName':'vendors_advisers'})
        # we call it explicitly to be sure it is 
        item.updateAdviceIndex(advice=advice, removeAdvice=False)
        ret = [x for x in item.adviceIndex.items()]
        self.assertEquals(ret,
            [(advice.UID(), advice.getAdviceInfo()),
             (LIST_ADVISERS_KEY, {'developers_advisers':'Developers',
                                  'vendors_advisers':'Vendors'})])
        item.updateAdviceIndex(advice=advice, removeAdvice=True)
        ret = [x for x in item.adviceIndex.items()]
        self.assertEquals(ret,
            [(LIST_ADVISERS_KEY, {'developers_advisers':'Developers',
                                  'vendors_advisers':'Vendors'})])

    def testGetDefaultMandatoryAdvisers(self):
        """
            We get the mandatory advisers list calculated
            from the meetingGroups
        """
        # Create an item as creator
        self.login('pmCreator1')
#        item = self.create('MeetingItem', **{'mandatoryAdvisers':self.meetingConfig.getMandatoryAdvisers()})
        item = self.create('MeetingItem')
        self.assertEquals(Set(item.calculateMandatoryAdvisers()), Set(['developers_advisers']))
        self.assertEquals(Set(item.calculateMandatoryAdvisers()), Set(['developers_advisers']))
        self.logout()

    def testListMandatoryAdvisers(self):
        """
            We get the mandatory advisers list selected in the meeting configuration 
        """
        # Create an item as creator
        self.login('pmCreator1')
        item = self.create('MeetingItem')
        self.assertEquals(item.listMandatoryAdvisers(), DisplayList([('developers_advisers', u'Developers (advisers)'), ('vendors_advisers', u'Vendors (advisers)')]))
        self.logout()

    def testListOptionalAdvisers(self):
        """
            We get the optional advisers list selected in the meeting configuration
        """
        # Create an item as creator
        self.login('pmCreator1')
        item = self.create('MeetingItem')
        self.assertEquals(item.listOptionalAdvisers(), DisplayList((('vendors_advisers', u'Vendors (advisers)'), )))
        self.logout()

    def testUpdateLocalRoles(self):
        """
            Updates the local roles of this item, regarding the proposing group.
        """
        self.login('pmCreator1')
#        item = self.create('MeetingItem', **{'mandatoryAdvisers':self.meetingConfig.getMandatoryAdvisers()})
        item = self.create('MeetingItem')
        # we set the optionalAdvisers attribute after the creation to have the permission to write it
        item.setOptionalAdvisers(self.meetingConfig.getOptionalAdvisers())
        item.updateLocalRoles()
        res = [('pmCreator1', ('Owner',)), ('developers_reviewers', ('MeetingReviewer',)), 
               ('developers_observers', ('MeetingObserverLocal',)), ('developers_creators', ('MeetingMember',)),
               ('developers_advisers', ('MeetingAdviser',)), ('vendors_advisers', ('MeetingAdviser',))]
        self.assertEquals(Set(res), Set(item.get_local_roles()))

    def testGetAdvicesByAgreementLevel(self):
        """
         Return advices ('adviceInfo' dicts) grouped by agreement level :
         [ [[agLevel_id, agLevel_iconUrl], [adviceInfo, ...]], ...]
        """
        self.login('pmManager')
        item = self.create('MeetingItem')
        ret = item.getAdvicesByAgreementLevel(withMissing=False)
        self.assertEquals(ret, [])
        ret = item.getAdvicesByAgreementLevel()
        self.assertEquals(ret,
            [[[MISSING_ADVICES_ID, MISSING_ADVICES_ICON_URL],
              [{'agLevel_Title':u'agreement_level_no_advices',
                'agLevel_id': MISSING_ADVICES_ID,
                'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
                'adviser_id': 'developers_advisers',
                'adviser_Title': 'Developers'}]]])
        self.setAttributes(item,
            **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        ret = item.getAdvicesByAgreementLevel()
        self.assertEquals(ret,
            [[[MISSING_ADVICES_ID, MISSING_ADVICES_ICON_URL],
              [{'agLevel_Title':u'agreement_level_no_advices',
                'agLevel_id': MISSING_ADVICES_ID,
                'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
                'adviser_id': 'vendors_advisers',
                'adviser_Title': 'Vendors'},
               {'agLevel_Title':u'agreement_level_no_advices',
                'agLevel_id': MISSING_ADVICES_ID,
                'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
                'adviser_id': 'developers_advisers',
                'adviser_Title': 'Developers'}]]])
        self.do(item, 'propose')
        self.do(item, 'validate')
        advice = self.create('MeetingAdvice', folder=item,
            **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        self.setAttributes(advice, **{'adviserName':'vendors_advisers'})
        ret = item.getAdvicesByAgreementLevel()
        metingConfigId = self.tool.getMeetingConfig(item).getId()
        self.assertEquals(ret,
            [[['positive', '/plone/portal_plonemeeting/' \
                   '%s/agreementlevels/positive/theIcon' % metingConfigId],
              [{'agLevel_id': 'positive',
                'agLevel_Title': 'Positive',
                'agLevel_iconUrl': '/plone/portal_plonemeeting/' \
                    '%s/agreementlevels/positive/theIcon' % metingConfigId,
                'adviser_id': 'vendors_advisers',
                'adviser_Title': 'Vendors',
                'uid': advice.UID(),
                'creator': 'pmManager',
                'Title': 'Vendors',
                'advice_Title': '',
                'url': '/plone/Members/pmManager/mymeetings/%s/o1/o2' % metingConfigId,
                'description': '',
                'review_state': 'advicecreated',
                'modification_date': advice.pm_modification_date}]],
             [[MISSING_ADVICES_ID, MISSING_ADVICES_ICON_URL],
              [{'agLevel_Title':u'agreement_level_no_advices',
                'adviser_id': 'developers_advisers',
                'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
                'agLevel_id': MISSING_ADVICES_ID,
                'adviser_Title': 'Developers'}]]])

    def testGetAdvicesSortedByAgreementLevel(self):
        '''Return advices ('adviceInfo' dicts) sorted by agreement level.'''

        # results expected after creating an item (without advices)
        # => testing 'missing advices' display
        self.login('pmManager')
        item = self.create('MeetingItem')
        self.assertEquals(
            item.getAdvicesSortedByAgreementLevel(withMissing=False),
            [])
        self.assertEquals(
            item.getAdvicesSortedByAgreementLevel(),
            [{'agLevel_Title':u'agreement_level_no_advices',
              'agLevel_id': MISSING_ADVICES_ID,
              'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
              'adviser_id': 'developers_advisers',
              'adviser_Title': 'Developers'}])
        self.setAttributes(item,
            **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        self.assertEquals(item.getAdvicesSortedByAgreementLevel(),
            [{'agLevel_Title':u'agreement_level_no_advices',
              'agLevel_id': MISSING_ADVICES_ID,
              'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
              'adviser_id': 'vendors_advisers',
              'adviser_Title': 'Vendors'},
             {'agLevel_Title':u'agreement_level_no_advices',
              'agLevel_id': MISSING_ADVICES_ID,
              'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
              'adviser_id': 'developers_advisers',
              'adviser_Title': 'Developers'}])

        # result expected after creating 2 advices by 2 ways...
        # => testing display ordered by agLevel_id
        self.do(item, 'propose')
        self.do(item, 'validate')
        metingConfigId = self.tool.getMeetingConfig(item).getId()
        expectedResult = \
            [{'agLevel_id': 'negative',
              'agLevel_Title': 'Negative',
              'agLevel_iconUrl': '/plone/portal_plonemeeting/' \
                  '%s/agreementlevels/negative/theIcon' % metingConfigId,
              'adviser_id': 'vendors_advisers',
              'adviser_Title': 'Vendors',
              'creator': 'pmManager',
              'Title': 'Vendors',
              'advice_Title': '',
              'review_state': 'advicecreated',  
              'description': ''},
             {'agLevel_id': 'positive',
              'agLevel_Title': 'Positive',
              'agLevel_iconUrl': '/plone/portal_plonemeeting/' \
                  '%s/agreementlevels/positive/theIcon' % metingConfigId,
              'adviser_id': 'vendors_advisers',
              'adviser_Title': 'Vendors',
              'creator': 'pmManager',
              'Title': 'Vendors',
              'advice_Title': '',
              'review_state': 'advicecreated',  
              'description': ''},
             {'agLevel_Title':u'agreement_level_no_advices',
              'adviser_id': 'developers_advisers',
              'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
              'agLevel_id': MISSING_ADVICES_ID,
              'adviser_Title': 'Developers'}]
        # 1st way
        advice1 = self.create('MeetingAdvice', folder=item,
            **{'agreementLevel':'negative', 'adviserName':'vendors_advisers'})
        self.setAttributes(advice1, **{'adviserName':'vendors_advisers'})
        # (some properties can not be guessed, so we update expected result)
        expectedResult[0].update(
            {'url': advice1.absolute_url_path(),
             'uid': advice1.UID(),
             'modification_date': advice1.pm_modification_date})
        advice2 = self.create('MeetingAdvice', folder=item,
            **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        self.setAttributes(advice2, **{'adviserName':'vendors_advisers'})
        expectedResult[1].update(
            {'url': advice2.absolute_url_path(),
             'uid': advice2.UID(),
             'modification_date': advice2.pm_modification_date})
        self.assertEquals(item.getAdvicesSortedByAgreementLevel(),
                          expectedResult)
        # (deleting advices created by 1st way - we take the opportunity to
        # test 'delete_givenuid' script and 'updateAdviceIndex()' method)
        self.portal.delete_givenuid(advice1.UID())
        self.portal.delete_givenuid(advice2.UID())
        # 2nd way
        advice1 = self.create('MeetingAdvice', folder=item,
            **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        self.setAttributes(advice1, **{'adviserName':'vendors_advisers'})
        expectedResult[1].update(
            {'url': advice1.absolute_url_path(),
             'uid': advice1.UID(),
             'modification_date': advice1.pm_modification_date})
        advice2 = self.create('MeetingAdvice', folder=item,
            **{'agreementLevel':'negative', 'adviserName':'vendors_advisers'})
        self.setAttributes(advice2, **{'adviserName':'vendors_advisers'})
        expectedResult[0].update(
            {'url': advice2.absolute_url_path(),
             'uid': advice2.UID(),
             'modification_date': advice2.pm_modification_date})
        self.assertEquals(item.getAdvicesSortedByAgreementLevel(),
                          expectedResult)

        # results expected by a local meeting reviewer
        # => testing display taking into account 'View' permission
        self.logout()
        # (login)
        self.login('pmReviewer1')
        self.assertEquals(
            item.getAdvicesSortedByAgreementLevel(),
            [{'agLevel_Title':u'agreement_level_no_advices',
              'adviser_id': 'vendors_advisers',
              'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
              'agLevel_id': MISSING_ADVICES_ID,
              'adviser_Title': 'Vendors'},
             {'agLevel_Title':u'agreement_level_no_advices',
              'adviser_id': 'developers_advisers',
              'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
              'agLevel_id': MISSING_ADVICES_ID,
              'adviser_Title': 'Developers'}])
        # (publishing the negative advice)
        self.logout()
        self.login('pmManager')
        self.do(advice2, 'advicePublish')
        self.logout()
        # (login)
        self.login('pmReviewer1')
        self.assertEquals(item.getAdvicesSortedByAgreementLevel(),
            [{'agLevel_id': 'negative',
              'agLevel_Title': 'Negative',
              'agLevel_iconUrl': '/plone/portal_plonemeeting/' \
                  '%s/agreementlevels/negative/theIcon' % metingConfigId,
              'adviser_id': 'vendors_advisers',
              'adviser_Title': 'Vendors',
              'uid': advice2.UID(),
              'creator': 'pmManager',
              'Title': 'Vendors',
              'advice_Title': '',
              'url': advice2.absolute_url_path(),
              'description': '',
              'review_state': 'advicepublished',
              'modification_date': advice2.pm_modification_date},
             {'agLevel_Title':u'agreement_level_no_advices',
              'adviser_id': 'developers_advisers',
              'agLevel_iconUrl': MISSING_ADVICES_ICON_URL,
              'agLevel_id': MISSING_ADVICES_ID,
              'adviser_Title': 'Developers'}])

    def testListAdvisersForUser(self):
        """
            Returns a list containing the "adviser groups" on whose behalf a
            user may add an advice related to me.

            - If user has Manager or MeetingManager role on me, he may add an
              advice even if it does not belong to any 'advisers group' which
              has MeetingAdviser role on me, and although it is not part of
              any 'advisers group' defined in meetingconfig.
              So this user should have the freedom to determine the 'advisers
              group' on whose behalf he submit the advice, by selecting inside
              all existing 'advisers groups' defined in meetingconfig, but also
              to submit the advice in the name of the 'advisers group(s)'
              linked to the meetinggroup(s) which is eventually member.

            - Else the user may only add an advice in the name of "advisers
              group(s)" he's member, and which have 'MeetingAdviser' role on me.
        """
        # Schema 1 : a 'Developers' creator creates an item
        ###################################################
        # N.B. 'Developers' advisers are designated as 'mandatory advisers' in
        # test config
        self.login('pmCreator1')
        item = self.create('MeetingItem')
        self.do(item, 'propose')
        self.changeUser('pmReviewer1')
        self.do(item, 'validate')
        # -> 'Developers' reviewer has not 'Add MeetingAdvice' permission
        self.assertEquals(item.listAdvisersForUser().items(), ())
        # -> 'Developers' advisers are item "mandatory advisers"
        self.changeUser('pmAdviser1')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('developers_advisers', u'Developers'),))
        # -> 'Vendors' advisers have not 'Add MeetingAdvice' permission
        self.changeUser('pmReviewer2')
        self.assertEquals(item.listAdvisersForUser().items(),  ())
        # -> pmManager may choose adviserName within all "advisers groups"
        # defined in config, while being informed if they are not designated as
        # item advisers
        self.changeUser('pmManager')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('vendors_advisers', u'Vendors'),
                           ('developers_advisers', u'Developers')))
        # -> ...and if pmManager choose to designate 'Vendors' as item
        # "optional advisers", we should view several changes... (we take the
        # opportunity to test the item 'updateLocalRoles' method)
        item.setOptionalAdvisers(('vendors_advisers',))
        item.at_post_edit_script()
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('vendors_advisers', u'Vendors'),
                           ('developers_advisers', u'Developers')))
        self.changeUser('pmReviewer2')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('vendors_advisers', u'Vendors'),))
        # Schema 2 : a 'Vendors' creator creates an item
        ################################################
        self.login('pmCreator2')
        item = self.create('MeetingItem')
        self.do(item, 'propose')
        self.changeUser('pmReviewer2')
        self.do(item, 'validate')
        # -> 'Vendors' advisers are not item advisers, but they even may add
        # advice (since they are members of creator's meeting group - we take
        # again the opportunity to test the item 'updateLocalRoles' method)
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('vendors_advisers', u'Vendors'),))
        # -> 'Developers' advisers are item "mandatory advisers"
        self.changeUser('pmAdviser1')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('developers_advisers', u'Developers'),))
        # -> pmManager may choose adviserName within all "advisers groups"
        # defined in config, while being informed if they are not designated as
        # item advisers
        self.changeUser('pmManager')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('vendors_advisers', u'Vendors'),
                           ('developers_advisers', u'Developers')))
        # Schema 3 : a 'Developers' creator creates an item, and designates
        ###################################################################
        # 'Vendors' as advisers
        #######################
        self.changeUser('pmCreator1')
        item = self.create('MeetingItem')
        self.setAttributes(item, **{'optionalAdvisers':('vendors_advisers',)})
        self.do(item, 'propose')
        self.changeUser('pmReviewer1')
        self.do(item, 'validate')
        # -> 'Developers' advisers are item "mandatory advisers"
        self.changeUser('pmAdviser1')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('developers_advisers', u'Developers'),))
        # -> 'Vendors' advisers are item "optional advisers"
        self.changeUser('pmReviewer2')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('vendors_advisers', u'Vendors'),))
        # -> pmManager may choose adviserName within all "advisers groups"
        # defined in config, while being informed if they are not designated as
        # item advisers
        self.changeUser('pmManager')
        self.assertEquals(item.listAdvisersForUser().items(),
                          (('vendors_advisers', u'Vendors'),
                           ('developers_advisers', u'Developers')))

    def testUsedColorSystemShowColors(self):
        """
           The showColors is initialized by the showColorsForUser method that depends on the value selected in portal_plonemeeting.usedColorSystem and portal_plonemeeting.colorSystemDisabledFor
        """
        #check with an empty list of colorSystemDisabledFor users
        self.tool.setColorSystemDisabledFor(None)
        #check with no colorization
        self.tool.setUsedColorSystem('no_color')
        self.assertEquals(self.tool.showColorsForUser(), False)
        #check with state_color
        self.tool.setUsedColorSystem('state_color')
        self.assertEquals(self.tool.showColorsForUser(), True)
        #check with modification_color
        self.tool.setUsedColorSystem('modification_color')
        self.assertEquals(self.tool.showColorsForUser(), True)

        #check with an list of user the current user is not in
        self.tool.setColorSystemDisabledFor("user1\nuser2\nuser3")
        #login as a user that is not in the list here above
        self.login('pmCreator1')
        #check with no colorization
        self.tool.setUsedColorSystem('no_color')
        self.assertEquals(self.tool.showColorsForUser(), False)
        #check with state_color
        self.tool.setUsedColorSystem('state_color')
        self.assertEquals(self.tool.showColorsForUser(), True)
        #check with modification_color
        self.tool.setUsedColorSystem('modification_color')
        self.assertEquals(self.tool.showColorsForUser(), True)

        #check with an list of user the current user is in
        self.login('admin')
        self.tool.setColorSystemDisabledFor("user1\nuser2\nuser3\npmCreator1")
        #login as a user that is not in the list here above
        self.login('pmCreator1')
        #check with no colorization
        self.tool.setUsedColorSystem('no_color')
        self.assertEquals(self.tool.showColorsForUser(), False)
        #check with state_color
        self.tool.setUsedColorSystem('state_color')
        self.assertEquals(self.tool.showColorsForUser(), False)
        #check with modification_color
        self.tool.setUsedColorSystem('modification_color')
        self.assertEquals(self.tool.showColorsForUser(), False)

    def testUsedColorSystemGetColoredLink(self):
        """
           The colorization of the item depends on the usedColorSystem value of the tool
        """
        #colorization modes are applied on MeetingItem, MeetingFile and Meeting
        #1. first check with a MeetingItem
        #1.1 check when the user is not in colorSystemDisabledFor
        self.tool.setColorSystemDisabledFor(None)
        #check with no colorization
        self.tool.setUsedColorSystem('no_color')
        #create an item for test
        self.login('pmCreator1')
        item = self.create('MeetingItem')
        item.setTitle('item_title')
        #here, the resulting item should not be colored
        showColors = self.tool.showColorsForUser()
        title = item.Title()
        url = item.absolute_url()
        content = item.Title()
        self.assertEquals(self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s" id="pmNoNewContent">%s</a>' % (url, title, content))
        self.login('admin')
        #use colors depdending on item workflow state
        self.tool.setUsedColorSystem('state_color')
        self.login('pmCreator1')
        showColors = self.tool.showColorsForUser()
        wf_class = "state-" + self.portal.portal_workflow.getInfoFor(item, 'review_state')
        self.assertEquals(self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s" class="%s">%s</a>' % (url, title, wf_class, content))
        self.login('admin')
        #use colors depdending on item modification
        self.tool.setUsedColorSystem('modification_color')
        self.login('pmCreator1')
        #now that we are in modification_color mode, we have to remember the access
        self.tool.rememberAccess(uid = item.UID(), commitNeeded=False)
        showColors = self.tool.showColorsForUser()
        wf_class = self.portal.portal_workflow.getInfoFor(item, 'review_state')
        #the item should not be colored as the creator already saw it
        self.assertEquals(self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s"%s>%s</a>' % (url, title, " id=\"pmNoNewContent\"", content))
        #change the item and check if the color appear for pmCreator1
        self.login('admin')
        #use process_form
        self.portal.REQUEST.set('title', 'my_new_title')
        self.portal.REQUEST.set('description', 'description')
        item.processForm()
        item.at_post_edit_script()
        self.login('pmCreator1')
        showColors = self.tool.showColorsForUser()
        #as 'admin' changed the content, it must be colored to 'pmCreator1'
        self.failIf('pmNoNewContent' in self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s"%s>%s</a>' % (url, title, "", content))

        #1.2 check when the user is in colorSystemDisabledFor
        #in this case, colors are never shown...
        self.tool.setColorSystemDisabledFor("user1\nuser2\npmCreator1")
        #check with no colorization
        self.tool.setUsedColorSystem('no_color')
        #create an item for test
        self.login('pmCreator1')
        item = self.create('MeetingItem')
        item.setTitle('item_title')
        #here, the resulting item should not be colored
        showColors = self.tool.showColorsForUser()
        title = item.Title()
        url = item.absolute_url()
        content = item.Title()
        self.assertEquals(self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s" id="pmNoNewContent">%s</a>' % (url, title, content))
        self.login('admin')
        #use colors depdending on item workflow state
        self.tool.setUsedColorSystem('state_color')
        self.login('pmCreator1')
        showColors = self.tool.showColorsForUser()
        wf_class = "state-" + self.portal.portal_workflow.getInfoFor(item, 'review_state')
        self.assertEquals(self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s" id="pmNoNewContent">%s</a>' % (url, title, content))
        self.login('admin')
        #use colors depdending on item modification
        self.tool.setUsedColorSystem('modification_color')
        self.login('pmCreator1')
        #now that we are in modification_color mode, we have to remember the access
        self.tool.rememberAccess(uid = item.UID(), commitNeeded=False)
        showColors = self.tool.showColorsForUser()
        wf_class = self.portal.portal_workflow.getInfoFor(item, 'review_state')
        #the item should not be colored as the creator already saw it
        self.assertEquals(self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s" id="pmNoNewContent">%s</a>' % (url, title, content))
        #change the item and check if the color appear for pmCreator1
        self.login('admin')
        item.at_post_edit_script()
        self.login('pmCreator1')
        self.assertEquals(self.tool.getColoredLink(item, showColors), '<a href="%s" title="%s" id="pmNoNewContent">%s</a>' % (url, title, content))
        #check the maxLength attribute, "item_title" becomes "it..."
        self.assertEquals(self.tool.getColoredLink(item, showColors, maxLength=2), '<a href="%s" title="%s" id="pmNoNewContent">%s</a>' % (url, title, "it..."))
        #2. check with a Meeting
        #3. check with a MeetingFile
        #4. check with a MeetingAdvice
        #XXX still needs to be done...

    def testListProposingGroup(self):
        """
          Check that the user is creator for the proposing groups
        """
        #that that if a user is cretor for a group but only reviewer for another, it
        #only returns the groups the user is creator for...  This test the bug of ticket #643
        #adapt the pmReviewer1 user : add him to a creator group and create is personnal folder
        self.login('admin')
        #pmReviser1 is member of developer_reviewers and developers_observers
        #add him to a creator group different from his reviwer group
        vcGroup = self.portal.portal_groups.getGroupById('vendors_creators')
        vcGroup.addMember('pmReviewer1')
        #create his personnal zone because he is a creator now
        self.createMemberarea('pmReviewer1')
        self.login('pmReviewer1')
        item = self.create('MeetingItem')
        self.assertEquals(tuple(item.listProposingGroup()), ('vendors', ))

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingItem))
    return suite
