# ------------------------------------------------------------------------------
import os.path
from Products.CMFCore.utils import getToolByName
from Products.PloneMeeting.profiles.migrations import Migrator
from Products.PloneMeeting.config import *
import logging
logger = logging.getLogger('PloneMeeting')

# The migration class ----------------------------------------------------------
class Migrate_To_1_5(Migrator):
    def __init__(self, context):
        Migrator.__init__(self, context)

    def _adaptPortalTypes(self):
        logger.info('Adapt existing MeetingItem portal types')
        registeredFactoryTypes = self.portal.portal_factory.getFactoryTypes(
            ).keys()
        basePortalType = getattr(self.portal.portal_types, 'MeetingItem')
        for portalTypeName in registeredFactoryTypes:
            if not portalTypeName.startswith('MeetingItem') or \
               (portalTypeName == 'MeetingItem'):
                continue
            logger.info('Adding actions on %s'%portalTypeName)
            portalType = getattr(self.portal.portal_types, portalTypeName)
            # Copy actions from the base portal type
            portalType._actions = tuple(basePortalType._cloneActions())
            portalType.manage_changeProperties(allowed_content_types = \
                ['MeetingFile', 'MeetingAdvice'])

    def _updateMeetingItems(self):
        logger.info('Adapt existing meeting items')
        brains = self.portal.portal_catalog(meta_type='MeetingItem')
        for brain in brains:
            item = brain.getObject()
            item.updateAdviceIndex()

    def _updatePloneMeetingUpdaters(self):
        '''Remove 'Member' from the roles able to add files...'''
        logger.info('Set PloneMeetingUpdaters...')
        allRelevantGroupIds = []
        #this property was taken from config.py for this method to work
        #but it has now disappeared...
        #this functionality is removed by migrate_to_1_6
        ploneMeetingRemovers = ('MeetingManager', 'Manager', 'Owner', 'Member')
        for meetingGroup in self.tool.objectValues('MeetingGroup'):
            for suffix in MEETINGROLES.iterkeys():
                allRelevantGroupIds.append(meetingGroup.getPloneGroupId(suffix))
        logger.info('Relevant group ids are: ' + str(allRelevantGroupIds))

        pm = self.portal.portal_membership
        for userId in pm.listMemberIds():
            memberFolder = pm.getHomeFolder(userId)
            if memberFolder is None:
                continue
            myMeetingsFolder = getattr(memberFolder.aq_inner, ROOT_FOLDER, None)
            if myMeetingsFolder is None:
                continue
            # Update permissions on every meetingConfig folder
            for configFolder in myMeetingsFolder.objectValues():
                p = configFolder.manage_permission
                p('Delete objects', ploneMeetingRemovers, acquire=0)
                p('ATContentTypes: Add File', ploneMeetingUpdaters, acquire=0)
        logger.info('Done.')

    def _addNewTopics(self):
        ''' 2 new topics have to be added in each meetingConfig '''
        logger.info('Adding new topics...')
        #one for items in copy
        #one for items to advice
        topicsInfo = (
         # Items in copy : need a script to do this search...
         ( 'searchallitemsincopy',
         (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
         ), 'created', 'searchItemsInCopy',
            "python: here.portal_plonemeeting.getMeetingConfig(here)." \
            "getUseCopies()"
         ),
         # Items to advice : need a script to do this search...
         ( 'searchallitemstoadvice',
         (  ('Type', 'ATPortalTypeCriterion', 'MeetingItem'),
         ), 'created', 'searchItemsToAdvice',
            "python: here.portal_plonemeeting.userIsAmong('advisers')"
         ),
        )
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            for topicId, topicCriteria, sortCriterion, searchScriptId, \
                topic_tal_expr in topicsInfo:
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

    def _addDefaultMeetingAdviceAgreementLevels(self):
        ''' Add some default MeetingAdviceAgreementLevels in the existing
            meetingConfigs '''
        logger.info('Adding default agreement levels...')
        # AgremmentLevels
        agreementLevelsInfo = (
            ('positive', 'Positive', 'positive.png'),
            ('remarks', 'Positive with remarks', 'remarks.png'),
            ('negative', 'Negative', 'negative.png'),
           )
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            agreementLevelsFolder = getattr(meetingConfig, 'agreementlevels')
            if agreementLevelsFolder.objectValues("MeetingAdviceAgreementLevel"):
                continue
            for alId, alTitle, alIcon in agreementLevelsInfo:
                #take images from the 'test' profile
                #change the last element of the path from 'migration' to 'test'
                iconPath = '%s/images/%s' % (self._profile_path.replace(
                    'migrations', 'test'), alIcon)
                iconFile = file(iconPath, 'rb')
                iconContent = iconFile.read()
                agreementLevelsFolder.invokeFactory(
                    'MeetingAdviceAgreementLevel', alId, title=alTitle,
                    theIcon=iconContent)
                iconFile.close()

    def _updateTopics(self):
        '''Add the TOPIC_TAL_EXPRESSION property on existing topics and define
           if possible.'''
        logger.info('Updating existing topics...')
        topicsInfo = {
            # My items
            'searchmyitems': "python: here.portal_plonemeeting.userIsAmong" \
                             "('creators')",
            # All (visible) items
            'searchallitems': '',
            # All not-yet-decided meetings
            'searchallmeetings': '',
            # All decided meetings
            'searchalldecisions': '',
            }
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            # Walk every 'topics' folder and see if some topics need to be
            # updated.
            topics = meetingConfig.topics
            for topicInfo in topicsInfo:
                if hasattr(topics, topicInfo):
                    #we have a corresponding topic, update it!
                    logger.info('Updating %s...' % topicInfo)
                    topic = getattr(topics, topicInfo)
                    topic.manage_addProperty(
                        TOPIC_TAL_EXPRESSION, topicsInfo[topicInfo], 'string')

    def run(self):
        self._adaptPortalTypes()
        self._updateMeetingItems()
        self._updatePloneMeetingUpdaters()
        self._addNewTopics()
        self._updateTopics()
        self._addDefaultMeetingAdviceAgreementLevels()
        logger.info('Updating security settings...')
        self.portal.portal_workflow.updateRoleMappings()
        # Refresh catalogs
        logger.info('Recataloging...')
        self.portal.portal_catalog.refreshCatalog(clear=0)
        self.portal.reference_catalog.refreshCatalog(clear=0)
        self.portal.uid_catalog.refreshCatalog(clear=0)
        logger.info('Migration finished.')

# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function adapts the PloneMeeting database for managing
       advices.'''
    Migrate_To_1_5(context).run()
# ------------------------------------------------------------------------------
