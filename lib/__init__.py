"""
Initliazation file for library module.
"""

import datetime
import businesstimedelta
import csv

def business_hours(start_date, end_date=None):
    if not end_date:
        end_date = datetime.datetime.now()

    start_d = start_date.replace(tzinfo=None)
    end_d = end_date.replace(tzinfo=None)

    workday = businesstimedelta.WorkDayRule(
        start_time=datetime.time(8),
        end_time=datetime.time(18),
        working_days=[0, 1, 2, 3, 4])

    businesshrs = businesstimedelta.Rules([workday])
    bdiff = businesshrs.difference(start_d, end_d)

    return bdiff.hours


def sprint_str_to_dict(f):
    # Transform the following format into a dictionary: 'com.atlassian.greenhopper.service.sprint.Sprint@6316c6c0[id=1387,rapidViewId=454,state=CLOSED,name=Week 30-31,startDate=2018-07-23T12:42:06.058Z,endDate=2018-08-06T12:42:00.000Z,completeDate=2018-08-06T07:57:14.389Z,sequence=1387,goal=]'
    if f:
        try:
            if isinstance(f, list):
                f = f[0]
            fIdx = f.index('[')
            lIdx = f.index(']')
            if fIdx > 0 and lIdx > 0:
                f = f[fIdx+1:lIdx]
                pairs = f.split(',')
                return dict([p.split('=') for p in pairs])
        except Exception as e:
            print("Type error: " + str(e))

    return None

def output_to_csv(rows, output_path, header=None):

    with open(output_path, 'w') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
