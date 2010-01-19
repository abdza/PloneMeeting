# ------------------------------------------------------------------------------
import os.path
from Products.CMFCore.utils import getToolByName
from Products.PloneMeeting.profiles.migrations import Migrator
from Products.PloneMeeting.config import TOOL_FOLDER_AGREEMENT_LEVELS, \
                                         TOOL_FOLDER_POD_TEMPLATES
import logging
logger = logging.getLogger('PloneMeeting')

# The migration class ----------------------------------------------------------
class Migrate_To_1_4(Migrator):
    def __init__(self, context):
        Migrator.__init__(self, context)

    newFolders = {
       TOOL_FOLDER_AGREEMENT_LEVELS: ('Meeting advices agreement levels',
                                      'MeetingAdviceAgreementLevel'),
       TOOL_FOLDER_POD_TEMPLATES: ('POD templates', 'PodTemplate')
    }
    def _createNewConfigFolders(self):
        '''Creates the new folders every 1.4-compliant meeting config must
           have, for storing advices and POD templates.'''
        logger.info('Create new meeting config sub-folders...')
        # Within meeting configs, create folders for storing advice agreements
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            for folderId, folderInfo in self.newFolders.iteritems():
                meetingConfig.invokeFactory('Folder', folderId)
                subFolder = getattr(meetingConfig, folderId)
                subFolder.setTitle(folderInfo[0])
                subFolder.setConstrainTypesMode(1)
                subFolder.setLocallyAllowedTypes([folderInfo[1]])
                subFolder.setImmediatelyAddableTypes([folderInfo[1]])
                subFolder.reindexObject()
        logger.info('Done.')

    def _createAdviceGroups(self):
        logger.info('Adding "advice" groups for every MeetingGroup...')
        # For every MeetingGroup, create the additional Plone group "_advisers"
        for meetingGroup in self.tool.objectValues('MeetingGroup'):
            meetingGroup._createPloneGroup('advisers')
        logger.info('Done.')

    itemOrMeeting = {True:'MeetingItem', False:'Meeting'}
    def _createPodTemplate(self, meetingConfig, fileContent, docFormat,
                           fileType, forItem=True, freezeOnArchive=False):
        podTemplatesFolder = getattr(meetingConfig, TOOL_FOLDER_POD_TEMPLATES)
        # Determine id of the pod template
        podId = fileType
        if hasattr(podTemplatesFolder, fileType):
            podId = fileType + docFormat[0].upper() + docFormat[1:]
        podTemplatesFolder.invokeFactory('PodTemplate', id=podId)
        podTemplate = getattr(podTemplatesFolder, podId)
        podTemplate.setTitle(os.path.splitext(fileContent.filename)[0])
        podTemplate.setPodTemplate(fileContent)
        podTemplate.setPodFormat(docFormat)
        podTemplate.setPodCondition('python:here.meta_type=="%s"' % \
                                    self.itemOrMeeting[forItem])
        if freezeOnArchive:
            if forItem:
                freezeEvent = 'pod_item_itemarchive'
            else:
                freezeEvent = 'pod_meeting_archive'
            podTemplate.setFreezeEvent(freezeEvent)

    itemFileTypes = ('itemDocDescriptionTemplate', 'itemDocDecisionTemplate')
    meetingFileTypes = ('meetingDocAgendaTemplate',
                        'meetingDocDecisionsTemplate')
    docFormats = ('doc', 'pdf', 'rtf', 'odt')
    def _convertPodTemplates(self):
        logger.info('Converting POD templates...')
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            itemFreeze = meetingConfig.exportIndividualDecisionsAsFiles
            meetingFreeze = meetingConfig.exportAllDecisionsAsFile
            for docFormat in meetingConfig.itemDocFormats:
                for fileType in self.itemFileTypes:
                    exec 'fileContent = meetingConfig.%s' % fileType
                    if fileContent.size:
                        # I must create the corresponding PodTemplate
                        self._createPodTemplate(meetingConfig, fileContent,
                                                docFormat, fileType,
                                                forItem=True,
                                                freezeOnArchive=itemFreeze)
            for docFormat in meetingConfig.meetingDocFormats:
                for fileType in self.meetingFileTypes:
                    exec 'fileContent = meetingConfig.%s' % fileType
                    if fileContent.size:
                        # I must create the corresponding PodTemplate
                        self._createPodTemplate(meetingConfig, fileContent,
                                                docFormat, fileType,
                                                forItem=False,
                                                freezeOnArchive=meetingFreeze)
            # Remove previous actions on Meeting and MeetingItem content types
            # for this meeting configuration.
            typesTool = self.portal.portal_types
            itemCt = getattr(typesTool, meetingConfig.getItemTypeName())
            meetingCt = getattr(typesTool, meetingConfig.getMeetingTypeName())
            elems = ('item', 'meeting')
            i = -1
            for contentType in (itemCt, meetingCt):
                i += 1
                actionstoDelete = []
                actionIds = ['%s_%s' % (elems[i], f) for f in self.docFormats]
                allActions = list(contentType.listActions())
                for actionInfo in allActions:
                    if actionInfo.id in actionIds:
                        actionstoDelete.append(allActions.index(actionInfo))
                contentType.deleteActions(actionstoDelete)
        logger.info('Done.')

    def _upgradeColorSystemConfig(self):
        logger.info('Upgrading color system configuration...')
        if self.tool.enableColorSystem:
            self.tool.setUsedColorSystem('modification_color')
        logger.info('Done.')

    def _convertSortItemOrder(self):
        '''Convert field "followCategoryOrderOnAddItem" to
           "sortingMethodOnAddItem".'''
        logger.info('Convert insert item method...')
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            atTheEnd = not meetingConfig.followCategoryOrderOnAddItem
            if atTheEnd:
                newMethod = 'at_the_end'
            else:
                if meetingConfig.getUseGroupsAsCategories():
                    newMethod = 'on_proposing_groups'
                else:
                    newMethod = 'on_categories'
            meetingConfig.setSortingMethodOnAddItem(newMethod)
        logger.info('Done.')

    def run(self):
        self._createNewConfigFolders()
        self._createAdviceGroups()
        self._convertPodTemplates()
        self._upgradeColorSystemConfig()
        self._convertSortItemOrder()
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
    '''This migration function does the following things:

       1) Updates meeting configs with data necessary for using the 'advices'
          system.'''
    Migrate_To_1_4(context).run()
# ------------------------------------------------------------------------------
