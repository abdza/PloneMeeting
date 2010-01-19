# ------------------------------------------------------------------------------
from persistent.mapping import PersistentMapping
from Products.PloneMeeting.profiles.migrations import Migrator
from Products.PloneMeeting.config import *
import logging
logger = logging.getLogger('PloneMeeting')

# The migration class ----------------------------------------------------------
class Migrate_To_1_7(Migrator):
    def __init__(self, context):
        Migrator.__init__(self, context)

    def _addMeetingUsersFolder(self):
        logger.info('Adding a folder in every meeting config for storing ' \
                    'meeting users.')
        folderId = TOOL_FOLDER_MEETING_USERS
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            if hasattr(meetingConfig, folderId): continue
            meetingConfig.invokeFactory('Folder', folderId)
            folder = getattr(meetingConfig, folderId)
            folder.setTitle(folderId.capitalize())
            folder.setConstrainTypesMode(1)
            folder.setLocallyAllowedTypes(['MeetingUser'])
            folder.setImmediatelyAddableTypes(['MeetingUser'])
            folder.reindexObject()

    def _removeMandatoryAdvisersAttributeFromConfigs(self):
        logger.info('Removing useless mandatoryAdvisers attribute ' \
                    'from meeting configurations.')
        folderId = TOOL_FOLDER_MEETING_USERS
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            if not hasattr(meetingConfig, 'mandatoryAdvisers'): continue
            delattr(meetingConfig, 'mandatoryAdvisers')
            logger.info('\'mandatoryAdvisers\' attribute removed for ' \
                        'meeting configuration \'%s\'.' % meetingConfig.getId())

    def _removeAnnexIndexFromCatalog(self):
        '''annexIndex appears sometimes in portal_catalog without any known
           reason.'''
        pc = self.portal.portal_catalog
        if 'annexIndex' in pc.schema():
            logger.info('Removing annexIndex from portal_catalog schema...')
            pc.manage_delColumn(['annexIndex'])

    def _updateItemsVotesAndAdvices(self):
        '''This method performs the following changes on every item:
           - adds the dict for votes;
           - updates the advice index.'''
        logger.info('Adds on every item the dictionary that stores votes and ' \
                    'updates the advice index.')
        brains = self.portal.portal_catalog(meta_type='MeetingItem')
        for brain in brains:
            item = brain.getObject()
            modifDate = item.modification_date
            # Creates the votes dict
            if not hasattr(item.aq_base, 'votes'):
                item.votes = PersistentMapping()
            # Updates the advice index
            item.updateAdviceIndex()
            item.setModificationDate(modifDate)
            # We ensure that the modification date of items has not changed
            # due to these maintenance-related changes.

    def _addNewTopics(self):
        '''One new topic has to be added in each meetingConfig '''
        logger.info('Adding new topic...')
        topicsInfo = (
         ( 'searchalladviseditems',
         (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
         ), 'created', 'searchAdvisedItems',
            "python: here.portal_plonemeeting.userIsAmong('advisers')"
         ),
        )
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            for topicId, topicCriteria, sortCriterion, searchScriptId, \
                topic_tal_expr in topicsInfo:
                if hasattr(meetingConfig.topics, topicId):
                    continue
                meetingConfig.topics.invokeFactory('Topic', topicId)
                topic = getattr(meetingConfig.topics, topicId)
                topic.setExcludeFromNav(True)
                topic.setTitle(topicId)
                mustAddStateCriterium = False
                for criterionName, criterionType, criterionValue in \
                    topicCriteria:
                    criterion = topic.addCriterion(field=criterionName,
                                                criterion_type=criterionType)
                    if criterionValue != None:
                        if criterionType == 'ATPortalTypeCriterion':
                            if criterionValue in ('MeetingItem', 'Meeting'):
                                mustAddStateCriterium = True
                            topic.manage_addProperty(
                                TOPIC_TYPE, criterionValue, 'string')
                            # We need to add a script doing the search
                            # when it is too complicated for a topic
                            topic.manage_addProperty(
                                TOPIC_SEARCH_SCRIPT, searchScriptId, 'string')
                            # Add a tal expression property
                            topic.manage_addProperty(
                                TOPIC_TAL_EXPRESSION, topic_tal_expr, 'string')
                            criterionValue = '%s%s' % \
                                (criterionValue, meetingConfig.getShortName())
                        criterion.setValue([criterionValue])
                if mustAddStateCriterium:
                    # We must add a state-related criterium. But for an item
                    # or meeting-related topic ?
                    getStatesMethod = meetingConfig.getItemTopicStates
                    stateCriterion = topic.addCriterion(
                        field='review_state', criterion_type='ATListCriterion')
                    stateCriterion.setValue(getStatesMethod())
                topic.setLimitNumber(True)
                topic.setItemCount(20)
                topic.setSortCriterion(sortCriterion, True)
                topic.setCustomView(True)
                topic.setCustomViewFields(['Title', 'CreationDate', 'Creator',
                                        'review_state'])
                topic.reindexObject()            

    def run(self):
        self._addMeetingUsersFolder()
        self._removeMandatoryAdvisersAttributeFromConfigs()
        self._updateItemsVotesAndAdvices()
        self._removeAnnexIndexFromCatalog()
        self._addNewTopics()
        self.refreshDatabase(catalogs=True, workflows=True)
        logger.info('Migration finished.')

# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function does the following things:

       1) Adds the "meetingusers" folder to every meeting config;
       2) Adds the dict for storing votes on every meeting item and updates
          the advice index;
       3) Removes annexIndex from portal_catalog;
       4) Remove attribute "Mandatory advisers" from every meeting config;
       5) Add a new advice-related topic.'''
    Migrate_To_1_7(context).run()
# ------------------------------------------------------------------------------
