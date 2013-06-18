import os
from celery.task import task
from maxrules.twitter import twitter_generator_name, debug_hashtag, max_server_url
import requests
import pymongo
from maxrules.config import mongodb_url, mongodb_db_name, mongodb_cluster, mongodb_hosts, mongodb_replica_set
from max.MADMax import MADMaxCollection
from max.rest.utils import canWriteInContexts
from max.rest.utils import findHashtags
import json
import logging


logging_file = '/var/pyramid/maxserver/var/log/twitter-processor.log'

# Temporary patch to avoid tests failure
if not os.path.exists(logging_file):  # pragma: no cover
    logging_file = '/tmp/twitter-processor.log'
logger = logging.getLogger("tweetprocessor")
fh = logging.FileHandler(logging_file, encoding="utf-8")
formatter = logging.Formatter('%(asctime)s %(message)s')
logger.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)


@task
def processTweet(twitter_username, content, tweetID='---'):
    """ Process inbound tweet
    """
    # Setup logging
    logger.info(u"(INFO) Processing tweet %s from %s with content: %s" % (str(tweetID), twitter_username, content))

    # DB connection
    if not mongodb_cluster:
        conn = pymongo.MongoClient(mongodb_url)
    else:
        conn = pymongo.MongoReplicaSetClient(mongodb_hosts, mongodb_replica_set)

    db = conn[mongodb_db_name]
    users = MADMaxCollection(db.users)
    contexts = MADMaxCollection(db.contexts)

    contexts_with_twitter_username = contexts.search({"twitterUsernameId": {"$exists": True}})
    readable_follow_list = [users_to_follow.get('twitterUsername', '').lower() for users_to_follow in contexts_with_twitter_username]
    twitter_username = twitter_username.lower()
    # If we have a tweet from a followed user
    if twitter_username in readable_follow_list:
        # Find the context
        maxcontext = contexts.search({"twitterUsername": twitter_username})

        # Watch for the case when two or more context share twitterUsername
        for context in maxcontext:
            url_hash = context.get("hash")
            context_url = context.get("url")

            # Construct the payload with the activity information
            newactivity = {
                "object": {
                    "objectType": "note",
                    "content": content
                },
                "contexts": [{'url': context_url,
                              'objectType': 'context'
                              }
                             ],
                "generator": twitter_generator_name
            }

            re = requests.post('%s/contexts/%s/activities' % (max_server_url, url_hash), json.dumps(newactivity), auth=('admin', 'admin'), verify=False)
            if re.status_code == 201:
                # 200: Successful tweet from context
                logger.info(u"(201) Successfully posted tweet %s from %s as context %s" % (str(tweetID), twitter_username, context_url))
                return u"(201) %s tweet from context %s" % (twitter_username, context_url)
            else:  # pragma: no cover
                # 500: Error accessing the MAX API
                logger.info(u"(500) Error accessing the MAX API at %s" % max_server_url)
                return u"(500) MAX API error"

        return u"Should not see me..."  # pragma: no cover

    # If we have a tweet from a tracked hashtag
    # Parse text and determine the second or nth hashtag
    possible_hastags = findHashtags(content)
    # Normalize possible_hastags
    #possible_hastags = [hashtag.lower() for hashtag in possible_hastags]
    # Prepare query with normalized possible_hastags

    query = [dict(twitterHashtag=hashtag.lower()) for hashtag in possible_hastags]

    if debug_hashtag in possible_hastags:
        logger.info(u"Debug hashtag detected! %s" % content)
        return u"Debug hashtag detected! %s" % content

    # Check if twitter_username is a registered for a valid MAX username
    # if not, discard it
    maxuser = users.search({"twitterUsername": twitter_username})
    if maxuser:
        maxuser = maxuser[0]
    else:
        logger.info(u"(404) Discarding tweet %s from %s : There's no MAX user with that twitter username." % (str(tweetID), twitter_username))
        return u"(404) %s: No such MAX user." % twitter_username

    # Check if hashtag is registered for a valid MAX context
    # if not, discard it

    successful_tweets = 0
    maxcontext = contexts.search({"$or": query})
    if maxcontext:
        for context in maxcontext:
            # Check if MAX username has permission to post to the MAX context
            # if not, discard it
            try:
                can_write = canWriteInContexts(maxuser, [context, ])
            except:
                can_write = False
                logger.info(u"(401) %s can't write to %s" % (maxuser.username, context['url']))

            if can_write:
                # Construct the payload with the activity information
                newactivity = {
                    "object": {
                        "objectType": "note",
                        "content": content
                    },
                    "contexts": [{'url': context['url'],
                                  'objectType': 'context'
                                  }
                                 ],
                    "generator": twitter_generator_name
                }

                # Use the restricted REST endpoint for create a new activity in the specified
                # MAX context in name of the specified MAX username
                re = requests.post('%s/people/%s/activities' % (max_server_url, maxuser.username), json.dumps(newactivity), auth=('admin', 'admin'), verify=False)
                if re.status_code == 201:
                    logger.info(u"(201) Successfully posted tweet %s from @%s as %s on context %s" % (str(tweetID), twitter_username, maxuser['username'], context.url))
                    successful_tweets += 1
                    #return u"Success tweet from user %s in context %s" % (maxuser, context.url)
                else:
                    logger.info(u"(500) Error accessing the MAX API at %s" % max_server_url)  # pragma: no cover
                    #return u"Error accessing the MAX API at %s" % max_server_url
        error_message = len(maxcontext) != successful_tweets and " We weren't able to send the tweet to all contexts. See above for more information." or ""
        logger.info(u"Processed tweet %s to %d of %d possible contexts.%s" % (str(tweetID), successful_tweets, len(maxcontext), error_message))
        if error_message:
            return u"(401) Some posts not sent"
        else:
            return u"(200) All posts sent"
    else:
        logger.info(u"(404) Discarding tweet %s from %s: There are no MAX context with any of those hashtags" % (str(tweetID), twitter_username))
        return u"(404) %s: Not such MAX context %s" % (maxuser.username, maxcontext)

    return u"Should not see mee"  # pragma: no cover
