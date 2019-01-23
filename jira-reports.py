#!/usr/bin/env python3

# Please see: https://developer.atlassian.com/cloud/jira/platform/rest/v3/#api-api-3-issue-issueIdOrKey-get

from jira import JIRA
import dateutil.parser
import datetime
import time
import csv

from etc import config
import lib

def fetch_jira_tasks():
    jira = JIRA(options=config.OPTIONS, basic_auth=config.AUTH)

    # Story points are a computed field and may differ between projects.
    jira_fields = jira.fields()
    field_map = {field['name']:field['id'] for field in jira_fields}

    # Print all fields for this Jira project.
    # print (field_map)

    # issues = jira.search_issues(jql_str='issue = CTCRM-52', maxResults=1,expand=["changelog", "transitions", "versionedRepresentations"])
    issues = jira.search_issues(jql_str='project in (PTECH, CTMD, CTFIND, CTCRM, CTED) ORDER BY Rank ASC', maxResults=10000,expand=["changelog", "transitions", "versionedRepresentations"])
    # issues = jira.search_issues(jql_str='project = PTECH AND issue = PTECH-103', maxResults=1,expand=["changelog","transitions"])
    # issues = jira.search_issues(jql_str='project = PTECH', maxResults=2,expand=["changelog","transitions"])

    # Buils a dictionary of statuses. We need to do this by cycling through all 
    # issues to ensure that we have a template to use during processing.
    statuses = {}
    for issue in issues:
        changelog = issue.changelog
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    statuses[item.fromString] = 0
        statuses[issue.fields.status.name] = 0

    rows = []

    for issue in issues:
        story_points = getattr(issue.fields, field_map['Story Points'])
        row = dict(
            id=issue.id,
            key=issue.key,
            description=issue.fields.description.replace('\r', '').replace(',', '').replace('\n', ''),
            issue_type=issue.fields.issuetype.name,

            url="{0}/browse/{1}".format(config.OPTIONS['server'], issue.key),

            created_on=dateutil.parser.parse(issue.fields.created).strftime("%Y-%m-%d %H:%M:%S"),
            created_week_of_year=dateutil.parser.parse(issue.fields.created).strftime("%W"),
            created_by=issue.fields.creator.name,

            current_status=issue.fields.status.name,
            status_changed_on=dateutil.parser.parse(issue.fields.created).strftime("%Y-%m-%d %H:%M:%S"),
            status_changed_week_of_year=int(dateutil.parser.parse(issue.fields.created).strftime("%W")),
            status_changed_cnt = 0,

            assigned_to=issue.fields.assignee.name if issue.fields.assignee else '',
            story_points=story_points if story_points else 0,
            developer = ''
        )

        # Add statuses to the current dictionary.
        row.update(statuses)
        
        start_date = None

        # Determine days spend in specific status.
        changelog = issue.changelog
        if changelog.histories:
            for history in changelog.histories:
                for item in history.items:
                    # print (item.field)
                    if item.field == 'status':
                        row['status_changed_cnt'] += 1
                        # Calculate days.
                        if not start_date:
                            start_date = dateutil.parser.parse(issue.fields.created)
                        
                        end_date = dateutil.parser.parse(history.created)
                        days = lib.date_diff_weekdays_only(start_date, end_date)
                        start_date = end_date
                        row[item.fromString] = row[item.fromString] + days

                        row['status_changed_on']=dateutil.parser.parse(history.created).strftime("%Y-%m-%d %H:%M:%S")
                        row['status_changed_week_of_year']=int(dateutil.parser.parse(history.created).strftime("%W"))

                    # Check if it is a developer.
                    if item.field == 'assignee':
                        if item.fromString in config.DEVELOPERS:
                            row['developer'] = item.fromString


        else:
            # No history yet, so take the date created.
            days = lib.date_diff_weekdays_only(dateutil.parser.parse(issue.fields.created))
            row[issue.fields.status.name] = days

        rows.append(row)

        # from pprint import pprint
        # pprint (rows, indent=4)

    return rows

def output_to_csv(rows, output_path, header=None):

    with open(output_path, 'w') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

def main():
    
    rows = fetch_jira_tasks()
    
    if rows:
        headers = rows[0].keys()
        output_to_csv(rows, config.REPORT_CSV_PATH, headers)

if __name__ == '__main__':
    main()
