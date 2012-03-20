import unittest
from pyramid import testing


class RulesTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_process_new_tweet(self):
        from maxrules.tasks import processTweet
        processTweet.delay('sneridagh', '#Atenea')
