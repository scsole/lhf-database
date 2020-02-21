"""Registrations module for the LHF database."""

import csv
import datetime
import sqlite3


def create_db():
    """Create registrations database."""
    with conn:
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


def get_new_registrations(input_file='./new_registrations.csv'):
    """Read registration input (csv) file, return list with new entries.

    We assume that the csv input file only contains valid input.
    TODO: Skip existing entries found in database
    """
    input_registrations = []
    with open(input_file) as regfile:
        reader = csv.reader(regfile)
        next(reader)    # skip headers
        for row in reader:
            input_registrations.append(row)
    return input_registrations


def add_new_registrations():
    """Add new registrations to the database.
    
    Registrations are considered new if they have a unique combination
    of First name, Last name, DoB and have a newer time stamp than the
    oldest registration.
    """
    reglist = get_new_registrations()
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
            reginfo = (reg[2].strip(),  # first_name
                    reg[3].strip(),     # last_name
                    reg[4].strip(),     # gender
                    reg[5].strip(),     # dob
                    reg[7].strip(),     # club
                    reg[1].strip(),     # email
                    reg[8].strip(),     # medical_conditions
                    reg[9].strip(),     # emergency_name
                    reg[10].strip(),    # emergency_contact
                    reg[0].strip(),     # registration_datetime
                    )
            c.execute(sql_insert_statement, reginfo)


def create_start_list(race_date=datetime.date.today()):
    """Generate start list for Webscorer."""
    print(race_date)


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
    add_new_registrations()
    create_start_list()
    create_registrations_list()

    conn.close()
