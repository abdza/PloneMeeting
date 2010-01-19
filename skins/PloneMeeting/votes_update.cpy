## Controller Python Script "update_votes.cpy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind state=state
##bind subpath=traverse_subpath
##parameters=
##title=Updates the votes encoded by the user.
from Products.CMFPlone import MessageFactory as _
rq = context.REQUEST

requestVotes = {}
secret = True
# If p_secret is True, we get vote counts. Else, we get vote values.
# In this case, we will count the total number of votes, to see if it
# corresponds to the number of voters.
numberOfVotes = 0

for key in rq.form.keys():
    if key.startswith('vote_value_'):
        voterId = key[11:]
        requestVotes[voterId] = rq[key]
        secret=False
    elif key.startswith('vote_count_'):
        # Check that the entered value is positive integer
        inError = False
        v = 0
        try:
            v = int(rq[key])
            if v < 0: inError = True
        except ValueError:
            inError = True
        if inError:
            msg= context.utranslate('vote_count_not_int', domain='PloneMeeting')
            context.plone_utils.addPortalMessage(msg)
            state.set(status='failure')
            return state
        numberOfVotes += v
        voteValue = key[11:]
        requestVotes[voteValue] = v

# Check the total number of votes
if secret:
    numberOfVoters = len(context.getMeetingUsers())
    if numberOfVotes != numberOfVoters:
        msg = context.utranslate('vote_count_wrong', domain='PloneMeeting')
        context.plone_utils.addPortalMessage(msg)
        state.set(status='failure')
        return state

# Update the vote values
if secret: context.updateVoteCounts(requestVotes)
else:      context.updateVoteValues(requestVotes)
state.set(status='success', portal_status_message="Changes made.")
return state
