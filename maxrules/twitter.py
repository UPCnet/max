#!/usr/bin/env python
import os
import sys
import argparse
#from getpass import getpass
from textwrap import TextWrapper
import pymongo
import tweepy

import logging

# CONFIG
max_server_url = 'https://max.upc.edu'
# max_server_url = 'https://sneridagh.upc.es'

twitter_generator_name = 'Twitter'
debug_hashtag = 'debugmaxupcnet'
logging_file = '/var/pyramid/maxserver/var/log/twitter-listener.log'
if not os.path.exists(logging_file):  # pragma: no cover
    logging_file = '/tmp/twitter-listener.log'
logger = logging.getLogger("tweeterlistener")
fh = logging.FileHandler(logging_file, encoding="utf-8")
formatter = logging.Formatter('%(asctime)s %(message)s')
logger.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    # command = MaxTwitterRulesRunnerTest(argv, quiet)
    command = MaxTwitterRulesRunner(argv, quiet)
    return command.run()


class StreamWatcherListener(tweepy.StreamListener):  # pragma: no cover

    status_wrapper = TextWrapper(width=60, initial_indent='    ', subsequent_indent='    ')

    def on_status(self, status):
        try:
            logger.info('Got tweet %d from %s via %s with content: %s' % (status.id, status.author.screen_name, status.source, status.text))
            # Insert the new data in MAX
            from maxrules.tasks import processTweet
            processTweet.delay(status.author.screen_name.lower(), status.text, status.id)
        except:
            # Catch any unicode errors while printing to console
            # and just ignore them to avoid breaking application.
            pass

    def on_error(self, status_code):
        logging.error('An error has occured! Status code = %s' % status_code)
        return True  # keep stream alive

    def on_timeout(self):
        logging.warning('Snoozing Zzzzzz')


class MaxTwitterRulesRunner(object):  # pragma: no cover
    verbosity = 1  # required
    description = "Max rules runner."
    usage = "usage: %prog [options]"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--twitter-username',
                      dest='username',
                      type=str,
                      help=("Twitter username"))
    parser.add_argument('-p', '--twitter-password',
                      dest='password',
                      type=str,
                      help=('Twitter password'))
    parser.add_argument('-d', '--mongodb-url',
                      dest='mongodb_url',
                      type=str,
                      help=('MongoDB url'))
    parser.add_argument('-n', '--mongodb-name',
                      dest='mongodb_db_name',
                      type=str,
                      help=('MongoDB database name'))
    parser.add_argument('-c', '--mongodb-cluster',
                      dest='mongodb_cluster',
                      action="store_true",
                      default=False,
                      help=('Enable MongoDB cluster'))
    parser.add_argument('-H', '--mongodb-hosts',
                      dest='mongodb_hosts',
                      type=str,
                      help=('MongoDB Cluster hosts'))
    parser.add_argument('-r', '--mongodb-replica_set',
                      dest='mongodb_replica_set',
                      type=str,
                      help=('MongoDB Cluster replica set'))

    def __init__(self, argv, quiet=False):
        self.quiet = quiet
        self.options = self.parser.parse_args()

    def run(self):
        if not self.options.username or not self.options.password:
            logging.error('You must provide a valid username and password.')
            return 2

        #username = raw_input('Twitter username: ')
        #password = getpass('Twitter password: ')
        #follow_list = raw_input('Users to follow (comma separated): ').strip()
        #track_list = raw_input('Keywords to track (comma seperated):').strip()

        # Querying the BBDD for users to follow - Cluster aware
        if not self.options.mongodb_cluster:
            db_uri = self.options.mongodb_url
            conn = pymongo.MongoClient(db_uri)
        else:
            hosts = self.options.mongodb_hosts
            replica_set = self.options.mongodb_replica_set
            conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

        db = conn[self.options.mongodb_db_name]
        contexts_with_twitter_username = db.contexts.find({"twitterUsernameId": {"$exists": True}})
        follow_list = [users_to_follow.get('twitterUsernameId') for users_to_follow in contexts_with_twitter_username]
        contexts_with_twitter_username.rewind()
        readable_follow_list = [users_to_follow.get('twitterUsername') for users_to_follow in contexts_with_twitter_username]

        # Prompt for login credentials and setup stream object
        auth = tweepy.auth.BasicAuthHandler(self.options.username, self.options.password)
        stream = tweepy.Stream(auth, StreamWatcherListener(), timeout=None)

        # Hardcoded global hashtag(s)
        track_list = ['#upc', '#%s' % debug_hashtag]

        logging.warning("Listening to this Twitter hashtags: %s" % str(track_list))
        logging.warning("Listening to this Twitter userIds: %s" % str(readable_follow_list))

        stream.filter(follow=follow_list, track=track_list)


# For testing purposes only
class MaxTwitterRulesRunnerTest(object):  # pragma: no cover
    verbosity = 1  # required
    description = "Max rules runner."
    usage = "usage: %prog [options]"
    parser = argparse.ArgumentParser(usage, description=description)
    parser.add_argument('-u', '--twitter-username',
                      dest='username',
                      type=str,
                      help=("Twitter username"))
    parser.add_argument('-p', '--twitter-password',
                      dest='password',
                      type=str,
                      help=('Twitter password'))
    parser.add_argument('-d', '--mongodb-url',
                      dest='mongodb_url',
                      type=str,
                      help=('Twitter password'))
    parser.add_argument('-n', '--mongodb-name',
                      dest='mongodb_db_name',
                      type=str,
                      help=('Twitter password'))

    def __init__(self, argv, quiet=False):
        self.quiet = quiet
        self.options = self.parser.parse_args()

        logging.warning("Running first time!")

    def run(self):
        while True:
            import time
            time.sleep(2)
            from maxrules.tasks import processTweet
            processTweet('sneridagh', u'Twitejant com un usuari de twitter assignat a un contexte')
            time.sleep(2)
            processTweet('maxupcnet', u'Twitejant amb el hashtag #upc #gsxf')

if __name__ == '__main__':  # pragma: no cover
    try:
        main()
    except KeyboardInterrupt:
        logging.warning('\nGoodbye!')
