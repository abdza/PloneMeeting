## Script (Python) "searchItemsInCopy"
##title=Return a list of items in copy for the current user
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=topic,batch_size=0

#how does that search work?
#we will return every MeetingItemxxx for wich the current user groups ids match
#the getCopyGroups index...

REQUEST= context.REQUEST
if REQUEST is None:
    REQUEST = getattr(self, 'REQUEST', {})
meetingConfig = context.portal_plonemeeting.getMeetingConfig(context)
member = context.portal_membership.getAuthenticatedMember()
userGroups = context.portal_groups.getGroupsForPrincipal(member)

#check if the user is in the group of the selected copy groups
res = context.portal_catalog(portal_type=meetingConfig.getItemTypeName(), getCopyGroups=' OR '.join(userGroups))

return context.portal_plonemeeting.batchAdvancedSearch(res, topic, REQUEST, batch_size=batch_size)