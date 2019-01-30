#!/usr/bin/env python3

# Please see: https://developer.atlassian.com/cloud/jira/platform/rest/v3/#api-api-3-issue-issueIdOrKey-get

from jira import JIRA
import dateutil.parser
import datetime
import time

from etc import config
import lib

def fetch_jira_tasks(maxResults, startAt):
    jira = JIRA(options=config.OPTIONS, basic_auth=config.AUTH)

    # Story points are a computed field and may differ between projects.
    jira_fields = jira.fields()
    field_map = {field['name']:field['id'] for field in jira_fields}

    # Print all fields for this Jira project.
    # print (field_map)

    # issues = jira.search_issues(jql_str='project in (PTECH, CTMD, CTFIND, CTCRM, CTED) ORDER BY Rank ASC', maxResults=maxResults, startAt=startAt, expand=["changelog", "transitions", "versionedRepresentations"])
    issues = jira.search_issues(jql_str='issue = CTED-170', maxResults=1,expand=["changelog", "transitions", "versionedRepresentations"])
    # issues = jira.search_issues(jql_str='project = PTECH AND issue = PTECH-103', maxResults=1,expand=["changelog","transitions"])
    # issues = jira.search_issues(jql_str='project = PTECH', maxResults=2,expand=["changelog","transitions"])

    # Buils a dictionary of statuses. We need to do this by cycling through all 
    # issues to ensure that we have a template to use during processing.
    statuses = {}
    statuses_week_of_year = {}
    for issue in issues:
        changelog = issue.changelog
        for history in changelog.histories:
            for item in history.items:
                if item.field == 'status':
                    statuses[item.fromString] = 0
                    statuses_week_of_year["{0}_WOY".format(item.fromString)] = 0
        statuses[issue.fields.status.name] = 0
        statuses_week_of_year["{0}_WOY".format(issue.fields.status.name)] = 0

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
            bsa = '',
            developer = '',
            developer_assigned_date = '',
            sprint_state = '',
            sprint_name = '',
            sprint_start_date = '',
            sprint_end_date = ''
        )

        sprint = lib.sprint_str_to_dict(getattr(issue.fields, field_map['Sprint']))
        if sprint:
            row['sprint_name'] = sprint['name']
            row['sprint_start_date'] = sprint['startDate']
            row['sprint_end_date'] = sprint['endDate']
            row['sprint_state'] = sprint['state']

        # Add statuses to the current dictionary.
        row.update(statuses)
        row.update(statuses_week_of_year)

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

                        row[item.fromString] = row[item.fromString] + lib.business_hours(start_date, end_date)
                        row["{0}_WOY".format(item.fromString)] = int(dateutil.parser.parse(history.created).strftime("%W"))

                        start_date = end_date

                        row['status_changed_on'] = dateutil.parser.parse(history.created).strftime("%Y-%m-%d %H:%M:%S")
                        row['status_changed_week_of_year'] = int(dateutil.parser.parse(history.created).strftime("%W"))

                    # Check if it is a developer.
                    if item.field == 'assignee':
                        if item.toString in config.DEVELOPERS:
                            row['developer'] = item.toString
                            row['developer_assigned_date'] = dateutil.parser.parse(history.created).strftime("%Y-%m-%d %H:%M:%S")
                        if item.toString in config.BSAS:
                            row['bsa'] = item.toString

        # Calculate hours for status that has not changed yet.
        if row[issue.fields.status.name] == 0:
            row[issue.fields.status.name] = lib.business_hours(dateutil.parser.parse(issue.fields.created))
            row["{0}_WOY".format(issue.fields.status.name)] = int(dateutil.parser.parse(issue.fields.created).strftime("%W"))

        # If there is no history for assignee change, we need to get it from the default.
        if issue.fields.assignee:
            if row['developer'] == '' and issue.fields.assignee.displayName in config.DEVELOPERS:
                row['developer'] = issue.fields.assignee.displayName
                row['developer_assigned_date'] = dateutil.parser.parse(issue.fields.created).strftime("%Y-%m-%d %H:%M:%S")

            if row['bsa'] == '' and issue.fields.assignee.displayName in config.BSAS:
                row['bsa'] = issue.fields.assignee.displayName

        rows.append(row)

        # from pprint import pprint
        # pprint (rows, indent=4)

    return rows

def main():

    maxResults = 900
    startAt = 0

    rows = fetch_jira_tasks(maxResults, startAt)
    headers = rows[0].keys()
    lib.output_to_csv(rows, config.REPORT_CSV_PATH, headers)

if __name__ == '__main__':
    main()
