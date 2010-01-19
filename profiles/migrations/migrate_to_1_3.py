# ------------------------------------------------------------------------------
from Products.CMFCore.utils import getToolByName
from BTrees.OOBTree import OOBTree
from DateTime import DateTime
from persistent.list import PersistentList
from Products.PloneMeeting.config import MEETINGROLES, ROOT_FOLDER, \
                                         ploneMeetingUpdaters, \
                                         ADD_CONTENT_PERMISSIONS
from Products.PloneMeeting.profiles.migrations import Migrator
import logging
logger = logging.getLogger('PloneMeeting')

# The migration class ----------------------------------------------------------
class Migrate_To_1_3(Migrator):
    def __init__(self, context):
        Migrator.__init__(self, context)
        self.brains = self.portal.portal_catalog(meta_type='MeetingItem')

    def _updateItemsOwnerShip(self):
        '''Change owner of recurring items.
           A Manager has created these items in portal_plonemeeting and owns them.
           After copying recurring items to the folder containing the target
           meeting, we look for the items the creator of the recurring items has
           created, change the owner to the owner of the container if different
           look for the owner of the recurring items.'''
        admin_creators = []
        logger.info("Creating the list of Managers...")
        # Create a list of admins that created items in portal_plonemeeting
        for meetingConfig in self.tool.objectValues('MeetingConfig'):
            recurringitems = getattr(meetingConfig.aq_base, 'recurringitems', None)
            if recurringitems:
                for item in recurringitems.objectValues():
                    if item.getOwner() not in admin_creators:
                        logger.info("Add %s" % str(item.Creator()))
                        admin_creators.append(item.Creator())
                    # We update each recurring item to add the pm_modification_date attribute.
                    # This is done for each catalogued item (in "_moveAnnexes" method) 
                    #   but recurring items are not catalogued.
                    item.pm_modification_date = item.modification_date
        logger.info("Done.")

        logger.info('Changing ownership of items generated from recurring items...')
        for brain in self.brains:
            item = brain.getObject()
            if brain.Creator in admin_creators:
                container = item.getParentNode()
                if container.getOwner() is not item.getOwner() and \
                   not item.isDefinedInTool():
                    # if the owner of the item is not the owner of the container,
                    # we change the owner it is most than probable that this is a
                    # recurring item copyied from the config.
                    new_owner = container.getOwner().getId()
                    logger.info("Changing owner of %s from %s to %s" % (
                        item, item.getOwner(), new_owner))
                    self.portal.plone_utils.changeOwnershipOf(item, new_owner)
                    item.setCreators(new_owner)
        logger.info('Done.')

    def _updateLocalRoles(self):
        '''Removes local roles from "mymeetings" folders and sets local roles
           on items themselves.'''
        # Remove local roles from 'mymeetings' folders
        logger.info('Removing local roles on "mymeetings" folders...')
        allRelevantGroupIds = []
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
            toRemove = []
            for principalId, localRoles in myMeetingsFolder.get_local_roles():
                if (principalId in allRelevantGroupIds):
                    toRemove.append(principalId)
            myMeetingsFolder.manage_delLocalRoles(toRemove)
            # Update permissions on every meetingConfig folder
            for configFolder in myMeetingsFolder.objectValues():
                p = configFolder.manage_permission
                p('Add portal content', ('Owner',), acquire=0)
                p('Delete objects', ploneMeetingUpdaters, acquire=0)
                p(ADD_CONTENT_PERMISSIONS['MeetingItem'], ('Owner',), acquire=0)
                p(ADD_CONTENT_PERMISSIONS['Meeting'], ('MeetingManager',),
                  acquire=0)
                p('ATContentTypes: Add File', ploneMeetingUpdaters, acquire=0)
        logger.info('Done.')

        # Update the local roles of every item in the database
        logger.info('Updating local roles on items...')
        for brain in self.brains:
            item = brain.getObject()
            item.updateLocalRoles()
        logger.info('Done.')

    def _moveAnnexes(self):
        '''Moves annexes in MeetingItems that are now folderish and:
           * adds a pm_modification_date to every item and annex;
           * adds the "annex name" black list to every item.
        '''
        logger.info('Moving annexes...')
        for brain in self.brains:
            item = brain.getObject()
            # Add the "annex names black list"
            item.alreadyUsedAnnexNames = PersistentList()
            # Manage annexes
            for annexesGroup in (item.getAnnexes(), item.getAnnexesDecision()):
                for annexe in annexesGroup:
                    # Move the annex
                    if annexe.getParentNode() == item:
                        pass
                    else:
                        sourceFolder = annexe.getParentNode()
                        destFolder = item
                        cuttedAnnexes = sourceFolder.manage_cutObjects(ids=[annexe.getId()])
                        destFolder.manage_pasteObjects(cuttedAnnexes)
                        logger.info("Annexe '%s' moved into item" % annexe.id)
                    # Add a pm_modification_date to every annex
                    annexe.pm_modification_date = annexe.modification_date
                    # Update "annex names black list"
                    item.alreadyUsedAnnexNames.append(annexe.id)
            # Update annexIndex
            item.updateAnnexIndex()
            # Update pm_modification_date
            item.pm_modification_date = item.modification_date
        logger.info('Done.')

    def _initialiseColorSystem(self):
        logger.info('Initializing color system...')
        # Add accessInfo dict to the tool
        if not hasattr(self.tool.aq_base, 'accessInfo'):
            self.tool.accessInfo = OOBTree()
        if self.tool.getUsedColorSystem() == "modification_color":
            # Add access info for every member
            for userId in self.portal.portal_membership.listMemberIds():
                if hasattr(self.portal.Members.aq_base, userId):
                    logger.info('Creating access dict for user %s...' % userId)
                    self.tool.accessInfo[userId] = OOBTree()
                    # Add access info to every item
                    accessInfo = self.tool.accessInfo[userId]
                    for itemBrain in self.brains:
                        item = itemBrain.getObject()
                        accessInfo[item.UID()] = DateTime() # Now
                        # Add access info to every annex
                        for annexesGroup in (item.getAnnexes(), \
                                             item.getAnnexesDecision()):
                            for annexe in annexesGroup:
                                accessInfo[annexe.UID()] = DateTime() # Now
                else:
                    logger.info('No access dict for %s, he has no member ' \
                                'folder so never logged in.' % userId)
        logger.info('Done.')

    def _updateSecuritySettings(self):
        logger.info('Updating security settings...')
        self.portal.portal_workflow.updateRoleMappings()
        # Annex security is tied to item security. Now that item security is OK,
        # update annex security accordingly.
        for itemBrain in self.brains:
            item = itemBrain.getObject()
            for annexesGroup in (item.getAnnexes(), item.getAnnexesDecision()):
                for annexe in annexesGroup:
                    annexe.updateAnnexSecurity()
        logger.info('Done.')

    uglyContent = (' align="left" style="text-align: left;" ' \
                   'class="MsoBodyTextIndent"', ' style="text-align: justify;"',
                   ' align="left"', ' start="1"', ' class="Para"',
                   ' align="center" style="text-align: center;"',
                   ' style="text-align: left;" class="MsoBodyTextIndent"',
                   ' class="MsoBodyTextIndent"', ' class="MsoBodyText2"',
                   ' class="ChrisNormal"', ' class="MsoNormalCxSpMiddle"',
                   ' class="MsoNormalCxSpFirst"', ' class="MsoNormalCxSpLast"',
                   ' class="Style1CxSpFirst"', ' class="Style1CxSpMiddle"',
                   ' class="Style1CxSpLast"', ' class="MsoBodyText"',
                   ' class="MsoBodyTextIndent3"', ' class="Monsieur"',
                   ' class="TextepardfautCarCar"')
    def _updateRichTextFields(self):
        logger.info('Updating rich text fields...')
        for brain in self.brains:
            item = brain.getObject()
            modifDate = item.modification_date
            # Remove some ugly attributes
            for ugly in self.uglyContent:
                item.setDecision(item.getDecision().replace(ugly, ''))
                item.setDescription(item.Description().replace(ugly, ''))
            item.transformAllRichTextFields()
            item.setModificationDate(modifDate)
        logger.info('Done.')

    def run(self):
        self._updateItemsOwnerShip()
        self._updateLocalRoles()
        self._moveAnnexes()
        self._initialiseColorSystem()
        self._updateRichTextFields()
        self._updateSecuritySettings()
        logger.info('Recataloging...')
        self.portal.portal_catalog.refreshCatalog(clear=0)
        self.portal.reference_catalog.refreshCatalog(clear=0)
        self.portal.uid_catalog.refreshCatalog(clear=0)
        logger.info('Migration finished.')

