# -*- coding: utf-8 -*-
import unittest
import re


class RegexTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_is_valid_hashtag_regex(self):
        """
        Tests valid and invalid hashtags against RE_VALID_HASHTAG.
        See max.regex for more info on what the regex is supposed to match
        """
        from max.regex import RE_VALID_HASHTAG

        #valid
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, '#foo'))      # hashtag with # ; lowercase hashtag
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, '#FO_1-2'))   # Hashtag with all accepted chars
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'foo'))       # hashtag without #
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, ' FOO '))     # hashtag with leading/trailing whitespace
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, '#veryveryveryveryveryveryveryveryveryverylonghashtag'))  # A long hashtag

        #invalid
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '##foo'))        # hashtags with more than one starting #
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '#'))            # hashtag with invalid length
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '#foé!?'))       # hashtag with invalid chars
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '#foo#'))        # hashtag with # in it
        self.assertIsNone(re.match(RE_VALID_HASHTAG, 'foo#'))         # hashtag with trailing #
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '#foo #bar'))    # more than one hashtag
        self.assertIsNone(re.match(RE_VALID_HASHTAG, 'foo bar'))      # more than one hashtag without #

    def test_captures_hashtag_correctly(self):
        """
        Tests hashtag capture output against RE_VALID_HASHTAG and some valid hashtag inputs
        See max.regex for more info on what the regex is supposed to capture
        """
        from max.regex import RE_VALID_HASHTAG
        self.assertEqual(re.sub(RE_VALID_HASHTAG, r'\1', '#foo'), 'foo')
        self.assertEqual(re.sub(RE_VALID_HASHTAG, r'\1', 'foo'), 'foo')
        self.assertEqual(re.sub(RE_VALID_HASHTAG, r'\1', '   #foo   '), 'foo')
        self.assertEqual(re.sub(RE_VALID_HASHTAG, r'\1', '   foo   '), 'foo')

    def test_is_valid_twitter_user_regex(self):
        """
        Tests valid and invalid twitter usernames against RE_VALID_TWITTER_USERNAME.
        See max.regex for more info on what the regex is supposed to match
        """
        from max.regex import RE_VALID_TWITTER_USERNAME

        #valid
        self.assertIsNotNone(re.match(RE_VALID_TWITTER_USERNAME, '@johndoe'))          # username with @; lowercase username
        self.assertIsNotNone(re.match(RE_VALID_TWITTER_USERNAME, '@JohnDoe_12'))       # username with all accepted chars
        self.assertIsNotNone(re.match(RE_VALID_TWITTER_USERNAME, 'johndoe'))           # username without @
        self.assertIsNotNone(re.match(RE_VALID_TWITTER_USERNAME, ' johndoe '))         # username with leading/trailing whitespace
        self.assertIsNotNone(re.match(RE_VALID_TWITTER_USERNAME, '@j'))                # username with only one char
        self.assertIsNotNone(re.match(RE_VALID_TWITTER_USERNAME, '@johndoe89_12345'))  # username with maximum length

        #invalid
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, 'twitter.com/@leo_struni'))  # No comments... real PICNIC case
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, '@@johndow'))          # username with more than one starting #
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, '@johndoe89_123456'))  # username with invalid length
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, '@'))                  # username with invalid length
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, '@johndoe!?'))         # username with invalid chars
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, '@johndoe@'))          # username with @ in it
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, 'foo@'))               # username with trailing @
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, '@foo @bar'))          # more than one username
        self.assertIsNone(re.match(RE_VALID_TWITTER_USERNAME, 'foo bar'))            # more than one username without @

    def test_captures_twitter_username_correctly(self):
        """
        Tests twitter username capture output against RE_VALID_TWITTER_USERNAME and some valid username inputs
        See max.regex for more info on what the regex is supposed to capture
        """
        from max.regex import RE_VALID_TWITTER_USERNAME
        self.assertEqual(re.sub(RE_VALID_TWITTER_USERNAME, r'\1', '@johndoe'), 'johndoe')
        self.assertEqual(re.sub(RE_VALID_TWITTER_USERNAME, r'\1', 'johndoe'), 'johndoe')
        self.assertEqual(re.sub(RE_VALID_TWITTER_USERNAME, r'\1', '   @johndoe   '), 'johndoe')
        self.assertEqual(re.sub(RE_VALID_TWITTER_USERNAME, r'\1', '   johndoe   '), 'johndoe')
