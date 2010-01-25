# -*- coding: utf-8 -*-
#
# File: MeetingAdviceAgreementLevel.py
#
# Copyright (c) 2010 by []
# Generator: ArchGenXML Version 2.4.1
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """unknown <unknown>"""
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import *
from zope.interface import implements
import interfaces

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

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
        widget=ImageField._properties['widget'](
            label_msgid="agreement_level_label_theicon",
            label="AgreementLevelTheIcon",
            i18n_domain='PloneMeeting',
        ),
        storage=AnnotationStorage(),
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

class MeetingAdviceAgreementLevel(BaseContent, BrowserDefaultMixin):
    """
    """
    security = ClassSecurityInfo()

    implements(interfaces.IMeetingAdviceAgreementLevel)

    meta_type = 'MeetingAdviceAgreementLevel'
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



