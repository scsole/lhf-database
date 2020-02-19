"""Registrations module for the LHF database."""

import sqlite3

#conn = sqlite3.connect('lhf.db')
conn = sqlite3.connect(':memory:')
c = conn.cursor()

def create_db():
    """Create registrations database."""
    # Dates are stores in TEXT as ISO8601 strings
    c.execute("""CREATE TABLE IF NOT EXISTS registrations (
                registration_id INTEGER,
                first_name TEXT,
                last_name TEXT,
                gender TEXT,
                dob TEXT,
                club TEXT,
                email TEXT,
                medical_conditions TEXT,
                emergency_name TEXT,
                emergency_contact TEXT,
                registration_date TEXT,
                PRIMARY KEY(registration_id ASC)
                )""")
    conn.commit()

def add_registrations():
    """Add new registrations to the database.
    
    Registrations are considered new if they have a unique combination
    of First name, Last name, DoB and have a newer time stamp than the
    oldest registration.
    """
    c.execute("INSERT INTO registrations VALUES (1, 'John', 'Doe', 'male', '1/2/1990', 'Leith', 'john.doe@gmail.com', '', 'Jane', '0221112222', '24/11/19')")
    conn.commit()

def create_start_list():
    """Generate start list for Webscorer."""
    pass

def create_registrations_list(sort="lname"):
    """Generate registration list for printing."""
    pass

if __name__ == "__main__":
    create_db()
    add_registrations()
    c.execute("SELECT * FROM registrations")
    for reg in c.fetchall():
        print(reg)
    conn.close()
    