from celery.task import task


@task
def processTweet(twitter_username, hashtag, content):
    """ Process inbound tweet
    """
    # Check if twitter_username is a registered for a valid MAX username
    # if not, discard it

    # Check if hashtag is registered for a valid MAX context
    # if not, discard it

    # Check if MAX username has permission to post to the MAX context
    # if not, discard it

    # Use the restricted REST endpoint for create a new activity in the specified
    # MAX context in name of the specified MAX username

    print "Ejecutandooo user %s" % twitter_username
    return twitter_username
