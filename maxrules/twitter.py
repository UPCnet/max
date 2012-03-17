#!/usr/bin/env python

import sys
import optparse
#from getpass import getpass
from textwrap import TextWrapper

import tweepy


def main(argv=sys.argv, quiet=False):
    command = MaxRulesRunner(argv, quiet)
    return command.run()


class StreamWatcherListener(tweepy.StreamListener):

    status_wrapper = TextWrapper(width=60, initial_indent='    ', subsequent_indent='    ')

    def on_status(self, status):
        try:
            print self.status_wrapper.fill(status.text)
            print '\n %s  %s  via %s\n' % (status.author.screen_name, status.created_at, status.source)
            # Filter by valid twitter usernames found in MAX users
            # Insert the new data in MAX
        except:
            # Catch any unicode errors while printing to console
            # and just ignore them to avoid breaking application.
            pass

    def on_error(self, status_code):
        print 'An error has occured! Status code = %s' % status_code
        return True  # keep stream alive

    def on_timeout(self):
        print 'Snoozing Zzzzzz'


class MaxRulesRunner(object):
    verbosity = 1  # required
    description = "Max rules runner."
    usage = "usage: %prog [options]"
    parser = optparse.OptionParser(usage, description=description)
    parser.add_option('-u', '--twitter-username',
                      dest='username',
                      type='string',
                      action='append',
                      help=("Twitter username"))
    parser.add_option('-p', '--twitter-password',
                      dest='password',
                      type='string',
                      action='append',
                      help=('Twitter password'))

    def __init__(self, argv, quiet=False):
        self.quiet = quiet
        self.options, self.args = self.parser.parse_args(argv[1:])

    def run(self):
        if not self.options.username or not self.options.password:
            self.out('You must provide a valid username and password.')
            return 2
        # Prompt for login credentials and setup stream object
        #username = raw_input('Twitter username: ')
        #password = getpass('Twitter password: ')
        auth = tweepy.auth.BasicAuthHandler(self.options.username[0], self.options.password[0])
        stream = tweepy.Stream(auth, StreamWatcherListener(), timeout=None)

        follow_list = ""
        track_list = "#ateneaupc, "

        #follow_list = raw_input('Users to follow (comma separated): ').strip()
        #track_list = raw_input('Keywords to track (comma seperated):').strip()
        if follow_list:
            follow_list = [u for u in follow_list.split(',')]
        else:
            follow_list = None
        if track_list:
            track_list = [k for k in track_list.split(',')]
        else:
            track_list = None

        stream.filter(follow=follow_list, track=track_list)

    def out(self, msg):  # pragma: no cover
        if not self.quiet:
            print(msg)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print '\nGoodbye!'
