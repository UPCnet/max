from celery.task import task


@task
def processTweet(twitter_username, hashtag):
    print "Ejecutandooo user %s" % twitter_username
    return twitter_username
