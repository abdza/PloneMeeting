## Script (Python) "ajaxget_data.py"
##title=Returns some data about a meeting configuration
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=configId, data

meetingConfig = getattr(context.portal_plonemeeting, configId)
objectFolder = getattr(meetingConfig, data)

if data == 'categories':
    res = '<select name="categories" multiple="multiple" size="7">'
elif data == 'classifiers':
    res = '<select name="classifiers" multiple="multiple" size="7">'

for obj in objectFolder.objectValues():
    if data == 'categories':
        objectId = obj.id
    elif data == 'classifiers':
        objectId = obj.UID()
    res += '<option value="%s">%s</option>\n' % (objectId, obj.Title())

if data == 'categories': res += '</select>'
elif data == 'classifiers': res += '</select>'
if not res: res = ' '
context.REQUEST.RESPONSE.setHeader('Content-Type','charset=utf-8')
return res
