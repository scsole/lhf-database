"""Registrations module for the LHF database."""

import csv
import datetime
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
                    dob TEXT NOT NULL,
                    club TEXT,
                    email TEXT NOT NULL,
                    medical_conditions TEXT,
                    emergency_name TEXT,
                    emergency_contact TEXT,
                    registration_datetime TEXT NOT NULL
                    )""")


def get_new_registrations(reg_input='./new_registrations.csv', dup_output='./duplicate_registrations.csv'):
    """Read new registration csv file and return a list with new entries.

    We assume that the csv input file already has its contents checked
    for validity. Duplicate enties are loged to dup_output if any
    exist. Registrations are considered duplicate if they do not have a
    unique combination of First name, Last name, and DoB.
    """
    newregs = []    # contains all new registrations
    dupregs = []    # contains all duplicate registrations w/ headers
    sql_search_statement = """SELECT *
                            FROM registrations
                            WHERE first_name = ? COLLATE NOCASE AND last_name = ? COLLATE NOCASE AND dob = ?"""

    with open(reg_input) as regfile:
        reader = csv.reader(regfile)
        dupregs.append(['Existing Registration ID'] + next(reader)) # file headers
        for row in reader:
            c.execute(sql_search_statement, (row[2].strip(), row[3].strip(), row[5]))
            search = c.fetchone()
            if search is None:
                newregs.append(row)
            else:
                dupregs.append([search[0]] + row)

    # Log skiped duplicate registrations
    if len(dupregs) > 1:
        print("Found {} duplicate registrations. They can be found in {}".format(len(dupregs) - 1, dup_output))
        with open(dup_output, 'w') as dupfile:
            writer = csv.writer(dupfile)
            writer.writerows(dupregs)

    return newregs


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
                                registration_datetime) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        for reg in reglist:
            # Only store necessary info in the database
            reginfo = (
                    reg[2].strip(),     # first_name
                    reg[3].strip(),     # last_name
                    reg[4].strip(),     # gender
                    reg[5],             # dob
                    reg[7].strip(),     # club
                    reg[1].strip(),     # email
                    reg[8].strip(),     # medical_conditions
                    reg[9].strip(),     # emergency_name
                    reg[10].strip(),    # emergency_contact
                    reg[0]              # registration_datetime
                    )
            c.execute(sql_insert_statement, reginfo)


def create_start_list(race_date=datetime.date.today()):
    """Generate start list for Webscorer."""
    return race_date


def create_registrations_list(outfile='reg_print.csv'):
    """Generate registration list in csv file for printing."""
    c.execute("""SELECT last_name, first_name, registration_id
                FROM registrations
                ORDER BY LOWER(last_name), LOWER(first_name) ASC""")
    reglist = c.fetchall()
    regheaders = ('Last Name', 'First Name', 'Bib Number')

    with open(outfile, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(regheaders)
        writer.writerows(reglist)


def last_entry_datetime():
    """Return the time stamp of the newest registration"""
    c.execute("SELECT MAX(datetime(registration_datetime)) FROM registrations")
    return c.fetchone()


if __name__ == "__main__":
    #conn = sqlite3.connect('lhf.db')
    conn = sqlite3.connect(':memory:')  # test the database in memory
    c = conn.cursor()

    create_db()
    add_registrations(get_new_registrations())
    create_start_list()
    create_registrations_list()

    conn.close()
