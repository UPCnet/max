import unittest
import re


class RegexTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_is_valid_hashtag_regex(self):
        """
        Tests valid and invalid hashtags against RE_VALID_HASHTAG.
        See max.regex for more info
        """
        from max.regex import RE_VALID_HASHTAG

        #valid
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, '#foo'))
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, '#FOO'))
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'foo'))
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'FOO'))
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'FOO '))
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, ' FOO '))
        self.assertIsNotNone(re.match(RE_VALID_HASHTAG, ' FOO'))


        #invalid
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '##foo'))
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '#'))
        self.assertIsNone(re.match(RE_VALID_HASHTAG, '#foo#'))
        self.assertIsNone(re.match(RE_VALID_HASHTAG, 'foo#'))
        self.assertIsNone(re.match(RE_VALID_HASHTAG, ''))

    # def test_is_valid_twitter_user_regex(self):
    #     """
    #     """
    #     from max.regex import RE_VALID_TWITTER_USERNAME

    #     #valid
    #     self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'johndoe'))
    #     self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'JohnJoe'))
    #     self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'John_doe'))
    #     self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'johndoe32))
    #     self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'johndoe_23'))
    #     self.assertIsNotNone(re.match(RE_VALID_HASHTAG, 'johndoe_23'))


    #     #invalid
    #     self.assertIsNone(re.match(RE_VALID_HASHTAG, '##foo'))
    #     self.assertIsNone(re.match(RE_VALID_HASHTAG, '#'))
    #     self.assertIsNone(re.match(RE_VALID_HASHTAG, '#foo#'))
    #     self.assertIsNone(re.match(RE_VALID_HASHTAG, 'foo#'))
    #     self.assertIsNone(re.match(RE_VALID_HASHTAG, ''))
