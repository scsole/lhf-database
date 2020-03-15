# LHF Database

Database backend for the Leith Harbour Free. This database is used to store runner information, and generate start lists for Webscorer.

## Usage

Requires Python version >= 3.5

```bash
python registrations.py [-h] [-a] [-s] [-d D] [-l] [newregs]
```

```bash
positional arguments:
  newregs     path to registrations csv file when -a is specified, default='new_registrations.csv'

optional arguments:
  -h, --help  show this help message and exit
  -a          add new registrations to the database
  -s          create a startlist for Webscorer
  -d D        date of the next race as YYYY-MM-DD, default=today
  -l          create registration list for the website
```

## Examples

### Add new runners

Download new registrations as csv file from Google forms. Then run:

```bash
python registrations.py -a /path/to/csvfile
```

If any duplicate or invalid entries were identified, a nessage will be displayed. If required, skiped entries can be corrected (e.g. in Excel) then saved as a new csv file. The previous command can then be run again with the new file to inset these entries.

### Create a startlist

To create a startlist ready to be uploaded to Webscorer append `-s` to the command. This assumes the race will be held today and will calculate runner's ages accordingly. To specify a race date, append `-d <date_of_race>` to the command. For example if the race is to be held on 2049-12-31, run:

```bash
python registrations.py -sd 2049-12-31
```
