# -*- coding: utf-8 -*-
#
# File: PloneMeeting.py
#
# Copyright (c) 2010 by []
# Generator: ArchGenXML Version 2.4.1
#            http://plone.org/products/archgenxml
#
# GNU General Public License (GPL)
#

__author__ = """unknown <unknown>"""
__docformat__ = 'plaintext'


# Product configuration.
#
# The contents of this module will be imported into __init__.py, the
# workflow configuration and every content type module.
#
# If you wish to perform custom configuration, you may put a file
# AppConfig.py in your product's root directory. The items in there
# will be included (by importing) in this file if found.

from Products.CMFCore.permissions import setDefaultRoles
##code-section config-head #fill in your manual code here
##/code-section config-head


PROJECTNAME = "PloneMeeting"

# Permissions
DEFAULT_ADD_CONTENT_PERMISSION = "Add portal content"
setDefaultRoles(DEFAULT_ADD_CONTENT_PERMISSION, ('Manager', 'Owner', 'Contributor'))
ADD_CONTENT_PERMISSIONS = {
    'MeetingItem': 'PloneMeeting: Add MeetingItem',
    'Meeting': 'PloneMeeting: Add Meeting',
    'MeetingCategory': 'PloneMeeting: Manage configuration',
    'MeetingConfig': 'PloneMeeting: Manage configuration',
    'MeetingFileType': 'PloneMeeting: Manage configuration',
    'MeetingFile': 'PloneMeeting: Add MeetingFile',
    'MeetingGroup': 'PloneMeeting: Manage configuration',
    'ExternalApplication': 'PloneMeeting: Manage configuration',
    'MeetingAdvice': 'PloneMeeting: Add MeetingAdvice',
    'MeetingAdviceAgreementLevel': 'PloneMeeting: Manage configuration',
    'PodTemplate': 'PloneMeeting: Manage configuration',
    'MeetingUser': 'PloneMeeting: Manage configuration',
}

setDefaultRoles('PloneMeeting: Add MeetingItem', ('Manager', ))
setDefaultRoles('PloneMeeting: Add Meeting', ('Manager', ))
setDefaultRoles('PloneMeeting: Manage configuration', ('Manager', ))
setDefaultRoles('PloneMeeting: Add MeetingFile', ('Manager', ))
setDefaultRoles('PloneMeeting: Add MeetingAdvice', ('Manager',))

product_globals = globals()

# Dependencies of Products to be installed by quick-installer
# override in custom configuration
DEPENDENCIES = []

# Dependend products - not quick-installed - used in testcase
# override in custom configuration
PRODUCT_DEPENDENCIES = []

##code-section config-bottom #fill in your manual code here
# Define PloneMeeting-specific permissions
AddAnnex = 'PloneMeeting: Add annex'
setDefaultRoles(AddAnnex, ('Manager','Owner'))
# We need 'AddAnnex', which is a more specific permission than
# 'PloneMeeting: Add MeetingFile', because decision-related annexes, which are
# also MeetingFile instances, must be secured differently.
# There is no permission linked to annex deletion. Deletion of annexes is
# allowed if one has the permission 'Modify portal content' on the
# corresponding item.
ReadDecision = 'PloneMeeting: Read decision'
WriteDecision = 'PloneMeeting: Write decision'
ReadObservations = 'PloneMeeting: Read item observations'
ReadDecisionAnnex = 'PloneMeeting: Read decision annex'
WriteObservations = 'PloneMeeting: Write item observations'
WriteDecisionAnnex = 'PloneMeeting: Write decision annex'
CopyOrMove = 'Copy or Move'
setDefaultRoles(ReadDecision, ('Manager',))
setDefaultRoles(WriteDecision, ('Manager',))

MEETINGROLES = {'creators': 'MeetingMember',
                'reviewers': 'MeetingReviewer',
                'observers': 'MeetingObserverLocal',
                'advisers': 'MeetingAdviser'}

JAVASCRIPTS = [{'id': 'plonemeeting.js'},
               {'id': 'plonemeeting_javascript_variables.js'}]

