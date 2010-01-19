## Script (Python) "paste_items"
##bind container=container
##bind context=context
##bind namespace=
##bind state=state
##bind script=script
##bind subpath=traverse_subpath
##parameters=
##title=Paste meetingItems into the parent/this folder
##

from AccessControl import Unauthorized
from ZODB.POSException import ConflictError
from Products.CMFPlone import PloneMessageFactory as _

if context.cb_dataValid:
    try:
        context.portal_plonemeeting.pasteItems(context, context.REQUEST['__cp'])
        context.plone_utils.addPortalMessage(_(u'Item(s) pasted.'))
        return state
    except ConflictError:
        raise
    except ValueError:
        msg=_(u'Disallowed to paste item(s).')
    except (Unauthorized, 'Unauthorized'):
        msg=_(u'Unauthorized to paste item(s).')
    except: # fallback
        msg=_(u'Paste could not find clipboard content.')

context.plone_utils.addPortalMessage(msg)
return state.set(status='failure')
