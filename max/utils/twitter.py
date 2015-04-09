# -*- coding: utf-8 -*-
import logging
import requests
import tweepy


def get_twitter_api(registry):
    twitter_settings = registry.cloudapis_settings.get('twitter', None)

    if twitter_settings:
        try:
            # Twitter auth
            auth = tweepy.OAuthHandler(twitter_settings.get('consumer_key', ''), twitter_settings.get('consumer_secret', ''))
            auth.set_access_token(twitter_settings.get('access_token', ''), twitter_settings.get('access_token_secret', ''))
            api = tweepy.API(auth)
            api.verify_credentials()
            return api
        except:
            # Some error occurred
            return None


def download_twitter_user_image(api, twitterUsername, filename):
    """
    """
    exit_status = False
    if api:
        user = api.get_user(twitterUsername)
        image_url = getattr(user, 'profile_image_url_https', None)

        if image_url:
            req = requests.get(image_url, verify=False)
            if req.status_code == 200:
                open(filename, 'w').write(req.content)
                exit_status = True

    if not exit_status:
        logger = logging.getLogger('max')
        logger.error("An error occurred while downloading twitter user image!")
    return exit_status


def get_userid_from_twitter(api, twitterUsername):
    if api:
        user = api.get_user(twitterUsername)
        return user.id_str

