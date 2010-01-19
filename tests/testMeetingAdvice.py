# -*- coding: utf-8 -*-
#
# File: testMeetingAdvice.py
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
from Products.PloneMeeting.tests.PloneMeetingTestCase import \
    PloneMeetingTestCase
from sets import Set
from Products.Archetypes.utils import DisplayList
from DateTime import DateTime

class testMeetingAdvice(PloneMeetingTestCase):
    """
        Tests the MeetingAdvice class methods.
    """

    def afterSetUp(self):
        PloneMeetingTestCase.afterSetUp(self)
        self.meetingConfig.setUseAdvices(True)

    def testListAgreementLevels(self):
        """
            Returns a list containing the active agreementLevels
        """
        self.login('pmManager')
        item = self.create('MeetingItem')
        self.setAttributes(item, **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        self.do(item, 'propose')
        self.do(item, 'validate')
        self.login('pmReviewer2')
        advice = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
#        self.setAttributes(item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        lst =  [('positive', 'Positive'), ('remarks', 'Positive with remarks'), ('negative', 'Negative')]
        self.assertEquals(advice.listAgreementLevels(), DisplayList(tuple(lst)))

    def testListAdvisersNames(self):
        """
            Returns a list containing for the creator the "adviser" groups in which he is
        """
        self.login('pmManager')
        item = self.create('MeetingItem')
        self.setAttributes(item, **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        self.do(item, 'propose')
        self.do(item, 'validate')
        advice = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        lst = [('developers_advisers', 'Developers'), ('vendors_advisers', 'Vendors')]
        self.assertEquals(advice.listAdvisersNames(), DisplayList(tuple(lst)))

    def testGetAdviceInfo(self):
        """
            Produces a dict with some useful info about this advice. This is
            used for indexing purposes (see method updateAdviceIndex in
            MeetingItem.py).
        """
        self.login('pmManager')
        item = self.create('MeetingItem')
        self.setAttributes(item, **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        self.do(item, 'propose')
        self.do(item, 'validate')
        advice = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        self.setAttributes(advice, **{'adviserName':'vendors_advisers'})
        advice_info = advice.getAdviceInfo()
        self.failUnless(advice_info.has_key('agLevel_id'))
        self.assertEquals(advice_info['agLevel_id'], 'positive')
        self.failUnless(advice_info.has_key('adviser_id'))
        self.assertEquals(advice_info['adviser_id'], 'vendors_advisers')
        self.failUnless(advice_info.has_key('uid'))
        self.failUnless(advice_info.has_key('url'))
        self.assertEquals(advice_info['url'], '/plone/Members/pmManager/mymeetings/plonegov-assembly/o1/o2')
        self.failUnless(advice_info.has_key('agLevel_iconUrl'))
        self.assertEquals(advice_info['agLevel_iconUrl'], '/plone/portal_plonemeeting/plonegov-assembly/agreementlevels/positive/theIcon')

    def testAdvicesAutoClose(self):
        """
          When we freeze a meeting, every items are frozen too and every advices of the
          item are closed by the 'doItemFreeze' method...
        """
        self.login('pmManager')
        item = self.create('MeetingItem')
        self.setAttributes(item, **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        meetingDate = DateTime().strftime('%y/%m/%d %H:%M:00')
        meeting = self.create('Meeting', date=meetingDate)
        self.do(item, 'propose')
        self.do(item, 'validate')
        self.do(item, 'present')
        advice = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        advice1 = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        advice2 = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        #test the MeeingItem.getAdvices method here
        self.assertEquals(len(item.getAdvices()), 3)
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice, 'review_state'), 'advicecreated')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice1, 'review_state'), 'advicecreated')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice2, 'review_state'), 'advicecreated')
        #we publish one advice...
        self.do(advice, 'advicePublish')
        #when the meeting is frozen, every items are in the 'itemfrozen' state
        self.do(meeting, 'publish')
        self.do(meeting, 'freeze')
        #and the MeetingAdvices must have been closed...
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice, 'review_state'), 'adviceclosed')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice1, 'review_state'), 'adviceclosed')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice2, 'review_state'), 'adviceclosed')

    def testAdvicesAutoBackToPublished(self):
        """
          When we backToPublish a meeting, every items are corrected back to 'itempublished' state.
          Every contained advices should back from 'adviceclosed' to 'advicepublished' too...
        """
        self.login('pmManager')
        item = self.create('MeetingItem')
        self.setAttributes(item, **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        meetingDate = DateTime().strftime('%y/%m/%d %H:%M:00')
        meeting = self.create('Meeting', date=meetingDate)
        self.do(item, 'propose')
        self.do(item, 'validate')
        self.do(item, 'present')
        advice = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        advice1 = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        advice2 = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'vendors_advisers'})
        #we publish one advice...
        self.do(advice, 'advicePublish')
        #when the meeting is frozen, every items are in the 'itemfrozen' state
        #and the MeetingAdvices must have been closed...
        self.do(meeting, 'publish')
        self.do(meeting, 'freeze')
        #this is tested above
        #now, if we 'backToPublished' the meeting, the contained advices must have been
        #set back from 'closed' to 'advicepublished' too...
        #even if the manager had already set an advice back to 'advicepublished' himself before...
        self.login('admin')
        self.do(advice, 'adviceBackToPublished')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice, 'review_state'), 'advicepublished')
        self.login('pmManager')
        self.do(meeting, 'backToPublished')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice, 'review_state'), 'advicepublished')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice1, 'review_state'), 'advicepublished')
        self.assertEquals(self.portal.portal_workflow.getInfoFor(advice2, 'review_state'), 'advicepublished')

    def testAdvicesSecurity(self):
        """
          Test here the way security about the advices should work...
          Advices must be enabled in the meetingConfig
          A creator create an item and select an optional adviser (a mandatory adviser is auto-selected)
          Check when the adviser can add his advice.
          Check security between advisers of same and different groups
          Check security in different relevant meeting/item/advice states
        """
        #a creator create an item and select advisers
        self.login('pmCreator1')
        item = self.create('MeetingItem')
        self.setAttributes(item, **{'optionalAdvisers':self.meetingConfig.getOptionalAdvisers()})
        #check that the advisers can still not see it and add their advice
        self.login('pmAdviser1')
        self.failIf(self.hasPermission('View', item))
        self.failIf(self.hasPermission('PloneMeeting: Add MeetingAdvice', item))
        #pmReviewer2 is an adviser for developers
        self.login('pmReviewer2')
        self.failIf(self.hasPermission('View', item))
        self.failIf(self.hasPermission('PloneMeeting: Add MeetingAdvice', item))
        #propose the item and check again
        self.login('pmCreator1')
        self.do(item, 'propose')
        self.login('pmAdviser1')
        self.failIf(self.hasPermission('View', item))
        self.failIf(self.hasPermission('PloneMeeting: Add MeetingAdvice', item))
        self.login('pmReviewer2')
        self.failIf(self.hasPermission('View', item))
        self.failIf(self.hasPermission('PloneMeeting: Add MeetingAdvice', item))
        #validate the item and check now that the advisers can see the item
        #and add an advice
        self.login('pmReviewer1')
        self.do(item, 'validate')
        self.login('pmAdviser1')
        self.failUnless(self.hasPermission('View', item))
        self.failUnless(self.hasPermission('PloneMeeting: Add MeetingAdvice', item))
        self.login('pmReviewer2')
        self.failUnless(self.hasPermission('View', item))
        self.failUnless(self.hasPermission('PloneMeeting: Add MeetingAdvice', item))
        self.login('pmManager')
        self.failUnless(self.hasPermission('View', item))
        self.failUnless(self.hasPermission('PloneMeeting: Add MeetingAdvice', item))
        #pmAdviser1 add an advice, check security
        self.login('pmAdviser1')
        advice = self.create('MeetingAdvice', folder=item, **{'agreementLevel':'positive', 'adviserName':'developers_advisers'})
        self.failUnless(self.hasPermission('View', advice))
        self.failUnless(self.hasPermission('Modify portal content', advice))
        #check that pmAdviser2 can not see the advice
        self.login('pmReviewer2')
        self.failIf(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        #check that pmManager can see the advice
        self.login('pmManager')
        self.failUnless(self.hasPermission('View', advice))
        self.failUnless(self.hasPermission('Modify portal content', advice))
        #publish the advice and check security
        self.login('pmAdviser1')
        self.do(advice, 'advicePublish')
        self.failUnless(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        #check wf transitions
        self.failIf(self.transitions(advice))
        #check that pmAdviser2 can now see the advice
        self.login('pmReviewer2')
        self.failUnless(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        self.failIf(self.transitions(advice))
        #check that pmManager can see the advice
        self.login('pmManager')
        self.failUnless(self.hasPermission('View', advice))
        self.failUnless(self.hasPermission('Modify portal content', advice))
        self.failUnless(self.transitions(advice), ['adviceBackToCreated',])
        #check that pmCreator1 can see the advice too
        self.login('pmCreator1')
        self.failUnless(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        self.failIf(self.transitions(advice))
        
        #create a meeting and present the item
        self.login('pmManager')
        meetingDate = DateTime().strftime('%y/%m/%d %H:%M:00')
        meeting = self.create('Meeting', date=meetingDate)
        self.do(item, 'present')
        #now, publish the meeting and freeze it
        self.do(meeting, 'publish')
        self.do(meeting, 'freeze')
        #the advices are in the 'adviceclosed' state, check security
        self.login('pmAdviser1')
        self.failUnless(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        self.failIf(self.transitions(advice))
        self.login('pmReviewer2')
        self.failUnless(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        self.failIf(self.transitions(advice))
        self.login('pmManager')
        self.failUnless(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        self.failIf(self.transitions(advice))
        self.login('pmCreator1')
        self.failUnless(self.hasPermission('View', advice))
        self.failIf(self.hasPermission('Modify portal content', advice))
        self.failIf(self.transitions(advice))
        
 
def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeetingAdvice))
    return suite
