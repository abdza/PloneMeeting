# -*- coding: utf-8 -*-
#
# File: PodTemplate.py
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
import os, time
from Globals import InitializeClass
from StringIO import StringIO
from Products.PloneMeeting.utils import getOsTempFolder, sendMail
from Products.PloneMeeting import PloneMeetingError
from Products.PloneMeeting.utils import \
     clonePermissions, getCustomAdapter, HubSessionsMarshaller
from Products.CMFCore.Expression import Expression, createExprContext
from Products.CMFCore.utils import getToolByName
from AccessControl import Unauthorized
import logging
logger = logging.getLogger('PloneMeeting')

# Marshaller -------------------------------------------------------------------
class PodTemplateMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a POD template into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all'
    rootElementName = 'podTemplate'
InitializeClass(PodTemplateMarshaller)
##/code-section module-header

schema = Schema((

    TextField(
        name='description',
        widget=TextAreaWidget(
            description="PodTemplateDescription",
            description_msgid="pod_template_description",
            label_msgid="podtemplate_label_description",
            label='Description',
            i18n_domain='PloneMeeting',
        ),
        accessor="Description"
    ),

    FileField(
        name='podTemplate',
        widget=FileWidget(
            description="PodTemplate",
            description_msgid="pod_template_descr",
            label='Podtemplate',
            label_msgid='PloneMeeting_label_podTemplate',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        storage=AttributeStorage()
    ),

    StringField(
        name='podFormat',
        default="odt",
        widget=SelectionWidget(
            description="PodFormat",
            description_msgid="pod_format_doc",
            label='Podformat',
            label_msgid='PloneMeeting_label_podFormat',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        vocabulary='listPodFormats',
        required=True
    ),

    StringField(
        name='podCondition',
        widget=StringWidget(
            size=100,
            description="PodCondition",
            description_msgid="pod_condition_descr",
            label='Podcondition',
            label_msgid='PloneMeeting_label_podCondition',
            i18n_domain='PloneMeeting',
        )
    ),

    LinesField(
        name='podPermission',
        default="View",
        widget=MultiSelectionWidget(
            description="PodPermission",
            description_msgid="pod_permission_descr",
            size=10,
            label='Podpermission',
            label_msgid='PloneMeeting_label_podPermission',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary=True,
        multiValued=1,
        vocabulary='listPodPermissions'
    ),

    StringField(
        name='freezeEvent',
        widget=SelectionWidget(
            description="FreezeEvent",
            description_msgid="freeze_event_descr",
            label='Freezeevent',
            label_msgid='PloneMeeting_label_freezeEvent',
            i18n_domain='PloneMeeting',
        ),
        enforceVocabulary= True,
        vocabulary='listFreezeEvents'
    ),

),
)

##code-section after-local-schema #fill in your manual code here
# Error-related constants ------------------------------------------------------
POD_ERROR = 'An error occurred while generating the document. Please check ' \
            'the following things if you wanted to generate the document in ' \
            'PDF, DOC or RTF: (1) OpenOffice is started in server mode on ' \
            'the port you should have specified in the PloneMeeting ' \
            'configuration (go to Site setup-> PloneMeeting configuration); ' \
            '(2) if the Python interpreter running Zope and ' \
            'Plone is not able to discuss with OpenOffice (it does not have ' \
            '"uno" installed - check it by typing "import uno" at the Python ' \
            'prompt) please specify, in the PloneMeeting configuration, ' \
            'the path to a UNO-enabled Python interpreter (ie, the Python ' \
            'interpreter included in the OpenOffice distribution, or, if ' \
            'your server runs Ubuntu, the standard Python interpreter ' \
            'installed in /usr/bin/python). Here is the error as reported ' \
            'by the appy.pod library:\n\n %s'
DELETE_TEMP_DOC_ERROR = 'A temporary document could not be removed. %s.'
##/code-section after-local-schema

PodTemplate_schema = BaseSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
from Products.PloneMeeting.model.extender import ModelExtender
PodTemplate_schema = ModelExtender(PodTemplate_schema, 'pod').run()
# Register the marshaller for DAV/XML export.
PodTemplate_schema.registerLayer('marshall', PodTemplateMarshaller())
##/code-section after-schema

class PodTemplate(BaseContent):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(BaseContent,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'PodTemplate'

    meta_type = 'PodTemplate'
    portal_type = 'PodTemplate'
    allowed_content_types = []
    filter_content_types = 0
    global_allow = 1
    #content_icon = 'PodTemplate.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "PodTemplate"
    typeDescMsgId = 'description_edit_podtemplate'

    _at_rename_after_creation = True

    schema = PodTemplate_schema

    ##code-section class-header #fill in your manual code here
    podFormats = ( ("doc", "Microsoft Word"),
                   ("odt", "Open Document Format (text)"),
                   ("rtf", "Rich Text Format (RTF)"),
                   ("pdf", "Adobe PDF") )
    BAD_CONDITION = 'Condition "%s" on POD template produced an error. %s'
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePrivate('listPodFormats')
    def listPodFormats(self):
        return DisplayList(self.podFormats)

    security.declarePrivate('listPodPermissions')
    def listPodPermissions(self):
        res = []
        for permission in self.portal_controlpanel.possible_permissions():
            res.append( (permission, permission) )
        return DisplayList(tuple(res))

    security.declarePublic('isApplicable')
    def isApplicable(self, obj):
        '''May the current user use this template for generating documents ?'''
        user = self.portal_membership.getAuthenticatedMember()
        res = False
        # Check permissions
        isAllowed = True
        for podPermission in self.getPodPermission():
            if not user.has_permission(podPermission, obj):
                isAllowed = False
                break
        if isAllowed:
            res = True # At least for now
            # Check condition
            if self.getPodCondition().strip():
                portal = getToolByName(self, 'portal_url').getPortalObject()
                ctx = createExprContext(obj.getParentNode(), portal, obj)
                try:
                    res = Expression(self.getPodCondition())(ctx)
                except Exception, e:
                    logger.warn(self.BAD_CONDITION % (self.getPodCondition(),
                                str(e)))
                    res = False
        return res

    security.declarePublic('getDocumentId')
    def getDocumentId(self, obj):
        '''Returns the id of the document that may be produced in the
           database from p_self and p_obj.'''
        return '%s_%s.%s' % (obj.id, self.id, self.getPodFormat())

    security.declarePrivate('meetingIsDecided')
    def meetingIsDecided(self, obj):
        '''Is the meeting decided ?'''
        res = False
        if obj.meta_type == 'Meeting':
            res = obj.adapted().isDecided()
        else: # It is a meeting item
            if obj.hasMeeting() and obj.getMeeting().adapted().isDecided():
                res = True
        return res

    security.declarePublic('generateDocument')
    def generateDocument(self, obj, itemUids=None, forBrowser=True):
        '''Generates a document from this template, for object p_obj. If p_obj
           is a meeting, p_itemUids contains the UIDs of the items to dump
           into the document (which is a subset of all items linked to this
           meeting).

           If p_forBrowser is True, this method produces a valid output for
           browsers (setting HTTP headers, etc). Else, it returns the raw
           document content.'''
        tool = self.portal_plonemeeting
        if not HAS_POD:
            raise PloneMeetingError(self.utranslate('pod_not_installed',
                                    domain='PloneMeeting'))
        meetingConfig = tool.getMeetingConfig(obj)
        if itemUids:
            itemUids = itemUids.split(',')
        # Temporary file where to generate the result
        tempFileName = '%s/%s_%f.%s' % (
            getOsTempFolder(), obj.UID(), time.time(), self.getPodFormat())
        # Define parameters to pass to the appy.pod renderer
        currentUser = self.portal_membership.getAuthenticatedMember()
        podContext = {'self': obj,
                      'meetingConfig': meetingConfig,
                      'meetingIsDecided': self.meetingIsDecided(obj),
                      'itemUids': itemUids,
                      'user': currentUser,
                      'podTemplate': self
                      }
        podContext.update(obj.adapted().getSpecificDocumentContext())
        rendererParams = { 'template': StringIO(self.getPodTemplate()),
                           'context': podContext,
                           'result': tempFileName }
        if tool.getUnoEnabledPython():
            rendererParams['pythonWithUnoPath'] = tool.getUnoEnabledPython()
        if tool.getOpenOfficePort():
            rendererParams['ooPort'] = tool.getOpenOfficePort()
        # Launch the renderer
        import appy.pod
        try:
            renderer = appy.pod.renderer.Renderer(**rendererParams)
            renderer.run()
        except appy.pod.PodError, pe:
            if not os.path.exists(tempFileName):
                # In some (most?) cases, when OO returns an error, the result is
                # nevertheless generated.
                raise PloneMeetingError(POD_ERROR % str(pe))
        # Open the temp file on the filesystem
        f = file(tempFileName, 'rb')
        if forBrowser:
            # Create a OFS.Image.File object that will manage correclty HTTP
            # headers, etc.
            from OFS.Image import File
            theFile = File('dummyId', 'dummyTitle', f,
                           content_type=mimeTypes[self.getPodFormat()])
            res = theFile.index_html(self.REQUEST, self.REQUEST.RESPONSE)
            # Before, I used the code below to set the HTTP headers.
            # But I've noticed that with some browsers (guess which one?) the
            # returned document could not be opened. Worse: the browser crashed
            # completely in some cases. So now I rely on File.index_html
            # instead. One caveat: the title of the file is "generateDocument-X'
            # and not a friendly title as before...
            #response = obj.REQUEST.RESPONSE
            #response.setHeader('Content-type', mimeTypes[self.getPodFormat()])
            #response.setHeader('Content-disposition',
            #                   'inline;filename="%s.%s"' % (
            #                       obj.Title(), self.getPodFormat()))
        else:
            # I must return the raw document content.
            res = f.read()
        f.close()
        # Returns the doc and removes the temp file
        try:
            os.remove(tempFileName)
        except OSError, oe:
            logger.warn(DELETE_TEMP_DOC_ERROR % str(oe))
        return res

    security.declarePrivate('listFreezeEvents')
    def listFreezeEvents(self):
        meetingConfig = self.getParentNode()
        res = [('', self.utranslate('no_freeze_event',
                                    domain='PloneMeeting'))]
        for id, text in meetingConfig.listTransitions('Meeting'):
            res.append(('pod_meeting_%s' % id, 'Meeting->%s' % text))
        for id, text in meetingConfig.listTransitions('Item'):
            res.append(('pod_item_%s' % id, 'Item->%s' % text))
        return DisplayList(tuple(res))

    security.declarePrivate('at_post_create_script')
    def at_post_create_script(self): self.adapted().onEdit(isCreated=True)

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self): self.adapted().onEdit(isCreated=False)

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'PodTemplate': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''



registerType(PodTemplate, PROJECTNAME)
# end of class PodTemplate

##code-section module-footer #fill in your manual code here
CANT_WRITE_DOC = 'User "%s" was not authorized to create file "%s" ' \
                 'in folder "%s" from template "%s".'
def freezePodDocumentsIfRelevant(obj, transition):
    '''p_transitions just occurred on p_obj. Is there any document that needs
       to be generated in the database from a POD template?'''
    meetingConfig = obj.portal_plonemeeting.getMeetingConfig(obj)
    user = obj.portal_membership.getAuthenticatedMember()
    podTemplatesFolder = getattr(meetingConfig, TOOL_FOLDER_POD_TEMPLATES)
    for podTemplate in podTemplatesFolder.objectValues():
        if (transition == podTemplate.getFreezeEvent()) and \
           podTemplate.isApplicable(obj):
            # I must dump a document in the DB based on this template and
            # object.
            fileId = podTemplate.getDocumentId(obj)
            folder = obj.getParentNode()
            existingDoc = getattr(folder, fileId, None)
            # If the doc was already generated, we do not rewrite it.
            # This way, if some doc generations crash, when retrying them
            # the already generated docs are not generated again.
            if not existingDoc:
                try:
                    docContent = podTemplate.generateDocument(obj,
                                                              forBrowser=False)
                    folder.invokeFactory('File', id=fileId, file=docContent)
                    doc = getattr(folder, fileId)
                    doc.setFormat(mimeTypes[podTemplate.getPodFormat()])
                    doc.setTitle('%s (%s)' % (obj.Title(), podTemplate.Title()))
                    clonePermissions(obj, doc)
                except PloneMeetingError, pme:
                    # Probably some problem while contacting OpenOffice.
                    logger.warn(str(pme))
                    portal = obj.portal_url.getPortalObject()
                    sendMail([portal.getProperty('email_from_address')],
                             obj, "documentGenerationFailed")
                except Unauthorized, ue:
                    logger.warn(CANT_WRITE_DOC % (
                        user.id, fileId, folder.absolute_url(), podTemplate.id))
##/code-section module-footer



