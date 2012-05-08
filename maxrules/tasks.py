from celery.task import task
from maxrules.twitter import twitter_generator_name, debug_hashtag, max_server_url
import requests
import pymongo
from maxrules.config import mongodb_url, mongodb_db_name
from max.MADMax import MADMaxCollection
from max.rest.utils import canWriteInContexts
from max.rest.utils import findHashtags
import json
import logging
import max.models


@task
def processTweet(twitter_username, content):
    """ Process inbound tweet
    """
    conn = pymongo.Connection(mongodb_url)
    db = conn[mongodb_db_name]
    users = MADMaxCollection(db.users)
    contexts = MADMaxCollection(db.contexts)

    contexts_with_twitter_username = contexts.search({"twitterUsernameId": {"$exists": True}})
    readable_follow_list = [users_to_follow.get('twitterUsername').lower() for users_to_follow in contexts_with_twitter_username]

    # If we have a tweet from a followed user
    if twitter_username in readable_follow_list:
        # Find the context
        maxcontext = contexts.search({"twitterUsername": twitter_username})

        # Watch for the case when two or more context share twitterUsername
        for context in maxcontext:
            url_hash = context.get("urlHash")
            context_url = context.get("url")

            # Construct the payload with the activity information
            newactivity = {
                "object": {
                    "objectType": "note",
                    "content": content
                },
                "contexts": [
                    context_url,
                ],
                "generator": twitter_generator_name
            }

            re = requests.post('%s/admin/contexts/%s/activities' % (max_server_url, url_hash), json.dumps(newactivity), auth=('admin', 'admin'), verify=False)
            if re.status_code == 201:
                logging.warning("Successful %s tweet from context %s" % (twitter_username, context_url))
                #return "Successful %s tweet from context %s" % (twitter_username, context_url)
            else:
                logging.warning("Error accessing the MAX API at %s" % max_server_url)
                #return "Error accessing the MAX API at %s" % max_server_url
        return

    # If we have a tweet from a tracked hashtag
    # Parse text and determine the second or nth hashtag
    possible_hastags = findHashtags(content)
    query = [dict(twitterHashtag=hashtag) for hashtag in possible_hastags]

    if debug_hashtag in possible_hastags:
        return "Debug hastagh detected! %s" % content

    # Check if twitter_username is a registered for a valid MAX username
    # if not, discard it
    maxuser = users.search({"twitterUsername": twitter_username})
    if maxuser:
        maxuser = maxuser[0]
    else:
        return "Discarding %s tweet: Not such MAX user" % twitter_username

    # Check if hashtag is registered for a valid MAX context
    # if not, discard it
    maxcontext = contexts.search({"$or": query})
    if maxcontext:
        for context in maxcontext:
            # Check if MAX username has permission to post to the MAX context
            # if not, discard it
            try:
                can_write = canWriteInContexts(maxuser, [context.url])
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
                    context.url,
                ],
                "generator": twitter_generator_name
            }

            # Use the restricted REST endpoint for create a new activity in the specified
            # MAX context in name of the specified MAX username
            re = requests.post('%s/admin/people/%s/activities' % (max_server_url, maxuser.username), json.dumps(newactivity), auth=('admin', 'admin'), verify=False)
            if re.status_code == 201:
                logging.warning("Success tweet from user %s in context %s" % (maxuser, context.url))
                #return "Success tweet from user %s in context %s" % (maxuser, context.url)
            else:
                logging.warning("Error accessing the MAX API at %s" % max_server_url)
                #return "Error accessing the MAX API at %s" % max_server_url
        return
    else:
        return "Discarding %s tweet: Not such MAX context" % maxuser.username
