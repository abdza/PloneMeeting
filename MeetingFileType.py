# -*- coding: utf-8 -*-
#
# File: MeetingFileType.py
#
# Copyright (c) 2009 by PloneGov
# Generator: ArchGenXML Version 1.5.2
#            http://plone.org/products/archgenxml
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

__author__ = """Gaetan DELANNAY <gaetan.delannay@geezteem.com>, Gauthier BASTIEN
<gbastien@commune.sambreville.be>, Stephan GEULETTE
<stephan.geulette@uvcw.be>"""
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from Products.PloneMeeting.config import *

##code-section module-header #fill in your manual code here
from Globals import InitializeClass
from Products.PloneMeeting.utils import getCustomAdapter, HubSessionsMarshaller

# Marshaller -------------------------------------------------------------------
class FileTypeMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a file type into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'fileType'
InitializeClass(FileTypeMarshaller)
##/code-section module-header

schema = Schema((

    ImageField(
        name='theIcon',
        widget=ImageWidget(
            label='Theicon',
            label_msgid='PloneMeeting_label_theIcon',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        storage=AttributeStorage()
    ),

    StringField(
        name='predefinedTitle',
        widget=StringWidget(
            size=70,
            label='Predefinedtitle',
            label_msgid='PloneMeeting_label_predefinedTitle',
            i18n_domain='PloneMeeting',
        )
    ),

    BooleanField(
        name='decisionRelated',
        default= False,
        widget=BooleanField._properties['widget'](
            label='Decisionrelated',
            label_msgid='PloneMeeting_label_decisionRelated',
            i18n_domain='PloneMeeting',
        )
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingFileType_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
MeetingFileType_schema = ModelExtender(MeetingFileType_schema, 'filetype').run()
# Register the marshaller for DAV/XML export.
MeetingFileType_schema.registerLayer('marshall', FileTypeMarshaller())
##/code-section after-schema

class MeetingFileType(BaseContent):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(BaseContent,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'MeetingFileType'

    meta_type = 'MeetingFileType'
    portal_type = 'MeetingFileType'
    allowed_content_types = []
    filter_content_types = 0
    global_allow = 1
    #content_icon = 'MeetingFileType.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "MeetingFileType"
    typeDescMsgId = 'description_edit_meetingfiletype'

    _at_rename_after_creation = True

    schema = MeetingFileType_schema

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePublic('getIcon')
    def getIcon(self, relative_to_portal=0):
        '''Return the icon for views'''
        field = self.getField('theIcon')
        if not field:
            # field is empty
            return BaseContent.getIcon(self, relative_to_portal)
        return self.absolute_url(relative=1) + "/theIcon"

    security.declarePublic('getBestIcon')
    def getBestIcon(self):
        '''Calculates the icon for the AT default view'''
        self.getIcon()

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self): self.adapted().onEdit(isCreated=True)

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self): self.adapted().onEdit(isCreated=False)

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'MeetingFileType': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''

    security.declarePublic('isSelectable')
    def isSelectable(self):
        '''See documentation in interfaces.py.'''
        mft = self.getSelf()
        wfTool = self.portal_workflow
        state = wfTool.getInfoFor(mft, 'review_state')
        return state == 'active'



registerType(MeetingFileType, PROJECTNAME)
# end of class MeetingFileType

##code-section module-footer #fill in your manual code here
##/code-section module-footer



