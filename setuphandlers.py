# -*- coding: utf-8 -*-
#
# File: setuphandlers.py
#
# Copyright (c) 2010 by []
# Generator: ArchGenXML Version 2.4.1
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """unknown <unknown>"""
__docformat__ = 'plaintext'


import logging
logger = logging.getLogger('PloneMeeting: setuphandlers')
from Products.PloneMeeting.config import PROJECTNAME
from Products.PloneMeeting.config import DEPENDENCIES
import os
from sets import Set
from Products.CMFCore.utils import getToolByName
import transaction
##code-section HEAD
##/code-section HEAD

def isNotPloneMeetingProfile(context):
    return context.readDataFile("PloneMeeting_marker.txt") is None

def setupHideToolsFromNavigation(context):
    """hide tools"""
    if isNotPloneMeetingProfile(context): return 
    # uncatalog tools
    site = context.getSite()
    toolnames = ['portal_plonemeeting']
    portalProperties = getToolByName(site, 'portal_properties')
    navtreeProperties = getattr(portalProperties, 'navtree_properties')
    if navtreeProperties.hasProperty('idsNotToList'):
        for toolname in toolnames:
            try:
                portal[toolname].unindexObject()
            except:
                pass
            current = list(navtreeProperties.getProperty('idsNotToList') or [])
            if toolname not in current:
                current.append(toolname)
                kwargs = {'idsNotToList': current}
                navtreeProperties.manage_changeProperties(**kwargs)

def setupCatalogMultiplex(context):
    """ Configure CatalogMultiplex.

    explicit add classes (meta_types) be indexed in catalogs (white)
    or removed from indexing in a catalog (black)
    """
    if isNotPloneMeetingProfile(context): return 
    site = context.getSite()
    #dd#
    muliplexed = ['ToolPloneMeeting', 'MeetingCategory', 'MeetingConfig', 'MeetingFileType', 'MeetingGroup', 'ExternalApplication', 'MeetingAdviceAgreementLevel', 'PodTemplate', 'MeetingUser']

    atool = getToolByName(site, 'archetype_tool')
    catalogmap = {}
    catalogmap['ToolPloneMeeting'] = {}
    catalogmap['ToolPloneMeeting']['black'] = ['portal_catalog']
    catalogmap['MeetingCategory'] = {}
    catalogmap['MeetingCategory']['white'] = ['portal_catalog']
    catalogmap['MeetingConfig'] = {}
    catalogmap['MeetingConfig']['black'] = ['portal_catalog']
    catalogmap['MeetingFileType'] = {}
    catalogmap['MeetingFileType']['black'] = ['portal_catalog']
    catalogmap['MeetingGroup'] = {}
    catalogmap['MeetingGroup']['black'] = ['portal_catalog']
    catalogmap['ExternalApplication'] = {}
    catalogmap['ExternalApplication']['black'] = ['portal_catalog']
    catalogmap['MeetingAdviceAgreementLevel'] = {}
    catalogmap['MeetingAdviceAgreementLevel']['black'] = ['portal_catalog']
    catalogmap['PodTemplate'] = {}
    catalogmap['PodTemplate']['black'] = ['portal_catalog']
    catalogmap['MeetingUser'] = {}
    catalogmap['MeetingUser']['black'] = ['portal_catalog']
    for meta_type in catalogmap:
        submap = catalogmap[meta_type]
        current_catalogs = Set([c.id for c in atool.getCatalogsByType(meta_type)])
        if 'white' in submap:
            for catalog in submap['white']:
                if getToolByName(site, catalog, None) is None:
                    raise AttributeError, 'Catalog "%s" does not exist!' % catalog
                current_catalogs.update([catalog])
        if 'black' in submap:
            for catalog in submap['black']:
                if catalog in current_catalogs:
                    current_catalogs.remove(catalog)
        atool.setCatalogsByType(meta_type, list(current_catalogs))



def updateRoleMappings(context):
    """after workflow changed update the roles mapping. this is like pressing
    the button 'Update Security Setting' and portal_workflow"""
    if isNotPloneMeetingProfile(context): return 
    wft = getToolByName(context.getSite(), 'portal_workflow')
    wft.updateRoleMappings()

def postInstall(context):
    """Called as at the end of the setup process. """
    # the right place for your custom code
    if isNotPloneMeetingProfile(context): return
    site = context.getSite()



##code-section FOOT
##/code-section FOOT
