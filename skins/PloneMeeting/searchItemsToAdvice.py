## Script (Python) "searchItemsToAdvice"
##title=Return a list of items that the current user has to give an advice for
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=topic,batch_size=0

#how does that search work?
#we will return every MeetingItemxxx for wich the current user groups ids match
#the indexAdvisers index...

REQUEST= context.REQUEST
if REQUEST is None:
    REQUEST = getattr(self, 'REQUEST', {})
meetingConfig = context.portal_plonemeeting.getMeetingConfig(context)
member = context.portal_membership.getAuthenticatedMember()
userGroups = context.portal_groups.getGroupsForPrincipal(member)

#add a '0' at the end meaning that we want not given advices
groups = []
for gr in userGroups:
    groups.append(gr+'0')
#check if the user is in the indexAdvisers index
review_states_to_search = meetingConfig.getStatesToSearch("MeetingAdviser", "PloneMeeting: Add MeetingAdvice")
res = context.portal_catalog(portal_type=meetingConfig.getItemTypeName(), indexAdvisers=' OR '.join(groups), review_state=review_states_to_search, sort_on="created", sort_order="reverse")

return context.portal_plonemeeting.batchAdvancedSearch(res, topic, REQUEST, batch_size=batch_size)