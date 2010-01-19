## Script (Python) "getBrainsForPortletTodo"
##title=Get brains from a topic evaluating the topic.queryCatalog or the search script
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=topic

if hasattr(topic, 'topic_search_script'):
    scriptId = topic.topic_search_script
    if len(scriptId):
        return getattr(context, scriptId)(topic,batch_size=3)

return topic.queryCatalog(b_size=3, batch=True)