ploneMeetingRoles = (
    'Manager', # The standard Plone 'Manager'
    'MeetingManager', # The important guy that creates and manages meetings
                      # (global role)
    'MeetingMember', # Guys that may create or update meeting items (local role
                     # within a group: they can only update items created by
                     # people belonging to the same group)
    'MeetingReviewer', # Guys that may review meeting items (local role within
                       # a group: they can only review items created by other
                       # people belonging to the same group)
    'MeetingObserverLocal', # Guys who may see items of people from
                            # their group (local role)
    'MeetingObserverLocalCopy', # Guys who may see items that the item creator
                            # has selected in the copyGroups box.
                            # This is a read-ony access to the item.
    'MeetingObserverGlobal', # Guy who may see meetings and items once
                             # published (global role)
    'MeetingAdviser', # Guy who is able to add an advice on a item (local role)
    )

# Roles that may create or edit item and/or meetings in PloneMeeting
ploneMeetingUpdaters = ('MeetingManager', 'Manager', 'Owner')

ROOT_FOLDER = "mymeetings"
MEETING_CONFIG = "meeting_config"

TOOL_ID = "portal_plonemeeting"
TOOL_FOLDER_CATEGORIES = 'categories'
TOOL_FOLDER_CLASSIFIERS = 'classifiers'
TOOL_FOLDER_RECURRING_ITEMS = "recurringitems"
TOOL_FOLDER_FILE_TYPES = 'meetingfiletypes'
TOOL_FOLDER_AGREEMENT_LEVELS = 'agreementlevels'
TOOL_FOLDER_POD_TEMPLATES = 'podtemplates'
TOOL_FOLDER_MEETING_USERS = 'meetingusers'

TOPIC_TYPE = 'meeting_topic_type'
TOPIC_SEARCH_SCRIPT = 'topic_search_script'
TOPIC_TAL_EXPRESSION = 'topic_tal_expression'

# If, for a topic, a specific script is used for the search, and if this topic
# does not define an "itemCount", we use this default value.
DEFAULT_TOPIC_ITEM_COUNT = 20

# Possible document types and formats for document generation
docActions = ('item_doc', 'meeting_doc')
mimeTypes = {'odt': 'application/vnd.oasis.opendocument.text',
             'doc': 'application/msword',
             'rtf': 'text/rtf',
             'pdf': 'application/pdf'}

# PloneMeeting portlets
ploneMeetingPortlets = ('here/portlet_todo/macros/portlet',
                        'here/portlet_meetingitems/macros/portlet',
                        'here/portlet_meetings/macros/portlet',
                        'here/portlet_decisions/macros/portlet',
                        'here/portlet_plonemeeting_navigation/macros/portlet')
DEPENDENCIES = ['kupu']

ITEM_NO_PREFERRED_MEETING_VALUE = "whatever"

HAS_PLONEPAS = False
try:
    from Products import PlonePAS
    HAS_PLONEPAS = True
except ImportError:
    pass

HAS_POD = False
try:
    import appy.pod.renderer
    HAS_POD = True
except ImportError:
    pass

STYLESHEETS = [{'id': 'plonemeeting.css',
                'title': 'PloneMeeting CSS styles'},
               {'id': 'meetingitem.css',
                'title': 'PloneMeeting CSS styles for MeetingItem',
                'expression': 'python: here.meta_type == "MeetingItem"'},
               {'id': 'meeting.css',
                'title': 'PloneMeeting CSS styles for Meeting',
                'expression': 'python: here.meta_type == "Meeting"'}]

# There are various ways to insert items into meetings
itemSortMethods = ( # Items are inserted:
    'at_the_end', # at the end of meetings;
    'on_categories', # according to category order;
    'on_proposing_groups', # according to proposing group order;
    'on_all_groups' # according to all groups (among proposing group AND
    # associated groups). Similar to the previous sort method, with this
    # difference: the group taken into consideration is the group among all
    # groups that comes first in the order.
)
# List of color system options : the way the item titles and annexes are colored
colorSystems = (
    'no_color', # nothing is colored
    'state_color', # the color follows the item state
    'modification_color' # the color depends on the fact that the current user
                         # has already viewed or not last modifications done on
                         # a given element (item/annex/advice...)
)

# "Missing advices" functionnality-related constants
LIST_ADVISERS_KEY = 'list_advisers'
MISSING_ADVICES_ID = 'no_advices'
MISSING_ADVICES_ICON_URL = 'no_advices.png'

NOT_ENCODED_VOTE_VALUE = 'not_yet'
NOT_CONSULTABLE_VOTE_VALUE = 'not_consultable'
##/code-section config-bottom


# Load custom configuration not managed by archgenxml
try:
    from Products.PloneMeeting.AppConfig import *
except ImportError:
    pass
