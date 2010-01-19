# -*- coding: utf-8 -*-
#
# File: testToolPloneMeeting.py
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

from Products.PloneMeeting.tests.PloneMeetingTestCase import \
    PloneMeetingTestCase

class testToolPloneMeeting(PloneMeetingTestCase):
    '''Tests the ToolPloneMeeting class methods.'''
    def afterSetUp(self):
        PloneMeetingTestCase.afterSetUp(self)

    def testGetMeetingGroup(self):
        '''Return the meeting group containing the plone group
           p_ploneGroupId.'''
        meetingGroup = self.tool.getMeetingGroup('developers_advisers')
        self.assertEquals(meetingGroup.id, 'developers')

    def testMoveMeetingGroups(self):
        '''Tests changing MeetingGroup and MeetingConfig order within the tool.
           This is more coplex than it seems at first glance because groups and
           configs are mixed together within the tool.'''
        self.login('admin')
        # Create a new MeetingGroup
        newGroup = self.create('MeetingGroup', title='NewGroup', acronym='N.G.')
        self.tool.REQUEST['template_id'] = '.'
        self.tool.folder_position(position='up', id=newGroup.id,template_id='.')
        self.assertEquals(self.tool.objectIds()[1:5],
                          ['developers', 'vendors', 'o1', 'endUsers'])

    def testCloneItem(self):
        '''Clones a given item in parent item folder.'''
        tool = self.tool
        self.login('pmManager')
        item1 = self.create('MeetingItem')
        workingFolder = item1.getParentNode()
        clonedItem = item1.clone()
        self.assertEquals(
            set([item1, clonedItem]), set(workingFolder.objectValues()))
        # Test that an item viewable by a different user (another member of the
        # same group) can be pasted too. item1 is viewable by pmCreator1 too.
        self.login('pmCreator1')
        clonedItem = item1.clone()
        # The item is cloned in the pmCreator1 personnal folder.
        self.assertEquals(
            set([clonedItem]), set(clonedItem.getParentNode().objectValues()))

    def testCloneItemWithContent(self):
        '''Clones a given item containing annexes in parent item folder.'''
        tool = self.tool
        self.login('pmManager')
        item1 = self.create('MeetingItem')
        # Add one annex
        self.addAnnex(item1)
        # Add one annex that is decision related
        self.addAnnex(item1, decisionRelated=True)
        workingFolder = item1.getParentNode()
        clonedItem = item1.clone()
        self.assertEquals(
            set([item1, clonedItem]), set(workingFolder.objectValues()))
        # Check that the annexes have been cloned, too.
        self.assertEquals(len(clonedItem.getAnnexes()), 1)
        self.assertEquals(len(clonedItem.getAnnexesDecision()), 1)
        # The annexIndex must be filled
        self.assertEquals(len(clonedItem.annexIndex), 2)
        # The adviceIndex should contain the users specified in optional and
        # mandatory advisers.
        self.assertEquals(len(clonedItem.adviceIndex.keys()),
            len(clonedItem.getOptionalAdvisers()) +
            len(clonedItem.getMandatoryAdvisers()))
        # Test that an item viewable by a different user (another member of the
        # same group) can be pasted too if it contains things. item1 is viewable
        # by pmCreator1 too. And Also tests cloning without annex copying.
        self.login('pmCreator1')
        clonedItem = item1.clone(copyAnnexes=False)
        self.assertEquals(set([clonedItem]),
            set(clonedItem.getParentNode().objectValues()))
        self.assertEquals(len(clonedItem.getAnnexes()), 0)
        self.assertEquals(len(clonedItem.getAnnexesDecision()), 0)

    def testCloneItemWithContentNotRemovableByPermission(self):
        '''Clones a given item in parent item folder. Here we test that even
           if the contained objects are not removable, they are removed.
           Now we use removeGivenObject to remove contained objects of
           copied items.'''
        tool = self.tool
        self.login('pmCreator1')
        item = self.create('MeetingItem')
        # Add one annex
        self.addAnnex(item)
        # Now, validate the item. In this state, annexes are not removable.
        self.do(item, 'propose')
        self.changeUser('pmReviewer1')
        self.do(item, 'validate')
        self.login('pmCreator1')
        clonedItem = item.clone()
        # The item is cloned in the pmCreator1 personal folder. We should
        # have now two elements in the folder
        self.assertTrue(hasattr(clonedItem.getParentNode(), 'o1'))
        self.assertTrue(hasattr(clonedItem.getParentNode(), 'copy_of_o1'))

    def testPasteItems(self):
        '''Paste objects (previously copied) in destFolder.'''
        tool = self.tool
        self.login('pmManager')
        item1 = self.create('MeetingItem')
        item2 = self.create('MeetingItem')
        destFolder = item1.getParentNode()
        copiedData = destFolder.manage_copyObjects(ids=[item1.id, item2.id, ])
        res = tool.pasteItems(destFolder, copiedData)
        self.assertEquals(set([item1, item2, res[0], res[1]]),
                          set(destFolder.objectValues()))

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(testToolPloneMeeting))
    return suite
