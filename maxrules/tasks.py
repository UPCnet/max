from celery.task import task
from maxrules.twitter import twitter_generator_name
import requests
import pymongo
from maxrules.config import mongodb_url, mongodb_db_name
from max.MADMax import MADMaxCollection
from max.rest.utils import canWriteInContexts


@task
def processTweet(twitter_username, hashtag, content):
    """ Process inbound tweet
    """
    conn = pymongo.Connection(mongodb_url)
    db = conn[mongodb_db_name]
    users = MADMaxCollection(db.users)
    contexts = MADMaxCollection(db.contexts)

    # Check if twitter_username is a registered for a valid MAX username
    # if not, discard it
    maxuser = users.getItemsBytwitterUsername(twitter_username)
    if maxuser:
        maxuser = maxuser[0]
    else:
        return "Discarding %s tweet: Not such MAX user" % twitter_username

    # Check if hashtag is registered for a valid MAX context
    # if not, discard it
    maxcontext = contexts.getItemsBytwitterHashtag(hashtag)
    if maxcontext:
        maxcontext = maxcontext[0]
    else:
        return "Discarding %s tweet: Not such MAX context" % maxuser.username

    # Check if MAX username has permission to post to the MAX context
    # if not, discard it
    try:
        can_write = canWriteInContexts(maxuser, [maxcontext.url])
    except:
        can_write = False

    if not can_write:
        return "Discarding %s tweet: MAX user can't write to specified MAX context" % maxuser.username

    # Construct the payload with the activity information
    newactivity = {
        "object": {
            "objectType": "note",
            "content": content
        },
        "contexts": [
            maxcontext.url,
        ],
        "generator": twitter_generator_name
    }

    # Use the restricted REST endpoint for create a new activity in the specified
    # MAX context in name of the specified MAX username

    re = requests.post('/admin/people/%s/activities' % maxuser.username, newactivity, auth=('admin', 'admin'))

    return "Successful tweet insertion from user %s in context %s" % (maxuser, maxcontext)
