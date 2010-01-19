## Python Script "doSystemAction"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Show the rename form for an object
##
rq = context.REQUEST
if rq.get('reindexAnnexes', ''):
    # Reindex annexes
    for b in context.portal_catalog(meta_type='MeetingItem'):
        b.getObject().updateAnnexIndex()
context.plone_utils.addPortalMessage('Done.')
rq.RESPONSE.redirect(rq['HTTP_REFERER'])
