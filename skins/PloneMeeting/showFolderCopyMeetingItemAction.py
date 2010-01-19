## Script (Python) "showFolderCopyMeetingItemAction"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=

#we are in PloneMeeting
meetingConfig = context.portal_plonemeeting.getMeetingConfig(context)
if not meetingConfig:
    return False

#the duplication is activated in the meetingConfig
if not meetingConfig.getEnableDuplication():
    return False

return True