# LHF Database

Database backend for the Leith Harbour Free. This database is used to store runner information, generate start lists for Webscorer, store race results from Webscorer, and generate reports.

## Usage

```bash
python3 registrations.py [-h] [-a] [-s] [-d D] [-p]
```

```bash
optional arguments:
  -h, --help  show this help message and exit
  -a          add new registrations to the database
  -s          create a startlist for Webscorer
  -d D        date of the next race as YYYY-MM-DD, default=today
  -p          create a printable registrations list
  ```

## Examples

### Add new runners

Download new registrations as csv file from Google forms. Rename it as `new_registrations.csv` and place it in the in the same directory as this script. Then run:

```bash
python3 registrations.py -a
```

If any duplicate or invalid entries were identified, a nessage will be printed. The skiped entries can then be inspected. If required, the entries should be corrected (e.g. in Excel) then saved as csv file titled `new_registrations.csv`. The command can then be run again to inset the corrected entries.

### Create a startlist

To create a startlist ready to be uploaded to Webscorer simply append `-s` to the command. This assumes the race will be held today and calculates the runners ages accordingly. To specify a race on a differend date provide `-d <date_of_race>` to the command. For example if the race is to be held on 2049-12-31, run:

```bash
python3 registrations.py -sd 2049-12-31
```
