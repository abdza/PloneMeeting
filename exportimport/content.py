# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Copyright (c) 2007 PloneGov
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

__author__ = '''Gauthier BASTIEN <gbastien@commune.sambreville.be>'''
__docformat__ = 'plaintext'

'''PloneMeeting exportimport setup.
   This is the exportimport file for GenericSetup. See configure.zcml and
   profiles/default for more information.'''

# ------------------------------------------------------------------------------
import os.path
from Products.CMFCore.utils import getToolByName
from Products.PlacelessTranslationService import utranslate
from Products.PloneMeeting import PloneMeetingError
from zExceptions import BadRequest
from Products.PloneMeeting.config import *
import logging
logger = logging.getLogger('PloneMeeting')

# PloneMeeting-Error related constants -----------------------------------------
MEETING_ID_EXISTS = 'The meeting config with id "%s" already exists.'

# ------------------------------------------------------------------------------
class ToolInitializer:
    '''Initializes the PloneMeeting tool based on information from a given
       PloneMeeting profile.'''
    successMessage = "The PloneMeeting tool has been successfully initialized."

    def __init__(self, context, productname):
        self.profilePath = context._profile_path
        self.productname = productname
        self.tool = context.getSite().portal_plonemeeting
        self.profileData = self.getProfileData()
        # Initialize the tool
        for k, v in self.profileData.getData().iteritems():
            exec 'self.tool.set%s%s(v)' % (k[0].upper(), k[1:])

    def getProfileData(self):
        '''Loads, from the current profile, the data to import into the tool:
        meeting config(s), categories, etc.'''
        pp = self.profilePath
        profileModule = pp[pp.rfind(self.productname):].replace('/', '.')
        profileModule = profileModule.replace('\\', '.')
        exec 'from Products.%s.import_data import data' % profileModule
        return data

    def run(self):
        # Import external applications
        d = self.profileData
        self.tool.addExternalApplications(d.externalApplications)
        self.tool.addUsersAndGroups(d.groups, d.usersOutsideGroups)
        for mConfig in d.meetingConfigs:
            try:
                meetingConfig = self.tool.createMeetingConfig(
                    mConfig, source=self.profilePath)
            except BadRequest:
                # If we raise a BadRequest, it is that the id is already in use.
                logger.warn(MEETING_ID_EXISTS % mConfig.id)
        return self.successMessage

# Functions that correspond to the PloneMeeting profile import steps -----------
def installProducts(context):
    '''Installs the necessary products for running PloneMeeting.'''
    portal = context.getSite()
    qi = getToolByName(portal, 'portal_quickinstaller')
    if not qi.isProductInstalled('Archetypes'):
        qi.installProduct('Archetypes')
    #if not qi.isProductInstalled('PloneMeeting'):
    #    qi.installProduct('PloneMeeting')
    return "Necessary products for PloneMeeting installed."

def initializeTool(context):
    '''Initialises the PloneMeeting tool based on information from the current
       profile.'''
    return ToolInitializer(context, PROJECTNAME).run()
# ------------------------------------------------------------------------------
