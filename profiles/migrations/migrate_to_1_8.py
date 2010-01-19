# ------------------------------------------------------------------------------
from persistent.list import PersistentList
from Products.PloneMeeting.profiles.migrations import Migrator
from Products.PloneMeeting.config import *
import logging
logger = logging.getLogger('PloneMeeting')

# The migration class ----------------------------------------------------------
class Migrate_To_1_8(Migrator):
    def __init__(self, context):
        Migrator.__init__(self, context)

    def _addItemHistory(self):
        '''This method adds a persistent list on every item for storing item
           history.'''
        logger.info('Adds on every item the persistent list that stores item ' \
                    'history.')
        brains = self.portal.portal_catalog(meta_type='MeetingItem')
        for brain in brains:
            item = brain.getObject()
            modifDate = item.modification_date
            # Creates the persistent list
            if not hasattr(item.aq_base, 'itemHistory'):
                item.itemHistory = PersistentList()
            item.setModificationDate(modifDate)
            # We ensure that the modification date of items has not changed
            # due to these maintenance-related changes.

    def run(self):
        self.reinstall()
        self._addItemHistory()
        #self.refreshDatabase(catalogs=True, workflows=True)
        logger.info('Migration finished.')

# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function does the following things:

       0) Reinstall PloneMeeting;
       1) Adds a persistent list on every item for storing item's history.'''
    Migrate_To_1_8(context).run()
# ------------------------------------------------------------------------------
