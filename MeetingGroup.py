# -*- coding: utf-8 -*-
#
# File: MeetingGroup.py
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
from Products.PloneMeeting import PloneMeetingError
import logging
logger = logging.getLogger('PloneMeeting')
from Products.CMFCore.permissions import ModifyPortalContent
from OFS.ObjectManager import BeforeDeleteException
from Products.PloneMeeting.profiles import GroupDescriptor
defValues = GroupDescriptor.get()

# Marshaller -------------------------------------------------------------------
class GroupMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a group into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'meetingGroup'
InitializeClass(GroupMarshaller)
##/code-section module-header

schema = Schema((

    StringField(
        name='acronym',
        widget=StringField._properties['widget'](
            label='Acronym',
            label_msgid='PloneMeeting_label_acronym',
            i18n_domain='PloneMeeting',
        ),
        required=True,
    ),
    TextField(
        name='description',
        widget=TextAreaWidget(
            label_msgid="meetinggroup_label_description",
            label='Description',
            i18n_domain='PloneMeeting',
        ),
        accessor="Description",
    ),
    StringField(
        name='givesMandatoryAdviceOn',
        default= defValues.givesMandatoryAdviceOn,
        widget=StringField._properties['widget'](
            size=100,
            description="GivesMandatoryAdviceOn",
            description_msgid="gives_mandatory_advice_on_descr",
            label='Givesmandatoryadviceon',
            label_msgid='PloneMeeting_label_givesMandatoryAdviceOn',
            i18n_domain='PloneMeeting',
        ),
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingGroup_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
MeetingGroup_schema = ModelExtender(MeetingGroup_schema, 'group').run()
# Register the marshaller for DAV/XML export.
MeetingGroup_schema.registerLayer('marshall', GroupMarshaller())
##/code-section after-schema

class MeetingGroup(BaseContent, BrowserDefaultMixin):
    """
    """
    security = ClassSecurityInfo()

    implements(interfaces.IMeetingGroup)

    meta_type = 'MeetingGroup'
    _at_rename_after_creation = True

    schema = MeetingGroup_schema

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    # Methods

    # Manually created methods

    def getPloneGroupId(self, suffix):
        '''Returns the id of the Plone group that corresponds to me and
           p_suffix.'''
        return '%s_%s' % (self.id, suffix)

    def _createPloneGroup(self, groupSuffix):
        '''Creates the PloneGroup that corresponds to me and p_groupSuffix.'''
        groupId = self.getPloneGroupId(groupSuffix)
        enc = self.portal_properties.site_properties.getProperty(
            'default_charset')
        groupTitle = '%s (%s)' % (
            self.Title().decode(enc),
            self.utranslate(groupSuffix, domain='PloneMeeting'))
        self.portal_groups.addGroup(groupId, title=groupTitle)
        self.portal_groups.setRolesForGroup(groupId, ('MeetingObserverGlobal',))
        group = self.portal_groups.getGroupById(groupId)
        group.setProperties(meetingRole=MEETINGROLES[groupSuffix],
                            meetingGroupId=self.id)

    def getOrder(self, associatedGroupIds=None):
        '''At what position am I among all the active groups ? If
           p_associatedGroupIds is not None or empty, this method must return
           the order of the lowest group among all associated groups (me +
           associated groups).'''
        activeGroups = self.getParentNode().getActiveGroups()
        i = activeGroups.index(self)
        if associatedGroupIds:
            j = -1
            for group in activeGroups:
                j += 1
                if (group.id in associatedGroupIds) and (j < i):
                    i = j + 0.5
        return i

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self):
        '''Creates the 3 corresponding Plone groups:
           - a group for the creators;
           - a group for the reviewers;
           - a group for the observers.'''
        # If a group with this id already exists, prevent creation from this
        # group.
        for groupSuffix in MEETINGROLES.iterkeys():
            groupId = self.getPloneGroupId(groupSuffix)
            ploneGroup = self.portal_groups.getGroupById(groupId)
            if ploneGroup:
                raise PloneMeetingError("You can't create this MeetingGroup " \
                                        "because a Plone groupe having id " \
                                        "'%s' already exists." % groupId)
        for groupSuffix in MEETINGROLES.iterkeys():
            self._createPloneGroup(groupSuffix)
        self.adapted().onEdit(isCreated=True) # Call product-specific code

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self): self.adapted().onEdit(isCreated=False)

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        '''Checks if the current meetingGroup can be deleted:
          - it can not be linked to an existing meetingItem;
          - it can not be referenced in an existing meetingConfig;
          - the linked ploneGroups must be empty of members.'''
        # Do lighter checks first...  Check that the meetingGroup is not used
        # in a meetingConfig
        #if we are trying to remove the Plone Site, bypass this hook...
        if not item.meta_type == "Plone Site":
            for mc in self.portal_plonemeeting.objectValues('MeetingConfig'):
                # The meetingGroup can be referenced in :
                # - advices : mandatoryAdvisers and optionalAdvisers;
                # - copies : selectableCopyGroups.
                for role in MEETINGROLES.iterkeys():
                    if self.getPloneGroupId(role) in mc.getOptionalAdvisers():
                        raise BeforeDeleteException, \
                            "can_not_delete_meetinggroup_meetingconfig"
                if self.getPloneGroupId(suffix="advisers") in \
                mc.getSelectableCopyGroups():
                    raise BeforeDeleteException, \
                            "can_not_delete_meetinggroup_meetingconfig"
            # Then check that every linked Plone group is empty because we are
            # going to delete them.
            for role in MEETINGROLES.iterkeys():
                ploneGroupId = self.getPloneGroupId(role)
                group = self.portal_groups.getGroupById(ploneGroupId)
                if group and group.getMemberIds():
                    raise BeforeDeleteException, \
                        "can_not_delete_meetinggroup_plonegroup"
            # And finally, check that meetingGroup is not linked to an existing
            # item.
            for brain in self.portal_catalog(meta_type="MeetingItem"):
                obj = brain.getObject()
                mgId = self.getId()
                if (obj.getProposingGroup() == mgId) or \
                   (mgId in obj.getAssociatedGroups()):
                    # The meetingGroup islinked to an existing item, we can not
                    # delete it.
                    raise BeforeDeleteException, \
                        "can_not_delete_meetinggroup_meetingitem"
            # If everything passed correctly, we delete every linked (and empty)
            # Plone groups.
            for role in MEETINGROLES.iterkeys():
                ploneGroupId = self.getPloneGroupId(role)
                group = self.portal_groups.getGroupById(ploneGroupId)
                if group:
                    self.portal_groups.removeGroup(ploneGroupId)
        BaseContent.manage_beforeDelete(self, item, container)

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'MeetingGroup': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''



registerType(MeetingGroup, PROJECTNAME)
# end of class MeetingGroup

##code-section module-footer #fill in your manual code here
##/code-section module-footer



