# -*- coding: utf-8 -*-
from max.tests.base import MaxTestBase
from max.tests.base import MockTweepyAPI
from max.tests.base import http_mock_twitter_user_image

from paste.deploy import loadapp

import ConfigParser
import httpretty
import os
import re
import shutil
import sys
import tempfile
import unittest


class TwitterApiTestCase(unittest.TestCase, MaxTestBase):
    """
        Tests to check communication with twitter api
        and max twitter utils
    """

    def setUp(self):
        """
            Tries to inject a real cloudapis settings into tests database.
            Raises and stops tests if invalid or not found configuration.
        """
        self.conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=self.conf_dir)
        buildout_folder = re.search(r'(.*?/)bin.*', sys.argv[0]).groups()[0]
        cloudapis_file = '{}/config/cloudapis.ini'.format(buildout_folder)

        self.tempfolder = tempfile.mkdtemp()

        try:
            cloudapis_config = ConfigParser.ConfigParser()
            cloudapis_config.read(cloudapis_file)
            twitter_config = dict(cloudapis_config.items('twitter'))
        except ConfigParser.NoSectionError:  # pragma: no cover
            raise Exception("\n\nMissing or invalid twitter section at {}".format(cloudapis_file))

        valid_configuration = twitter_config.get('consumer_key') and \
            twitter_config.get('consumer_secret') and\
            twitter_config.get('access_token') and\
            twitter_config.get('access_token_secret')

        if not valid_configuration:  # pragma: no cover
            raise Exception("\n\nMissing or invalid twitter section value at {}".format(cloudapis_file))

        real_cloudapis = {'twitter': twitter_config}

        self.app.registry.max_store.cloudapis.insert(real_cloudapis)
        self.app.registry.cloudapis_settings = real_cloudapis

    def tearDown(self):
        self.app.registry.max_store.drop_collection('cloudapis')
        shutil.rmtree(self.tempfolder)

    @unittest.skipUnless(os.environ.get('twitter', False), 'Twitter tests must be explicitly enabled to avoid being banned')
    def test_get_twitter_api(self):
        """
            Given a valid cloudapis settings
            When i try to get the api
            Then get the tweepy wrapper object
            And the expected methods are there
        """
        from max.utils.twitter import get_twitter_api
        api = get_twitter_api(self.app.registry)
        self.assertTrue(hasattr(api, 'verify_credentials'))
        self.assertTrue(hasattr(api, 'get_user'))

    @unittest.skipUnless(os.environ.get('twitter', False), 'Twitter tests must be explicitly enabled to avoid being banned')
    def test_get_twitter_user(self):
        """
            Given a valid cloudapis settings
            When i try to get a twitter user
            Then get a user object
            And the expected properties are there
        """
        from max.utils.twitter import get_twitter_api
        from max.utils.twitter import get_userid_from_twitter

        api = get_twitter_api(self.app.registry)
        userid = get_userid_from_twitter(api, 'maxupcnet')

        self.assertEqual(userid, '526326641')

    @unittest.skipUnless(os.environ.get('twitter', False), 'Twitter tests must be explicitly enabled to avoid being banned')
    def test_get_twitter_avatar(self):
        """
            Given a valid cloudapis settings
            When i try to get a twitter user
            Then get a user object
            And the expected properties are there
        """
        from max.utils.twitter import get_twitter_api
        from max.utils.twitter import download_twitter_user_image

        api = get_twitter_api(self.app.registry)
        imagefile = os.path.join(self.tempfolder, 'twitter.png')
        download_twitter_user_image(api, 'maxupcnet', imagefile)
        self.assertFileExists(imagefile)


class TwitterApiFailingScenariosTestCase(unittest.TestCase, MaxTestBase):

    def setUp(self):
        """
            Tests to check failing scenarios when communicating
            with twitter api
        """
        self.conf_dir = os.path.dirname(__file__)
        self.app = loadapp('config:tests.ini', relative_to=self.conf_dir)
        self.app.registry.max_store.drop_collection('cloudapis')
        self.tempfolder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempfolder)

    def test_get_twitter_api_no_settings(self):
        """
            Given an empty cloudapis settings
            When i try to get the twitter api object
            I get nothing in response
        """
        from max.utils.twitter import get_twitter_api
        self.app.registry.cloudapis_settings['twitter'] = {}
        api = get_twitter_api(self.app.registry)
        self.assertEqual(api, None)

    def test_get_twitter_api_no_image_url(self):
        """
            Given a tweepy api without user image property
            When i try to get the user image
            I get no download
        """
        from max.utils.twitter import download_twitter_user_image
        api = MockTweepyAPI(None, provide_image=False)
        imagefile = os.path.join(self.tempfolder, 'twitter.png')
        download_twitter_user_image(api, 'maxupcnet', imagefile)
        self.assertFileNotExists(imagefile)

    @httpretty.activate
    def test_get_twitter_api_failing_download(self):
        """
            Given a tweepy api with user image property
            And a url that fails for some unknown reason
            When i try to get the user image
            I get no download
        """
        from max.utils.twitter import download_twitter_user_image
        avatar_image = os.path.join(self.conf_dir, "avatar.png")
        http_mock_twitter_user_image(avatar_image, status=500)

        api = MockTweepyAPI(None, provide_image=True)
        imagefile = os.path.join(self.tempfolder, 'twitter.png')
        download_twitter_user_image(api, 'maxupcnet', imagefile)
        self.assertFileNotExists(imagefile)