# The migration function -------------------------------------------------------
def migrate(context):
    '''This migration function does the following things:

       1) Now in PloneMeeting a user may belong to several MeetingGroups. The
          security model has evolved accordingly: local roles that grant access
          to items are not set on 'mymeetings' folders anymore (within member
          folders) but are set on items themselves. Recurring items must now be
          owned by the meeting creator.

       2) Items are now folderish: this script cuts and pastes annexes and puts
          them within items.

       3) annexIndexes on MeetingItems are recomputed because they include now
          relative paths instead of absolute paths. This was problematic when
          moving a database from one site to the other (like for copying the
          production DB to the test DB in order to test a migration function,
          for instance).

       4) The 'color system', that allows one to see in a distinct color every
          item or annex that was added or updated since the last time he
          consulted meeting_view, needs, for items and annexes, to compute a new
          modification_date (= pm_modification_date). Indeed, the standard
          modification_date evolves when some changes occur that are of no
          interest for users (like state changes).

       5) The PloneMeeting color system, if used, must be initialized. Every
          item and annex must be noted as already consulted. Indeed, they may be
          stored in browsers' caches, which means that they will maybe not be
          downloaded again, so the accessInfo will not be updated.

       6) Updates richtext fields by calling "updateAllRichTextFields" (keeps
          the modification_date unchanged). This has no effect if your
          PloneMeeting site has not overridden this method.'''
    Migrate_To_1_3(context).run()
# ------------------------------------------------------------------------------
