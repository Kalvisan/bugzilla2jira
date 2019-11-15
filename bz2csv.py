import sys
import os
import argparse
import configparser
from datetime import datetime
import bugsy
import csv


def map_status(status, mapping_file=None, default="Closed"):
    default_status_mapping = {
        'NEW': 'Open',
        'CONFIRMED': 'Open',
        'IN_PROGRESS': 'In_progress',
        'RESOLVED': 'Closed'
    }
    if mapping_file is not None and os.path.exists(mapping_file):
        with open(mapping_file, 'r') as file:
            for line in file:
                new_status, old_status = line.split('=')
                if old_status == status:
                    return new_status
        return map_status(status, default=default, mapping_file=None)
    else:
        if status not in default_status_mapping:
            return default
    return default_status_mapping[status]


def map_users(username, mapping_file=None, default="admin"):
    found_user = None
    if mapping_file is None:
        return str(username).split('@')[0]
    elif mapping_file is not None:
        if not os.path.exists(mapping_file):
            print("User mapping file not found!")
            return None

        with open(mapping_file, 'r') as file:
            for line in file:
                user, email = line.split('=')
                if email == username:
                    found_user = user
                    break
        if found_user is None:
            # if not found in file use default mapping
            found_user = map_users(username, mapping_file=None)
    else:
        return default
    return found_user


def main(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config-file', required=True)
    parser.add_argument('-u', '--users-file', help="You can specify users mapping, by default it will split email and use first part of it\"user123@x.org = user123\"")
    parser.add_argument('-s', '--status-file', help="You can specify status mapping. \"new_status=old_status\"")
    args = parser.parse_args(arguments)

    settings = configparser.ConfigParser()
    settings.read(args.config_file)
    has_user_mapping = (args.users_file if args.users_file else None)
    has_status_mapping = (args.status_file if args.status_file else None)

    if has_user_mapping:
        print("Will be using user mapping file %s" % args.users_file)
    if has_status_mapping:
        print("Will be using status mapping file %s" % args.status_file)

    # Connect to Bugzilla 
    bz_url = settings.get('bugzilla', 'url')
    bz_user = settings.get('bugzilla', 'user')
    bz_pass = settings.get('bugzilla', 'pass')

    # Jira settings
    jira_key = settings.get('jira', 'key')
    jira_default_type = settings.get('jira', 'def_type')
    jira_default_status = settings.get('jira', 'def_status')
    jira_default_user = settings.get('jira', 'def_user')

    # CSV settings
    csv_filename = settings.get('csv', 'filename')
    csv_time_format = settings.get('csv', 'format')
    csv_max_comment = settings.get('csv', 'max_comment')
    csv_max_attachment = settings.get('csv', 'max_attachment')
    csv_advanced_attachment = settings.get('csv', 'advanced_attachment')

    # Check if csv export file does not exists
    if os.path.isfile(csv_filename):
        os.remove(csv_filename)

    bzapi = bugsy.Bugsy(username=str(bz_user), password=str(bz_pass), bugzilla_url=str(bz_url + "/rest"))

    titles = ["Issue Id", "Category", "Summary", "Description", "Date Created", "Date Modified", "Priority", "Issue type", "Status", "Resolution", "Reporter", "Assignee", "OS", "Label"]
    max_attachments = max_comments = 0
    # Obtain Bugzilla bug from gotten products
    extra_search = ["creation_time", "last_change_time", "creator", "assigned_to", "priority"]
    bugs = bzapi.search_for.include_fields(extra_search).search()
    print("Got total of %s issues" % len(bugs))

    print("Pre-fill titles of Comments and Attachments to csv")
    print("Adding %s comments and %s attachments" % (csv_max_comment, csv_max_attachment))
    titles = append_array(titles, "Comments", int(csv_max_comment))
    titles = append_array(titles, "Attachment", int(csv_max_attachment))
    with open(csv_filename, 'a', encoding='utf-8') as csvFile:
        writer = csv.writer(csvFile, delimiter=",", quotechar='\"', quoting=csv.QUOTE_ALL)
        writer.writerow(titles)

    for bug in bugs:
        # bug is object of Bugs more info: https://bugsy.readthedocs.io/en/latest/bug.html#bugsy.Bug.id
        _raw = bug.to_dict()
        row = [
            "%s-%s" % (str(jira_key).upper(), bug.id),
            bug.product,
            bug.summary,
            bug.summary,
            str(datetime.strptime(_raw.get('creation_time')[:-1], '%Y-%m-%dT%H:%M:%S').strftime(csv_time_format)),
            str(datetime.strptime(_raw.get('last_change_time')[:-1], '%Y-%m-%dT%H:%M:%S').strftime(csv_time_format)),
            _raw.get('priority'),
            jira_default_type,
            map_status(bug.status, mapping_file=has_status_mapping, default=str(jira_default_status)),
            bug.resolution,
            map_users(_raw.get('creator'), mapping_file=has_user_mapping, default=jira_default_user),
            map_users(_raw.get('assigned_to'), mapping_file=has_user_mapping, default=jira_default_user),
            bug.OS,
            bug.component
        ]

        comments = bug.get_comments()
        if len(comments) > max_comments:
            max_comments = len(comments)

        # there is specific way jira handle comments
        for comment in comments:
            time = str(comment.creation_time.strftime(csv_time_format))
            row.append("%s;%s; %s" % (time, map_users(comment.creator, mapping_file=has_user_mapping, default=jira_default_user), comment.text))

        # Jira require you to fill other comment columns empty
        row = append_array(row, "", int(csv_max_comment) - len(comments))

        # Bugsy just added attachment support, but there wasn't enough documentation, so I use raw data
        attachments = bug.get_attachments()
        if len(attachments) > max_attachments:
            max_attachments = len(attachments)

        # there is specific way jira handle attachments
        for attach in attachments:
            attach = attach.to_dict()
            url = "%s/attachment.cgi?id=%s" % (bz_url, attach.get('id'))
            if bool(csv_advanced_attachment):
                time = str(attach.get('creation_time').strftime(csv_time_format))
                row.append("%s;%s;%s;%s" % (time, map_users(attach.get('creator'), mapping_file=has_user_mapping, default=jira_default_user), attach.get('file_name'), url))
            else:
                row.append(url)

        # jira require to pre-fill empty columns
        row = append_array(row, "", int(csv_max_attachment) - len(attachments))

        print("Writing bug #%s to csv" % bug.id)
        with open(csv_filename, 'a', encoding='utf-8') as csvFile:
            writer = csv.writer(csvFile, delimiter=",", quotechar='\"', quoting=csv.QUOTE_ALL)
            writer.writerow(row)

    print("Got max comments: %s" % max_comments)
    print("Got max attachments: %s" % max_attachments)


def append_array(arr, text, count):
    for x in range(count):
        arr.append(text)
    return arr


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
