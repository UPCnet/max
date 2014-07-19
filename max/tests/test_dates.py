# -*- coding: utf-8 -*-
import unittest
from max.rest.utils import date_filter_parser


class FunctionalTests(unittest.TestCase):

    def setUp(self):
        pass

    # BEGIN TESTS

    def test_exact_year(self):
        """
        """
        query = date_filter_parser('2014')

        self.assertIn('$gte', query)
        self.assertIn('$lte', query)
        self.assertEqual(len(query), 2)

        self.assertEqual(query['$gte'].year, 2014)
        self.assertEqual(query['$gte'].month, 1)
        self.assertEqual(query['$gte'].day, 1)
        self.assertEqual(query['$gte'].hour, 0)
        self.assertEqual(query['$gte'].minute, 0)
        self.assertEqual(query['$gte'].second, 0)

        self.assertEqual(query['$lte'].year, 2014)
        self.assertEqual(query['$lte'].month, 12)
        self.assertEqual(query['$lte'].day, 31)
        self.assertEqual(query['$lte'].hour, 23)
        self.assertEqual(query['$lte'].minute, 59)
        self.assertEqual(query['$lte'].second, 59)

    def test_exact_month_of_year(self):
        """
        """
        query = date_filter_parser('2014-02')

        self.assertIn('$gte', query)
        self.assertIn('$lte', query)
        self.assertEqual(len(query), 2)

        self.assertEqual(query['$gte'].year, 2014)
        self.assertEqual(query['$gte'].month, 2)
        self.assertEqual(query['$gte'].day, 1)
        self.assertEqual(query['$gte'].hour, 0)
        self.assertEqual(query['$gte'].minute, 0)
        self.assertEqual(query['$gte'].second, 0)

        self.assertEqual(query['$lte'].year, 2014)
        self.assertEqual(query['$lte'].month, 2)
        self.assertEqual(query['$lte'].day, 28)
        self.assertEqual(query['$lte'].hour, 23)
        self.assertEqual(query['$lte'].minute, 59)
        self.assertEqual(query['$lte'].second, 59)

    def test_exact_day_of_month_of_year(self):
        """
        """
        query = date_filter_parser('2014-02-27')

        self.assertIn('$gte', query)
        self.assertIn('$lte', query)
        self.assertEqual(len(query), 2)

        self.assertEqual(query['$gte'].year, 2014)
        self.assertEqual(query['$gte'].month, 2)
        self.assertEqual(query['$gte'].day, 27)
        self.assertEqual(query['$gte'].hour, 0)
        self.assertEqual(query['$gte'].minute, 0)
        self.assertEqual(query['$gte'].second, 0)

        self.assertEqual(query['$lte'].year, 2014)
        self.assertEqual(query['$lte'].month, 2)
        self.assertEqual(query['$lte'].day, 27)
        self.assertEqual(query['$lte'].hour, 23)
        self.assertEqual(query['$lte'].minute, 59)
        self.assertEqual(query['$lte'].second, 59)

    def test_after_year(self):
        """
        """
        query = date_filter_parser('+2014')

        self.assertIn('$gt', query)
        self.assertEqual(len(query), 1)

        self.assertEqual(query['$gt'].year, 2014)
        self.assertEqual(query['$gt'].month, 12)
        self.assertEqual(query['$gt'].day, 31)
        self.assertEqual(query['$gt'].hour, 23)
        self.assertEqual(query['$gt'].minute, 59)
        self.assertEqual(query['$gt'].second, 59)

    def test_after_month_of_year(self):
        """
        """
        query = date_filter_parser('+2014-06')

        self.assertIn('$gt', query)
        self.assertEqual(len(query), 1)

        self.assertEqual(query['$gt'].year, 2014)
        self.assertEqual(query['$gt'].month, 06)
        self.assertEqual(query['$gt'].day, 30)
        self.assertEqual(query['$gt'].hour, 23)
        self.assertEqual(query['$gt'].minute, 59)
        self.assertEqual(query['$gt'].second, 59)

    def test_after_day_of_month_of_year(self):
        """
        """
        query = date_filter_parser('+2014-06-15')

        self.assertIn('$gt', query)
        self.assertEqual(len(query), 1)

        self.assertEqual(query['$gt'].year, 2014)
        self.assertEqual(query['$gt'].month, 06)
        self.assertEqual(query['$gt'].day, 15)
        self.assertEqual(query['$gt'].hour, 23)
        self.assertEqual(query['$gt'].minute, 59)
        self.assertEqual(query['$gt'].second, 59)

    def test_before_year(self):
        """
        """
        query = date_filter_parser('-2014')

        self.assertIn('$lt', query)
        self.assertEqual(len(query), 1)

        self.assertEqual(query['$lt'].year, 2014)
        self.assertEqual(query['$lt'].month, 1)
        self.assertEqual(query['$lt'].day, 1)
        self.assertEqual(query['$lt'].hour, 0)
        self.assertEqual(query['$lt'].minute, 0)
        self.assertEqual(query['$lt'].second, 0)

    def test_before_month_of_year(self):
        """
        """
        query = date_filter_parser('-2014-06')

        self.assertIn('$lt', query)
        self.assertEqual(len(query), 1)

        self.assertEqual(query['$lt'].year, 2014)
        self.assertEqual(query['$lt'].month, 06)
        self.assertEqual(query['$lt'].day, 1)
        self.assertEqual(query['$lt'].hour, 0)
        self.assertEqual(query['$lt'].minute, 0)
        self.assertEqual(query['$lt'].second, 0)

    def test_before_day_of_month_of_year(self):
        """
        """
        query = date_filter_parser('-2014-06-15')

        self.assertIn('$lt', query)
        self.assertEqual(len(query), 1)

        self.assertEqual(query['$lt'].year, 2014)
        self.assertEqual(query['$lt'].month, 06)
        self.assertEqual(query['$lt'].day, 15)
        self.assertEqual(query['$lt'].hour, 00)
        self.assertEqual(query['$lt'].minute, 0)
        self.assertEqual(query['$lt'].second, 0)
