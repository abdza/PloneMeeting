## Script (Python) "showPasteMeetingItemAction"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=

#show the action if :
#we have a content to paste
if not context.cb_dataValid():
    return False

#we are in PloneMeeting
meetingConfig = context.portal_plonemeeting.getMeetingConfig(context)
if not meetingConfig:
    return False

#the duplication is activated in the meetingConfig
if not meetingConfig.getEnableDuplication():
    return False

return True