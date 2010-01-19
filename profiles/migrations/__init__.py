# -*- coding: utf-8 -*-
# Copyright (c) 2008 by PloneGov
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

'''This module defines functions that allow to migrate to a given version of
   PloneMeeting for production sites that run older versions of PloneMeeting.
   You must run every migration function in the right chronological order.
   For example, if your production site runs a version of PloneMeeting as of
   2008_04_01, and two migration functions named
   migrateToPloneMeeting_2008_05_23 and migrateToPloneMeeting_2008_08_29 exist,
   you need to execute migrateToPloneMeeting_2008_05_23 first AND
   migrateToPloneMeeting_2008_08_29 then.

   Migration functions must be run from portal_setup within your Plone site
   through the ZMI. Every migration function corresponds to a import step in
   portal_setup.'''

# ------------------------------------------------------------------------------
from Products.CMFCore.utils import getToolByName
import logging
logger = logging.getLogger('PloneMeeting')

# ------------------------------------------------------------------------------
class Migrator:
    '''Abstract class for creating a migrator.'''
    def __init__(self, context):
        self.portal = context.getSite()
        self.tool = getToolByName(self.portal, 'portal_plonemeeting')
        self._profile_path = context._profile_path

    def run(self):
        '''Must be overridden. This method does the migration job.'''
        raise 'You should have overridden me darling.'''

    def refreshDatabase(self, catalogs=True,
        catalogsToRebuild=['portal_catalog'], workflows=False):
        '''After the migration script has been executed, it can be necessary to
           update the Plone catalogs and/or the workflow settings on every
           database object if workflow definitions have changed. We can pass
           catalog ids we want to 'clear and rebuild' using
           p_catalogsToRebuild.'''
        if catalogs:
            logger.info('Recataloging...')
            # Manage the catalogs we want to clear and rebuild
            # We have to call another method as clear=1 passed to refreshCatalog
            #does not seem to work as expected...
            for catalog in catalogsToRebuild:
                catalogObj = getattr(self.portal, catalog)
                catalogObj.clearFindAndRebuild()
            catalogIds = ('portal_catalog', 'reference_catalog', 'uid_catalog')
            for catalogId in catalogIds:
                if not catalogId in catalogsToRebuild:
                    catalogObj = getattr(self.portal, catalogId)
                    catalogObj.refreshCatalog(clear=0)
        if workflows:
            logger.info('Refresh workflow-related information on every ' \
                        'object of the database...')
            self.portal.portal_workflow.updateRoleMappings()

    def reinstall(self, products=['PloneMeeting']):
        '''Allows to reinstall a series of p_products.'''
        logger.info('Reinstalling product(s) %s...' % ','.join(products))
        self.portal.portal_quickinstaller.reinstallProducts(products)
        logger.info('Done.')
# ------------------------------------------------------------------------------
