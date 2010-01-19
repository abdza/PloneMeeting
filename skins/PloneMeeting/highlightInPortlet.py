## Python Script "highlightInPortlet.py"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=currentObj, obj
##title=Return True if the element must be highlighted in the portlet meaning that it is the currently showed element

if hasattr(currentObj, 'UID'):
    return currentObj.UID() == obj.UID() 

return False