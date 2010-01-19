## Python Script "meeting_triggertransition.py"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=itemUid,transition
##title=Triggers a transition on an item in an items list

from Products.CMFPlone import PloneMessageFactory as _
item = context.uid_catalog(UID=itemUid)[0].getObject()
context.portal_workflow.doActionFor(item, transition)
msg = _('%s_done_descr' % transition, default=u'Your content\'s status has been modified.')
context.plone_utils.addPortalMessage(msg)
return context.portal_plonemeeting.gotoReferer()