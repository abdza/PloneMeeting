# -*- coding: utf-8 -*-
#
# File: MeetingFile.py
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
import os, os.path, time, unicodedata
from Globals import InitializeClass
from Products.CMFCore.permissions import View
from Products.ATContentTypes.content.file import ATFile, ATFileSchema
from Products.PloneMeeting.utils import clonePermissions, getCustomAdapter, \
     getOsTempFolder, HubSessionsMarshaller
import logging
logger = logging.getLogger('PloneMeeting')

# Marshaller -------------------------------------------------------------------
class MeetingFileMarshaller(HubSessionsMarshaller):
    '''Allows to marshall a meetin file into a XML file.'''
    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')
    fieldsToMarshall = 'all_with_metadata'
    rootElementName = 'meetingFile'

    def marshallSpecificElements(self, mf, res):
        HubSessionsMarshaller.marshallSpecificElements(self, mf, res)
        self.dumpField(res, 'pm_modification_date', mf.pm_modification_date)

InitializeClass(MeetingFileMarshaller)

# Error-related constants ------------------------------------------------------
UNSUPPORTED_FORMAT_FOR_OCR = 'File "%s" could not be OCR-ized because mime ' \
    'type "%s" is not a supported input format. Supported input formats ' \
    'are: %s; %s.'
DUMP_FILE_ERROR = 'Error occurred while dumping or removing file "%s" on ' \
    'disk. %s'
GS_ERROR = 'An error occurred when using Ghostscript to convert "%s". Note ' \
    'that program "gs" must be in path.'
TESSERACT_ERROR = 'An error occurred when using Tesseract to OCR-ize file ' \
    '"%s". Note that program "tesseract" must be in path.'

GS_TIFF_COMMAND = 'gs -q -dNOPAUSE -dBATCH -sDEVICE=tiffg4 ' \
    '-sOutputFile=%s/%%04d.tif %s -c quit'
GS_INFO_COMMAND = 'Launching Ghoscript: %s'
TESSERACT_COMMAND = 'tesseract %s %s -l %s'
TESSERACT_INFO_COMMAND = 'Launching Tesseract: %s'
##/code-section module-header

schema = Schema((

    ReferenceField(
        name='meetingFileType',
        widget=ReferenceField._properties['widget'](
            label='Meetingfiletype',
            label_msgid='PloneMeeting_label_meetingFileType',
            i18n_domain='PloneMeeting',
        ),
        required=True,
        relationship="MeetingFileType"
    ),

    TextField(
        name='extractedText',
        index="ZCTextIndex, lexicon_id=plone_lexicon, index_type=Okapi BM25 Rank",
        widget=TextAreaWidget(
            label='Extractedtext',
            label_msgid='PloneMeeting_label_extractedText',
            i18n_domain='PloneMeeting',
        )
    ),

),
)

##code-section after-local-schema #fill in your manual code here
##/code-section after-local-schema

MeetingFile_schema = ATFileSchema.copy() + \
    schema.copy()

##code-section after-schema #fill in your manual code here
# Integrate potential extensions from PloneMeeting sub-products
from Products.PloneMeeting.model.extender import ModelExtender
MeetingFile_schema = ModelExtender(MeetingFile_schema, 'file').run()
# Register the marshaller for DAV/XML export.
MeetingFile_schema.registerLayer('marshall', MeetingFileMarshaller())
##/code-section after-schema

