# ------------------------------------------------------------------------------
import os.path
from Products.CMFCore.utils import getToolByName
from Products.PloneMeeting.profiles.migrations import Migrator
from Products.PloneMeeting.config import *
from Products.CMFCore import permissions

import logging
logger = logging.getLogger('PloneMeeting')

# The migration class ----------------------------------------------------------
class Migrate_To_1_6(Migrator):
    def __init__(self, context):
        Migrator.__init__(self, context)

    def _addClassifiersFolder(self):
        logger.info('Adding a folder in every meeting config for storing ' \
                    'classifiers.')
        folderId = 'classifiers'
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            if hasattr(meetingConfig, folderId): continue
            meetingConfig.invokeFactory('Folder', folderId)
            folder = getattr(meetingConfig, folderId)
            folder.setTitle(folderId.capitalize())
            folder.setConstrainTypesMode(1)
            folder.setLocallyAllowedTypes(['MeetingCategory'])
            folder.setImmediatelyAddableTypes(['MeetingCategory'])
            folder.reindexObject()

    def _removePloneMeetingRemovers(self):
        logger.info("Correcting 'Delete objects' permission on every " \
                     "user meeting folders...")
        # Elderly we had to define removers to be able to remove an item
        # because the removal process was linked to the "Delete objects"
        # permission of the parent (by default in Plone). Now that we monkey
        # patched manage_delObjects in the Tool, the security is located on the
        # element itself and we have to remove what we set on containers...
        # just remove everything about "Delete objects" permission on every
        # meetingConfigFolders of every users...
        # if everything is OK, we can remove every meetingFolders...
        members = self.portal.portal_membership.getMembersFolder()
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            meetingFolderId = meetingConfig.getId()
            for member in members.objectValues():
                # Get the right meetingConfigFolder
                if hasattr(member, ROOT_FOLDER):
                    root_folder = getattr(member, ROOT_FOLDER)
                    if hasattr(root_folder, meetingFolderId):
                        # We found the right folder
                        folder = getattr(root_folder, meetingFolderId)
                        # Set the "Delete objects" permission to acquire
                        folder.manage_permission(
                         permissions.DeleteObjects, [], acquire=1)

    def _adaptLeftSlotForPortletTodo(self):
        # Adapt the left_slots property at the root of the Plone Site
        # We will insert it at the top of left_slots
        from types import TupleType
        left_slots = self.portal.getProperty('left_slots', None)
        # Check that we have a property of type "list"
        if type(left_slots) == TupleType:
            res = list(left_slots)
            portlet_todo_macro = "here/portlet_todo/macros/portlet"
            if not portlet_todo_macro in res:
                logger.info("Adapting 'left_slots' to take 'portlet_todo' " \
                            "into account")
                res.insert(0, portlet_todo_macro)
                self.portal.manage_changeProperties(left_slots=res)
            else:
                logger.warning("'portlet_todo' already in 'left_slots', " \
                               "nothing done!")
        else:
            logger.error("No correct 'left_slots' found at the root of " \
                         "the Plone Site!")

    def run(self):
        self._addClassifiersFolder()
        self._removePloneMeetingRemovers()
        self._adaptLeftSlotForPortletTodo()
        self.refreshDatabase()
        logger.info('Migration finished.')

# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function does the following things:

       1) Adds the "classifiers" folder to every meeting config.
       2) Remove the list of roles noted as ploneMeetingRemovers on meeting
          config folders.
       3) Add the "Todo" portlet to left_slots.'''
    Migrate_To_1_6(context).run()
# ------------------------------------------------------------------------------
