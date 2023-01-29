# LHF Database

Database management for the Leith Harbour Free 5km or 10km race.

The database currently stores runner information. The purpose of this project is to *quickly* perform the following
operations:

- Insert new registrations from an existing Google Form
- Update existing registrations which were resubmitted via the Google Form
- Generate startlists compatible with Webscorer
- Generate registration lists for our website

Other management tasks, such as deleting registrations, should be performed with programs such as [DB Browser for
SQLite](https://sqlitebrowser.org/). The database **must** be stored securely.

> **Breaking changes**: v2 added the field `last_updated` and renamed the field `registration_timestamp` to `created`.
> Existing databases schemas must be manually updated. See the updating procedure section for details.

## Usage

Requires Python version >= 3.5

```bash
python registrations.py [-h] [-a] [-s] [-n N] [-d D] [-l] [newregs]
```

```
positional arguments:
  newregs     path to registrations csv file when -a is specified, default='new_registrations.csv'

options:
  -h, --help  show this help message and exit
  -a          add new registrations to the database
  -s          create a startlist for Webscorer
  -n N        optional name for the startlist file; Webscorer uses this for the race name by default
  -d D        optional date for the next race as YYYY-MM-DD, default=today
  -l          create registration list for the website
```

If a database does not exist or cannot be located, the program can create a new one.

## Examples

### Add new runners

Download new registrations as csv file from Google forms. Then run:

```bash
python registrations.py -a /path/to/csvfile
```

If any duplicate or invalid entries were identified, a message will be displayed. If required, skipped entries can be
corrected (e.g. in Excel) then saved as a new csv file. The previous command can then be run again with the new file to
inset these entries.

### Create a startlist

To create a startlist ready to be uploaded to Webscorer append `-s` to the command. This assumes the race will be held
today and will calculate runner's ages accordingly. To specify a race date, append `-d <date_of_race>` to the command.
For example, if the race is to be held on 2049-12-31, run:

```bash
python registrations.py -sd 2049-12-31
```

Since Webscorer uses the startlist file name as the default race name, the startlist name can be modified by appending
`-n <name_of_file>` to the command. The `.csv` extension is optional. For example, if the race is being held on Course
1, and is held on 2049-12-31, run:

```bash
python registrations.py -sd 2049-12-31 -n "Leith Harbour Free - Course 1"
```

## Updating to new versions

### v1 to v2

```sql
ALTER TABLE registrations
RENAME COLUMN registration_timestamp TO created;

ALTER TABLE registrations
ADD last_updated timestamp;

UPDATE registrations SET last_updated = created;
```
