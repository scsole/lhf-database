# LHF Database

Database backend for the Leith Harbour Free. This database is used to store runner information, generate start lists for Webscorer, store race results from Webscorer, and generate reports.

## Usage

To add new runers and generate start lists, place registration info at `./new_registrations.csv`. Then run:

```bash
python3 ./lft/registrations.py
```
