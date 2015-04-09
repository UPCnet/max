# -*- coding: utf-8 -*-
from calendar import monthrange
from datetime import datetime
from datetime import time

import re


def rfc3339_parse(date):
    """
    Converts a date in format 2012-10-27T18:14:14.000Z to a python datetime
    """
    timeparts = list(re.search(r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+).?(\d*)Z', date).groups())
    timeparts[6] = timeparts[6] and (int(timeparts[6]) * 1000) or 0
    return datetime(*[int(part) for part in timeparts])


def date_filter_parser(date_filter):
    """
        Parses a date filter query in the following format:

        (+-)yyyy-(mm-dd)


        where month and day are optional, and a prefix may be specified to modifiy the query.
        Separators between year month and day can be anything except a number.

        If no +- modifier is specified, parser assumes it has to perform a exact query. If the
        + modifier is prepended, parser will generate query for dates earliear than specified,
        otherwise, if - is prepended, it will look for dates older than specified

        Examples:

            2014          Dates elapsed during year 2014
            2014-03       Dates elapsed during march of 2014
            +2014         Dates elapsed after the end of 2014
                          (anything Starting the first second of 2015, included)
            -2014-01-30   Dates elapsed before the begginning of the 30th of January 2014
                          (anything until 2014-01-29 at 23:59:59)

        At the end outputs a mongodb date query suitable to be set on any field
    """
    before = date_filter.startswith('-')
    after = date_filter.startswith('+')
    exact = not before and not after

    date_filter = date_filter.lstrip('-').lstrip('+')
    result = re.search(r'(\d{4})[^\d]*(\d{2})*[^\d]*(\d{2})*', date_filter)

    date1 = [0, 0, 0]
    date2 = [0, 0, 0]

    query = {}

    if result:
        year, month, day = result.groups()
        date1[0] = int(year)
        date2[0] = int(year)

        if month is not None:
            date1[1] = int(month)
            date2[1] = int(month)
        else:
            date1[1] = 1 if exact or before else 12
            if exact:
                date2[1] = 12

        if day is not None:
            date1[2] = int(day)
            date2[2] = int(day)
        else:
            last_day_of_month = monthrange(date1[0], date1[1])[1]
            date1[2] = 1 if exact or before else last_day_of_month
            if exact:
                date2[2] = last_day_of_month

        base_dt1 = datetime(*date1)
        if before:
            query = {
                '$lt': datetime.combine(base_dt1, time.min)
            }
        elif after:
            query = {
                '$gt': datetime.combine(base_dt1, time.max)
            }
        elif exact:
            base_dt2 = datetime(*date2)
            query = {
                '$gte': datetime.combine(base_dt1, time.min),
                '$lte': datetime.combine(base_dt2, time.max)
            }

    return query
