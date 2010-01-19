# -*- coding: utf-8 -*-
#
# File: MeetingCategory.py
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
class CategoryMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a category into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'category'
InitializeClass(CategoryMarshaller)

##/code-section module-header

schema = Schema((

    TextField(
        name='description',
        widget=TextAreaWidget(
            label_msgid="meetingcategory_label_description",
            label='Description',
            i18n_domain='PloneMeeting',
        ),
        accessor="Description"
    ),

    StringField(
        name='categoryId',
        widget=StringWidget(
            description="CategoryId",
            description_msgid="category_category_id_descr",
            label='Categoryid',
            label_msgid='PloneMeeting_label_categoryId',
            i18n_domain='PloneMeeting',
        ),
        searchable=True
    ),

    IntegerField(
        name='itemsCount',
        default=0,
        widget=IntegerField._properties['widget'](
            description="ItemsCount",
            description_msgid="category_items_count_descr",
            label='Itemscount',
            label_msgid='PloneMeeting_label_itemsCount',
            i18n_domain='PloneMeeting',
        ),
        schemata="metadata"
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingCategory_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
MeetingCategory_schema = ModelExtender(MeetingCategory_schema, 'category').run()
# Register the marshaller for DAV/XML export.
MeetingCategory_schema.registerLayer('marshall', CategoryMarshaller())
##/code-section after-schema

class MeetingCategory(BaseContent):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(BaseContent,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'MeetingCategory'

    meta_type = 'MeetingCategory'
    portal_type = 'MeetingCategory'
    allowed_content_types = []
    filter_content_types = 0
    global_allow = 1
    #content_icon = 'MeetingCategory.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "MeetingCategory"
    typeDescMsgId = 'description_edit_meetingcategory'

    _at_rename_after_creation = True

    schema = MeetingCategory_schema

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    # Methods

    # Manually created methods

    def getOrder(self):
        '''At what position am I among all the active categories of my
           folder in the meeting config?'''
        try:
            folderId = self.getParentNode().id
            classifiers = False
            if folderId == 'classifiers':
                classifiers = True
            i = self.getParentNode().getParentNode().getCategories(
                classifiers=classifiers).index(self)
        except ValueError:
            i = None
        return i

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self): self.adapted().onEdit(isCreated=True)

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self): self.adapted().onEdit(isCreated=False)

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'MeetingCategory': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''

    security.declarePublic('isSelectable')
    def isSelectable(self):
        '''See documentation in interfaces.py.'''
        cat = self.getSelf()
        wfTool = self.portal_workflow
        state = wfTool.getInfoFor(cat, 'review_state')
        return state == 'active'

    def incrementItemsCount(self):
        '''A new item has chosen me as a classifier or category. I must
           increment my item counter. This method returns the new items
           count.'''
        if self.getItemsCount() == None: self.setItemsCount(0)
        newCount = self.getItemsCount() + 1
        self.setItemsCount(newCount)
        return newCount



registerType(MeetingCategory, PROJECTNAME)
# end of class MeetingCategory

##code-section module-footer #fill in your manual code here
##/code-section module-footer



