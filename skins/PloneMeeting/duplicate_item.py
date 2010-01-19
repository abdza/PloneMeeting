## Script (Python) "duplicate_item"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=

newItem = context.clone(copyAnnexes=False, copyAdvices=False)
urlBack = newItem.absolute_url()

# Remove previous message if one was there
i = urlBack.find('portal_status_message')
if i != -1:
    urlBack = urlBack[:i].strip('?&')

# Add the message to the urlBack
sep = '/?'
msg = 'item_duplicated'
if urlBack.find('?') != -1:
    sep = '&'
urlBack = '%s%sportal_status_message=%s' % (urlBack, sep, msg)
return context.REQUEST.RESPONSE.redirect(urlBack)
