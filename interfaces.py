# -*- coding: utf-8 -*-

from zope.interface import Interface

##code-section HEAD
##/code-section HEAD

class IMeetingItem(Interface):
    """Marker interface for .MeetingItem.MeetingItem
    """

class IMeeting(Interface):
    """Marker interface for .Meeting.Meeting
    """

class IToolPloneMeeting(Interface):
    """Marker interface for .ToolPloneMeeting.ToolPloneMeeting
    """

class IMeetingCategory(Interface):
    """Marker interface for .MeetingCategory.MeetingCategory
    """

class IMeetingConfig(Interface):
    """Marker interface for .MeetingConfig.MeetingConfig
    """

class IMeetingFileType(Interface):
    """Marker interface for .MeetingFileType.MeetingFileType
    """

class IMeetingFile(Interface):
    """Marker interface for .MeetingFile.MeetingFile
    """

class IMeetingGroup(Interface):
    """Marker interface for .MeetingGroup.MeetingGroup
    """

class IExternalApplication(Interface):
    """Marker interface for .ExternalApplication.ExternalApplication
    """

class IMeetingAdvice(Interface):
    """Marker interface for .MeetingAdvice.MeetingAdvice
    """

class IMeetingAdviceAgreementLevel(Interface):
    """Marker interface for .MeetingAdviceAgreementLevel.MeetingAdviceAgreementLevel
    """

class IPodTemplate(Interface):
    """Marker interface for .PodTemplate.PodTemplate
    """

class IMeetingUser(Interface):
    """Marker interface for .MeetingUser.MeetingUser
    """

##code-section FOOT
##/code-section FOOT