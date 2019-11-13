# BugZilla to JIRA exporter
This simple script exports all bugzilla issues to one csv file. Jira got specific way to import csv files, so here is a script who can help you!

## How to start
1. First of all make sure you got [python 3](https://www.python.org/downloads/) installed.
2. Download this repository to your local machine: `git clone https://github.com/Kalvisan/bugzilla2jira.git bz2jira` next go to folder `cd bz2jira`
3. Install all needed python library `pip3 install -r requirements.txt`
    1. Attention: I created this script while Bugsy wasn't released 0.11.1+ version to public in pip, so I installed newest version by `pip3 install git+https://github.com/AutomatedTester/Bugsy.git` 
4. Now you can start editing config file as you need. `open local config example file` more info how to edit file below
5. You are ready now to start exporting data from bugzilla to local csv file
6. Basic export example: `python3 bz2csv.py -c config` a bit more advanced commands you can see below.
7. Now you got your csv export. You can navigate to jira "External System Import" category and start importing CSV file. You can use example configuration file `jira_configuration_example.txt` for help in mapping fields.

## How to use config file
First of all, fill your administrator user and password rows. Next change bugzilla url. 
And next and most `important` row is "max_comment" and "max_attachment", because the way how jira handle csv file is bit odd.
More info about how jira handle csv files [here](https://confluence.atlassian.com/adminjiracloud/importing-data-from-csv-776636762.html).
This script require to know, what is the largest count of comments and attachments in ONE issue. If you don't know, just set big numbers like `max_comment: 100` and `max_attachment: 50`, this will take more time to create csv file and more time to import data to Jira.

If you want to be specific with your config, then my script will count what is the biggest count of attachments and comments in one issue, but script will show you that number only, at the end of process. So you can leave those number as it is and start example run (From "How to start" #6), and in the end you will see numbers.


Inside example config file, there is `format:` this is for handling time format for Jira. You need to look up in what way your jira use time format.
You need to convert time to [python datetime format](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes), but don't forget to add extra `%` before every % symbol, like in the example (python config will not handle single % symbol).

There is two ways how jira handle attachments inside csv file:
1. If you leave `advanced_attachment: False` then script will fill attachment with only a link
2. If you set `advanced_attachment: True` then script will add extra parameters to your attachment like "Create time;Author;Filename;URL"

#### Other rows
`key:` - your Jira project KEY
`def_type:` - what will be your jira issue type
`def_user` - what will be default user if none found  

## How to use extra arguments
There is couple of extra options you can use:
1. You can map your bugzilla users. Just give script another argument like `-u user-mapping.cfg` or `--user-file user-mapping.cfg`:

By default your bugzilla username will be handled as email first part.i.e. by default: `bugzilla_user@example.com` script will use only the part before `@` = bugzille_user.

But you can create user mapping file. Script will be reading every single line and split it using `=` symbol.
You can map users like this:

`jira_user=bugzilla_user@example.com` or
`jira_user@example.com=bugzilla_user@example.com` or
`jira_user=bugzilla_user`

2. You can map your status in bugzilla with argument `-s status-mapping.cfg` or `--status-file status-mapping.cfg`. File parsing will be the same as user file parsing.
