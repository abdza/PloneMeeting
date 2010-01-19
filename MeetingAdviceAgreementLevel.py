# -*- coding: utf-8 -*-
#
# File: MeetingAdviceAgreementLevel.py
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
class AgLevelMarshaller(HubSessionsMarshaller):
    '''Allows to marshall an agreement level into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'agLevel'
InitializeClass(AgLevelMarshaller)
##/code-section module-header

schema = Schema((

    ImageField(
        name='theIcon',
        widget=ImageWidget(
            label_msgid="agreement_level_label_theicon",
            label="AgreementLevelTheIcon",
            i18n_domain='PloneMeeting',
        ),
        storage=AttributeStorage()
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingAdviceAgreementLevel_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
MeetingAdviceAgreementLevel_schema = ModelExtender(
    MeetingAdviceAgreementLevel_schema, 'aglevel').run()
# Register the marshaller for DAV/XML export.
MeetingAdviceAgreementLevel_schema.registerLayer('marshall',AgLevelMarshaller())
##/code-section after-schema

class MeetingAdviceAgreementLevel(BaseContent):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(BaseContent,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'MeetingAdviceAgreementLevel'

    meta_type = 'MeetingAdviceAgreementLevel'
    portal_type = 'MeetingAdviceAgreementLevel'
    allowed_content_types = []
    filter_content_types = 0
    global_allow = 1
    #content_icon = 'MeetingAdviceAgreementLevel.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "MeetingAdviceAgreementLevel"
    typeDescMsgId = 'description_edit_meetingadviceagreementlevel'

    _at_rename_after_creation = True

    schema = MeetingAdviceAgreementLevel_schema

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self): self.adapted().onEdit(isCreated=True)

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self): self.adapted().onEdit(isCreated=False)

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'MeetingAdviceAgreementLevel':
            return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''



registerType(MeetingAdviceAgreementLevel, PROJECTNAME)
# end of class MeetingAdviceAgreementLevel

##code-section module-footer #fill in your manual code here
##/code-section module-footer



