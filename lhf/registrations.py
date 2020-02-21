"""Registrations module for the LHF database."""

import csv
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

def get_new_registrations(input_file='./input.csv'):
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
            reginfo = (reg[2],  # first_name
                    reg[3],     # last_name
                    reg[4],     # gender
                    reg[5],     # dob
                    reg[7],     # club
                    reg[1],     # email
                    reg[8],     # medical_conditions
                    reg[9],     # emergency_name
                    reg[10],    # emergency_contact
                    reg[0],     # registration_datetime
                    )
            c.execute(sql_insert_statement, reginfo)

def create_start_list():
    """Generate start list for Webscorer."""
    c.execute("SELECT registration_id, first_name, last_name FROM registrations")
    for reg in c.fetchall():
        print(reg)

def create_registrations_list(sort="lname"):
    """Generate registration list for printing."""
    pass

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

    #print(last_entry_datetime()[0])

    conn.close()
