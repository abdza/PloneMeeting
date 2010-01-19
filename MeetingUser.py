# -*- coding: utf-8 -*-
#
# File: MeetingUser.py
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
class MeetingUserMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a meeting user into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'meetingUser'
InitializeClass(MeetingUserMarshaller)

class DummyMeetingUser:
    '''Used as a replacement for a MeetingUser when it has been deleted.'''
    security = ClassSecurityInfo()
    def __init__(self, id): self.id = id
    security.declarePublic('Title')
    def Title(self): return '<Deleted user>'
InitializeClass(DummyMeetingUser)
##/code-section module-header

schema = Schema((

    StringField(
        name='title',
        widget=StringWidget(
            visible=False,
            label='Title',
            label_msgid='PloneMeeting_label_title',
            i18n_domain='PloneMeeting',
        ),
        accessor="Title"
    ),

    StringField(
        name='ploneUserId',
        widget=StringWidget(
            description="MeetingUserPloneUser",
            description_msgid="meeting_user_plone_user_descr",
            label='Ploneuserid',
            label_msgid='PloneMeeting_label_ploneUserId',
            i18n_domain='PloneMeeting',
        ),
        required= True
    ),

    StringField(
        name='duty',
        widget=StringWidget(
            description="MeetingUserDuty",
            description_msgid="meeting_user_duty_descr",
            label='Duty',
            label_msgid='PloneMeeting_label_duty',
            i18n_domain='PloneMeeting',
        )
    ),

    LinesField(
        name='usages',
        widget=MultiSelectionWidget(
            description="MeetingUserUsages",
            description_msgid="meeting_user_usages_descr",
            format="checkbox",
            label='Usages',
            label_msgid='PloneMeeting_label_usages',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        multiValued=1,
        vocabulary='listUsages'
    ),

    ImageField(
        name='signatureImage',
        widget=ImageWidget(
            description="MeetingUserSignatureImage",
            description_msgid="meeting_user_signature_image_descr",
            label='Signatureimage',
            label_msgid='PloneMeeting_label_signatureImage',
            i18n_domain='PloneMeeting',
        ),
        storage=AttributeStorage()
    ),

    BooleanField(
        name='signatureIsDefault',
        default= False,
        widget=BooleanField._properties['widget'](
            description="MeetingUserSignatureIsDefault",
            description_msgid="meeting_user_signature_is_default",
            label='Signatureisdefault',
            label_msgid='PloneMeeting_label_signatureIsDefault',
            i18n_domain='PloneMeeting',
        )
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingUser_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
MeetingUser_schema = ModelExtender(MeetingUser_schema, 'muser').run()
# Register the marshaller for DAV/XML export.
MeetingUser_schema.registerLayer('marshall', MeetingUserMarshaller())
##/code-section after-schema

class MeetingUser(BaseContent):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(BaseContent,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'MeetingUser'

    meta_type = 'MeetingUser'
    portal_type = 'MeetingUser'
    allowed_content_types = []
    filter_content_types = 0
    global_allow = 1
    #content_icon = 'MeetingUser.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "MeetingUser"
    typeDescMsgId = 'description_edit_meetinguser'

    _at_rename_after_creation = True

    schema = MeetingUser_schema

    ##code-section class-header #fill in your manual code here
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'MeetingUser': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''

    security.declarePublic('getMeetingUserTitle')
    def getMeetingUserTitle(self):
        '''My title is based on the fullname of the corresponding Plone user.'''
        userInfo = self.portal_membership.getMemberById(self.getPloneUserId())
        if userInfo and userInfo.getProperty('fullname'):
            return userInfo.getProperty('fullname')
        else:
            return self.getPloneUserId()

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self):
        self.setTitle(self.getMeetingUserTitle())
        self.adapted().onEdit(isCreated=True)

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self):
        self.setTitle(self.getMeetingUserTitle())
        self.adapted().onEdit(isCreated=False)

    def validate_ploneUserId(self, value):
        '''Does p_value correspond to an existing Plone user id?'''
        ploneUser = self.acl_users.getUser(value)
        if not ploneUser:
            return self.utranslate('meeting_user_no_plone_user',
                                   domain='PloneMeeting')
        mUsers = getattr(self.portal_plonemeeting, TOOL_FOLDER_MEETING_USERS)
        for mUser in mUsers.objectValues('MeetingUser'):
            if mUser.ploneUserId == value and self.UID() != mUser.UID():
                return self.utranslate('meeting_user_plone_user_already_used',
                                   domain='PloneMeeting')
        return None

    def listUsages(self):
        '''Returns list of possible usages (for what will this user be useful
           in voting process: "assembly member", "signer" or "voter").'''
        d = 'PloneMeeting'
        res = DisplayList((
                ("assemblyMember", self.utranslate(
                    'meeting_user_usage_assemblyMember', domain=d)),
                ("signer", self.utranslate(
                    'meeting_user_usage_signer', domain=d)),
                ("voter", self.utranslate(
                    "meeting_user_usage_voter", domain=d)),
              ))
        return res

    security.declarePublic('mayConsultVote')
    def mayConsultVote(self, loggedUser, item):
        '''See doc in interfaces.py.'''
        mUser = self.getSelf()
        if (loggedUser.id == mUser.getPloneUserId()) or \
           loggedUser.has_role('MeetingManager') or \
           loggedUser.has_role('Manager') or \
           item.getMeeting().isDecided():
            return True
        return False

    security.declarePublic('mayEditVote')
    def mayEditVote(self, loggedUser, item):
        '''See doc in interfaces.py.'''
        mUser = self.getSelf()
        if loggedUser.has_role('Manager'):
            return True
        if item.getMeeting().isDecided():
            return False
        else:
            meetingConfig = item.portal_plonemeeting.getMeetingConfig(item)
            votesEncoder = meetingConfig.getVotesEncoder()
            if (loggedUser.id == mUser.getPloneUserId()) and \
               ('theVoterHimself' in votesEncoder):
                return True
            if loggedUser.has_role('MeetingManager') and \
               ('aMeetingManager' in votesEncoder):
                return True
        return False



registerType(MeetingUser, PROJECTNAME)
# end of class MeetingUser

##code-section module-footer #fill in your manual code here
##/code-section module-footer



