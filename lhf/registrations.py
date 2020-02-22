"""Registrations module for the LHF database."""

import csv
from datetime import datetime, date
import re
import sqlite3


def create_db():
    """Create registrations database."""
    with conn:
        # We cannot reuse registration_ids so we must use AUTOINCREMENT.
        c.execute("""CREATE TABLE IF NOT EXISTS registrations (
                    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    dob date NOT NULL,
                    club TEXT,
                    email TEXT NOT NULL,
                    medical_conditions TEXT,
                    emergency_name TEXT,
                    emergency_contact TEXT,
                    registration_timestamp timestamp NOT NULL
                    )""")


def get_new_registrations(reg_input='./new_registrations.csv', dup_output='./duplicate_registrations.csv', inv_output='./invalid_registrations.csv'):
    """Read new registration csv file and return a list with new entries.

    Duplicate enties are loged to dup_output if any
    exist. Registrations are considered duplicate if they do not have a
    unique combination of First name, Last name, and DoB. Any
    duplicates in reg_input will NOT be detected.
    """
    
    newregs = []    # new registrations w/o headers
    dupregs = []    # duplicate registrations w/ headers
    invregs = []    # invalid registrations w/ headers
    
    # Keys for newregs. These must match the order of the headers in reg_input.
    input_csv_headers = ('registration_timestamp', 'email', 'first_name', 'last_name', 'gender', 'dob', 'age', 'club', 'medical_conditions', 'emergency_name', 'emergency_contact', 'accepted_terms')

    sql_search_statement = """SELECT registration_id
                            FROM registrations
                            WHERE first_name LIKE ? AND last_name LIKE ? AND dob = ?"""
    
    # Date formats expected from csv file.
    datetimefmt = "%d/%m/%Y %H:%M:%S"
    datefmt = "%d/%m/%Y"

    with open(reg_input) as regfile:
        reader = csv.DictReader(regfile, input_csv_headers)
        dupregs.append(['Existing Registration ID'] + list(next(reader).values())) # skip actual csv headers
        invregs.append(['Invalid Reason'] + dupregs[0][1:-1])

        for row in reader:
            # Check for duplicates
            try:
                c.execute(sql_search_statement, (re.sub(r"[ ']", '_', row['first_name'].strip()), re.sub(r"[ ']", '_',row['last_name'].strip()), parse_date(row['dob'])))
            except ValueError:
                invregs.append(["DoB does not match {}".format(datefmt)] + list(row.values()))
                continue
            
            search = c.fetchone()
            if search is None:
                newregs.append(row)

                # Convert required strings into dates
                try:
                    row['registration_timestamp'] = datetime.strptime(row['registration_timestamp'], datetimefmt)
                except ValueError:
                    del(newregs[-1])
                    invregs.append(["Timestamp does not match {}".format(datetimefmt)] + list(row.values()))
                    continue
                
                row['dob'] = parse_date(row['dob'])
            else:
                dupregs.append([search[0]] + list(row.values()))    

    # Log duplicate registrations
    if len(dupregs) > 1:
        print("Skipped {} duplicate registrations. View them in {}".format(len(dupregs) - 1, dup_output))
        with open(dup_output, 'w') as dupfile:
            writer = csv.writer(dupfile)
            writer.writerows(dupregs)

    # Log invalid registrations
    if len(invregs) > 1:
        print("Skipped {} invalid registrations. View them in {}".format(len(invregs) - 1, inv_output))
        with open(inv_output, 'w') as invfile:
            writer = csv.writer(invfile)
            writer.writerows(invregs)
    
    return newregs


def parse_date(date_str):
    """Attempt to format date_str as a date.
    
    It is assumed date_str will be in the form %d<sep>%m<sep>%Y. If a date
    object cannot be created from the string a ValueError is raised.
    """
    date_str = re.sub(r"[ .-]", '/', date_str.strip())
    date_time = datetime.strptime(date_str, "%d/%m/%Y")
    return date_time.date()


def add_registrations(reglist):
    """Add registrations to the database."""
    with conn:
        sql_insert_statement = """INSERT INTO registrations(
                                first_name,
                                last_name,
                                gender,
                                dob,
                                club,
                                email,
                                medical_conditions,
                                emergency_name,
                                emergency_contact,
                                registration_timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        for reg in reglist:
            reginfo = (
                    reg['first_name'].strip(),
                    reg['last_name'].strip(),
                    reg['gender'].strip(),
                    reg['dob'],
                    reg['club'].strip(),
                    reg['email'].strip(),
                    reg['medical_conditions'].strip(),
                    reg['emergency_name'].strip(),
                    reg['emergency_contact'].strip(),
                    reg['registration_timestamp']
                    )
            c.execute(sql_insert_statement, reginfo)


def create_start_list(race_date=date.today()):
    """Generate start list for Webscorer."""
    webscorer_headers = ('Bib', 'First name', 'Last name', 'Team name', 'Age', 'Gender', 'Distance')
    c.execute("""SELECT registration_id, first_name, last_name, club, dob, gender
                FROM registrations""")
    startlist = c.fetchall()
    startlistfile = './Startlist{}.csv'.format(race_date.strftime('%Y%m%d'))

    # We don't know what distance each runner will undertake ahead of the
    # event. We just need to include each distance at least once.
    for i,entry in enumerate(startlist):
        startlist[i] = list(entry)
        startlist[i].append('5km')

        # Replace DoB with age at time of race
        startlist[i][4] = years_between(startlist[i][4], race_date)
    startlist[0][-1] = '10km'

    with open(startlistfile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(webscorer_headers)
        writer.writerows(startlist)


def years_between(date1, date2):
    """Return the number of full years between dates."""
    if date1 > date2:
        temp = date2
        date2 = date1
        date1 = temp
    date1_this_year = date(date2.year, date1.month, date1.day)
    return date2.year - date1.year - (date1_this_year >= date2)


def create_registrations_list(outfile='reg_print.csv'):
    """Create a csv file containing registration ids sorted by last name."""
    c.execute("""SELECT last_name, first_name, registration_id
                FROM registrations
                ORDER BY LOWER(last_name), LOWER(first_name) ASC""")
    reglist = c.fetchall()
    regheaders = ('Last Name', 'First Name', 'Bib Number')

    with open(outfile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(regheaders)
        writer.writerows(reglist)


if __name__ == "__main__":
    #conn = sqlite3.connect('lhf.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    c = conn.cursor()

    create_db()
    add_registrations(get_new_registrations())
    add_registrations(get_new_registrations('./fixed.csv'))
    create_start_list()
    #create_registrations_list()

    conn.close()
