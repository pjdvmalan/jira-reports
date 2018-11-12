"""
Initliazation file for library module.
"""

# import datetime
from datetime import datetime, timezone
import pytz

def date_diff_weekdays_only(start_date, end_date=None):
    """
    Calculate the number of work days between two dates.

    Taken from: https://stackoverflow.com/questions/46386764/python-exclude-weekends-between-two-dates

    @param start_date: The start date.
    @param end_date: The end date.
    @return: Number of week days.
    """
    if not end_date:
        end_date = datetime.now(pytz.timezone('US/Eastern'))

    delta = (end_date - start_date).days

    return (delta - (delta // 7) * 2)
