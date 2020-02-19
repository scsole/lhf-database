"""Registrations module for the LHF database."""

import csv
import sqlite3

#conn = sqlite3.connect('lhf.db')
conn = sqlite3.connect(':memory:')
c = conn.cursor()

def create_db():
    """Create registrations database."""
    with conn:
        c.execute("""CREATE TABLE IF NOT EXISTS registrations (
                    registration_id INTEGER,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    dob TEXT NOT NULL,
                    club TEXT,
                    email TEXT NOT NULL,
                    medical_conditions TEXT,
                    emergency_name TEXT,
                    emergency_contact TEXT,
                    registration_datetime TEXT NOT NULL,
                    PRIMARY KEY(registration_id ASC)
                    )""")

def add_registrations():
    """Add new registrations to the database.
    
    Registrations are considered new if they have a unique combination
    of First name, Last name, DoB and have a newer time stamp than the
    oldest registration.
    """
    sql_insert_statement = "INSERT INTO registrations VALUES (?, ?, ?, ?, date(?), ?, ?, ?, ?, ?, datetime(?))"
    with conn:
        c.execute(sql_insert_statement, (1, 'John', 'Doe', 'male', '1990-02-01', 'Leith', 'john.doe@gmail.com', '', 'Jane', '0221112222', '1999-11-20 12:01:01'))
        c.execute(sql_insert_statement, (2, 'Jane', 'Doe', 'male', '1991-02-01', 'Leith', 'jane.doe@gmail.com', '', 'John', '0221111111', '2019-11-20 12:00:00'))
        c.execute(sql_insert_statement, (3, 'Mike', 'Doe', 'female', '1990-02-02', 'Leith', 'mike.doe@gmail.com', '', 'Jane', '0221112222', '2019-11-20 12:00:01'))


def create_start_list():
    """Generate start list for Webscorer."""
    c.execute("SELECT registration_id, first_name, last_name FROM registrations")
    for reg in c.fetchall():
        print(reg)

def create_registrations_list(sort="lname"):
    """Generate registration list for printing."""
    pass

def last_entry_datetime():
    """Return the time stamp of the last database registration"""
    c.execute("SELECT MAX(datetime(registration_datetime)) FROM registrations")
    print(c.fetchall())

if __name__ == "__main__":
    create_db()
    add_registrations()
    create_start_list()

    c.execute("SELECT * FROM registrations")
    for reg in c.fetchall():
        print(reg)

    last_entry_datetime()

    conn.close()
