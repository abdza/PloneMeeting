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


from DateTime import DateTime
from Products.PloneMeeting.config import *
from Products.PloneMeeting.tests.PloneMeetingTestCase import \
    PloneMeetingTestCase

class testMeeting(PloneMeetingTestCase):
    '''Tests various aspects of Meetings management.'''

    def _createMeetingWithItems(self):
        '''Create a meeting with a bunch of items.'''
        meetingDate = DateTime().strftime('%y/%m/%d %H:%M:00')
        meeting = self.create('Meeting', date=meetingDate)
        item1 = self.create('MeetingItem') # id=o2
        item1.setProposingGroup('vendors')
        item1.setAssociatedGroups(('developers',))
        item2 = self.create('MeetingItem') # id=o3
        item2.setProposingGroup('developers')
        item3 = self.create('MeetingItem') # id=o4
        item3.setProposingGroup('vendors')
        item4 = self.create('MeetingItem') # id=o5
        item4.setProposingGroup('developers')
        item5 = self.create('MeetingItem') # id=o6
        item5.setProposingGroup('vendors')
        for item in (item1, item2, item3, item4, item5):
            self.do(item, 'propose')
            self.do(item, 'validate')
            self.do(item, 'present')
        return meeting

    def testInsertItem(self):
        '''Tests that items are inserted at the right place into the meeting.
           In the test profile, groups order is like this:
           1) developers
           2) vendors
           Sort methods are defined this way:
           a) plonegov-assembly: on_categories
              (with useGroupsAsCategories=True);
           b) plonemeeting-assembly: on_proposing_groups.

           sort methods tested here are "on_categories" and
           "on_proposing_groups".'''
        self.login('pmManager')
        for meetingConfig in ('plonegov-assembly', 'plonemeeting-assembly'):
            self.setMeetingConfig(meetingConfig)
            meeting = self._createMeetingWithItems()
            self.assertEquals([item.id for item in meeting.getItemsInOrder()],
                              ['o3', 'o5', 'o2', 'o4', 'o6'])

    def testInsertItemAllGroups(self):
        '''Sort method tested here is "on_all_groups".'''
        self.login('pmManager')
        self.meetingConfig.setSortingMethodOnAddItem('on_all_groups')
        meeting = self._createMeetingWithItems()
        self.assertEquals([item.id for item in meeting.getItemsInOrder()],
                            ['o3', 'o5', 'o2', 'o4', 'o6'])

    def testRemoveOrDeleteLinkedItem(self):
        '''Test that removing or deleting a linked item works.'''
        self.login('pmManager')
        meeting = self._createMeetingWithItems()
        self.assertEquals([item.id for item in meeting.getItemsInOrder()],
                            ['o3', 'o5', 'o2', 'o4', 'o6'])
        #remove an item
        item5 = getattr(meeting, 'o5')
        meeting.removeItem(item5)
        self.assertEquals([item.id for item in meeting.getItemsInOrder()],
                            ['o3', 'o2', 'o4', 'o6'])
        #delete a linked item
        item4 = getattr(meeting, 'o4')
        meeting.delete_givenuid(item4.UID())
        self.assertEquals([item.id for item in meeting.getItemsInOrder()],
                            ['o3', 'o2', 'o6'])

    def testMeetingNumbers(self):
        '''Tests that meetings receive correctly their numbers from the config
           when they are published.'''
        self.login('pmManager')
        m1 = self._createMeetingWithItems()
        self.assertEquals(self.meetingConfig.getLastMeetingNumber(), 0)
        self.assertEquals(m1.getMeetingNumber(), -1)
        self.do(m1, 'publish')
        self.assertEquals(m1.getMeetingNumber(), 1)
        self.assertEquals(self.meetingConfig.getLastMeetingNumber(), 1)
        m2 = self._createMeetingWithItems()
        self.do(m2, 'publish')
        self.assertEquals(m2.getMeetingNumber(), 2)
        self.assertEquals(self.meetingConfig.getLastMeetingNumber(), 2)

    def testAvailableItems(self):
        """
          By default, available items should be :
          - validated items
          - with no preferred meeting
          - items for wich the preferredMeeting is not a future meeting
        """
        #create 3 meetings
        #we can do every steps as a MeetingManager
        self.login('pmManager')
        meetingDate = DateTime('2008/06/12 08:00:00')
        m1 = self.create('Meeting', date=meetingDate)
        meetingDate = DateTime('2008/06/19 08:00:00')
        m2 = self.create('Meeting', date=meetingDate)
        meetingDate = DateTime('2008/06/26 08:00:00')
        m3 = self.create('Meeting', date=meetingDate)
        #create 3 items
        #one with no preferredMeeting
        #one with m2 preferredMeeting
        #one with m3 as preferredMeeting
        i1 = self.create('MeetingItem')
        i1.setTitle('i1')
        i1.reindexObject()
        i2 = self.create('MeetingItem')
        i2.setPreferredMeeting(m2.UID())
        i2.setTitle('i2')
        i2.reindexObject()
        i3 = self.create('MeetingItem')
        i3.setPreferredMeeting(m3.UID())
        i3.setTitle('i3')
        i3.reindexObject()
        #for now, no items are presentable...
        self.assertEquals(len(m1.getAvailableItems()), 0)
        self.assertEquals(len(m2.getAvailableItems()), 0)
        self.assertEquals(len(m3.getAvailableItems()), 0)
        ##propose and validate the items
        self.do(i1, 'propose')
        self.do(i1, 'validate')
        self.do(i2, 'propose')
        self.do(i2, 'validate')
        self.do(i3, 'propose')
        self.do(i3, 'validate')
        #now, check that available items have some respect
        #the first meeting has only one item, the one with no preferred meeting selected
        itemTitles = []
        for brain in m1.getAvailableItems():
            itemTitles.append(brain.Title)
        self.assertEquals(itemTitles, ['i1', ])
        #the second meeting has 2 items, the no preferred meeting one and the i2
        #for wich we selected this meeting as preferred
        itemTitles = []
        for brain in m2.getAvailableItems():
            itemTitles.append(brain.Title)
        self.assertEquals(itemTitles, ['i1', 'i2', ])
        #the third has 3 items
        #--> no preferred meeting item
        #--> the second item because the meeting date is in the future
        #--> the i3 where we selected m3 as preferred meeting
        itemTitles = []
        for brain in m3.getAvailableItems():
            itemTitles.append(brain.Title)
        self.assertEquals(itemTitles, ['i1', 'i2', 'i3', ])

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testMeeting))
    return suite