class MeetingFile(ATFile):
    """
    """
    security = ClassSecurityInfo()
    __implements__ = (getattr(ATFile,'__implements__',()),)

    # This name appears in the 'add' box
    archetype_name = 'MeetingFile'

    meta_type = 'MeetingFile'
    portal_type = 'MeetingFile'
    allowed_content_types = []
    filter_content_types = 0
    global_allow = 1
    #content_icon = 'MeetingFile.gif'
    immediate_view = 'base_view'
    default_view = 'base_view'
    suppl_views = ()
    typeDescription = "MeetingFile"
    typeDescMsgId = 'description_edit_meetingfile'


    actions =  (


       {'action': "string:${object_url}/file_view",
        'category': "object",
        'id': 'view',
        'name': 'View',
        'permissions': ("View",),
        'condition': 'python:not here.portal_factory.isTemporary(here)'
       },


    )

    _at_rename_after_creation = True

    schema = MeetingFile_schema

    ##code-section class-header #fill in your manual code here
    aliases = {
        '(Default)'  : '(dynamic view)',
        'view'       : 'file_view',
        'index.html' : '(dynamic view)',
        'edit'       : 'atct_edit',
        'properties' : 'base_metadata',
        'sharing'    : 'folder_localrole_form',
        'gethtml'    : '',
        'mkdir'      : '',
        }
    ocrFormatsOk = ('image/tiff',)
    ocrFormatsOkButConvertNeeded = ('application/pdf',)
    ocrAllFormatsOk = ocrFormatsOk + ocrFormatsOkButConvertNeeded
    ##/code-section class-header

    # Methods

    # Manually created methods

    security.declarePublic('getIcon')
    def getIcon(self, relative_to_portal=0):
        '''Calculate the icon using the meetingFileType icon.'''
        field = self.getField('file')
        if not field:
            # field is empty
            return BaseContent.getIcon(self, relative_to_portal)
        mtf = self.getMeetingFileType()
        if mtf:
            return mtf.absolute_url(relative=1) + "/theIcon"
        else:
            return None

    security.declarePublic('getBestIcon')
    def getBestIcon(self):
        '''Calculates the icon for the AT default view'''
        self.getIcon()

    security.declarePublic('getItem')
    def getItem(self):
        '''Returns the linked item.'''
        # getBRefs returns links of the ReferenceField
        res = self.getBRefs('ItemAnnexes')
        if res:
            res = res[0]
        else:
            res = self.getBRefs('DecisionAnnexes')
            if res:
                res = res[0]
        return res

    security.declarePublic('updateAnnexSecurity')
    def updateAnnexSecurity(self):
        '''Applies the same security settings to this annex than those of its
           linked item. By "security settings", we mean "Which role(s) have
           which permissions".

           No workflow is defined on MeetingFiles, but when a MeetingFile is
           linked to a MeetingItem, we want the file to have the same
           permissions as the item. So in the MeetingItem workflow, every time
           a transition is triggered, we update the security settings of the
           MeetingFile.'''
        item = self.getItem()
        if item:
            clonePermissions(item, self)

    security.declareProtected(View, 'index_html')
    def index_html(self, REQUEST=None, RESPONSE=None):
        '''Download the file'''
        self.portal_plonemeeting.rememberAccess(self.UID())
        return ATFile.index_html(self, REQUEST, RESPONSE)

    security.declarePublic('at_post_create_script')
    def at_post_create_script(self):
        # We define here a PloneMeeting-specific modification date for this
        # annex. Indeed, we can't use the standard Plone modification_date for
        # the PloneMeeting color system because some events like item state
        # changes update security settings on annexes and modification_date is
        # updated.
        self.pm_modification_date = self.modification_date
        self.updateAnnexSecurity()
        self.portal_plonemeeting.rememberAccess(self.UID(), commitNeeded=False)
        item = self.getItem()
        if item:
            item.updateAnnexIndex(self)
            item.alreadyUsedAnnexNames.append(self.id)
        self.adapted().onEdit(isCreated=True) # Call su-product code if any

    security.declarePrivate('at_post_edit_script')
    def at_post_edit_script(self): self.adapted().onEdit(isCreated=False)

    security.declarePublic('isDecisionRelated')
    def isDecisionRelated(self):
        if self.reference_catalog.getBackReferences(self, 'ItemAnnexes'):
            return False
        else: return True

    security.declarePublic('getAnnexInfo')
    def getAnnexInfo(self):
        '''Produces a dict with some useful info about this annex. This is
           used for indexing purposes (see method updateAnnexIndex in
           MeetingItem.py).'''
        fileType = self.getMeetingFileType()
        res = {'Title': self.Title(),
               'url': self.absolute_url_path(),
               'uid': self.UID(),
               'fileTypeId': fileType.id,
               'iconUrl': fileType.absolute_url_path() + '/theIcon',
               'modification_date': self.pm_modification_date,
               'decisionRelated': self.isDecisionRelated()
               }
        return res

    security.declarePublic('getSelf')
    def getSelf(self):
        if self.__class__.__name__ != 'MeetingFile': return self.context
        return self

    security.declarePublic('adapted')
    def adapted(self): return getCustomAdapter(self)

    security.declareProtected('Modify portal content', 'onEdit')
    def onEdit(self, isCreated): '''See doc in interfaces.py.'''

    security.declarePrivate('dump')
    def dump(self):
        '''Dumps me on disk, in a temp folder, with some unique name
           including time.time(). This method returns the absolute filename
           of the dumped file.'''
        tempFolder = getOsTempFolder()
        fileName = unicodedata.normalize(
            'NFKD', self.getFilename().decode('utf-8'))
        fileName = fileName.encode("ascii", "ignore").replace(' ', '')
        tempFileName = '%s/f%f.%s' % (tempFolder, time.time(), fileName)
        f = file(tempFileName, 'w'); f.write(self.data); f.close()
        return tempFileName

    security.declareProtected('Modify portal content', 'extractText')
    def extractText(self, needsOcr, ocrLanguage):
        '''This method extracts text from this file and stores it in field
           "extractedText". If p_needsOcr is True, it does OCR recognition
           by calling command-line programs Ghostscript (gs) and Tesseract
           (tesseract). Ghostscript is used for converting a file into
           images and Tesseract is the OCR engine that converts those images
           into text. Tesseract needs to know in what p_ocrLanguage the file
           is written.'''
        if needsOcr:
            mimeType = self.content_type
            if mimeType in self.ocrAllFormatsOk:
                try:
                    fileName = self.dump() # Dumps me on disk first
                    tifFolder = None
                    if mimeType in self.ocrFormatsOkButConvertNeeded:
                        # I will first use Ghostscript to convert the file to
                        # "tiff" format. I will create a folder where
                        # Ghostscript will generate one tiff file per PDF page.
                        tifFolder = os.path.splitext(fileName)[0] + '.folder'
                        os.mkdir(tifFolder)
                        cmd = GS_TIFF_COMMAND % (tifFolder, fileName)
                        logger.info(GS_INFO_COMMAND % cmd)
                        os.system(cmd)
                        tifFiles = ['%s/%s' % (tifFolder, f) for f in \
                                    os.listdir(tifFolder)]
                        if not tifFiles:
                            logger.warn(GS_ERROR % (fileName))
                    else:
                        tifFiles = [fileName]
                    tifFiles.sort()
                    # Launch the OCR engine
                    extractedText = ''
                    for tifFile in tifFiles:
                        resFile = os.path.splitext(tifFile)[0]
                        resFilePlusExt = resFile + '.txt'
                        cmd = TESSERACT_COMMAND % (tifFile,resFile,ocrLanguage)
                        logger.info(TESSERACT_INFO_COMMAND % cmd)
                        os.system(cmd)
                        if not os.path.exists(resFilePlusExt):
                            logger.warn(TESSERACT_ERROR % tifFile)
                        else:
                            f = file(resFilePlusExt)
                            extractedText += f.read()
                            f.close()
                            os.remove(resFilePlusExt)
                        os.remove(tifFile)
                    self.setExtractedText(extractedText)
                    if tifFolder:
                        os.removedirs(tifFolder)
                    os.remove(fileName)
                except OSError, oe:
                    logger.warn(DUMP_FILE_ERROR % (self.getFilename(), str(oe)))
                except IOError, ie:
                    logger.warn(DUMP_FILE_ERROR % (self.getFilename(), str(ie)))
            else:
                logger.warn(UNSUPPORTED_FORMAT_FOR_OCR % (self.getFilename(),
                    mimeType, self.ocrFormatsOk,
                    self.ocrFormatsOkButConvertNeeded))
            self.reindexObject()



registerType(MeetingFile, PROJECTNAME)
# end of class MeetingFile

##code-section module-footer #fill in your manual code here
##/code-section module-footer



