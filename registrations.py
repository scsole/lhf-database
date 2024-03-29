"""Registrations module for the LHF database."""

import argparse
import csv
import re
import sqlite3
from datetime import datetime, date
from pathlib import Path

def adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()

def adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.isoformat()

sqlite3.register_adapter(date, adapt_date_iso)
sqlite3.register_adapter(datetime, adapt_datetime_iso)

def convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return date.fromisoformat(val.decode())

def convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return datetime.fromisoformat(val.decode())

sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("datetime", convert_datetime)

def open_db(db_path=Path("lhf.db")):
    """Connect to the database and return a connection.
    
    If the database does not exist, confirm if one should be created.
    """
    if not db_path.is_file():
        print("Could not find a database at {}".format(db_path))
        print("(c)reate a database and continue\n(a)bort all operations")
        choice = input("Option: ")
        if choice.lower().strip() == 'c':
            print("Creating new database at {}".format(db_path))
        else:
            print("Aborting, no changes have been made")
            exit()
    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    create_registrations_table(conn)
    return conn


def create_registrations_table(conn):
    """Create registrations table."""
    with conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS registrations (
                    registration_id INTEGER NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    dob date NOT NULL,
                    club TEXT,
                    email TEXT NOT NULL,
                    medical_conditions TEXT,
                    emergency_name TEXT NOT NULL,
                    emergency_contact TEXT NOT NULL,
                    created timestamp NOT NULL,
                    last_updated timestamp NOT NULL,
                    PRIMARY KEY(last_name, first_name, dob)
                    )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS race_genders (
                    registration_id INTEGER NOT NULL UNIQUE,
                    gender TEXT NOT NULL,
                    FOREIGN KEY(registration_id) REFERENCES registrations(registration_id)
                    )""")


def get_new_registrations(conn, reg_input):
    """Read new registrations csv file and return lists for new and updated entries.

    Registrations are considered updated if they do not have a unique
    combination of First name, Last name, and DoB. Any duplicates in reg_input
    will NOT be detected.
    """
    conflict_dir = Path("import_conflicts")
    inv_output = conflict_dir / "invalid_registrations.csv"

    newregs = []    # new registrations w/o headers
    updregs = []    # updated registrations w/o headers
    invregs = []    # invalid registrations w/ headers
    emptyregs = 0
    
    # Keys for newregs. These must match the order of the headers in reg_input.
    input_csv_headers = ('created', 'email', 'first_name', 'last_name', 'gender', 'dob', 'age', 'club', 'medical_conditions', 'emergency_name', 'emergency_contact', 'accepted_terms')

    c = conn.cursor()
    sql_search_statement = """SELECT registration_id
                            FROM registrations
                            WHERE first_name LIKE ? AND last_name LIKE ? AND dob = ?"""
    
    # Datetime formats expected from csv file.
    datetimefmt = "%d/%m/%Y %H:%M:%S"
    datefmt = "%d/%m/%Y"
    try:
        with open(reg_input) as regfile:
            reader = csv.DictReader(regfile, input_csv_headers)
            invregs.append(['Invalid Reason'] + list(next(reader).values())) # skip csv headers

            for row in reader:
                # Skip empty rows
                if (row['created'] == ''
                        or row['email'] == ''
                        or row['first_name'] == ''
                        or row['first_name'] == ''
                        or row['gender'] == ''
                        or row['dob'] == ''):
                    emptyregs += 1
                    continue

                # Check for duplicates
                try:
                    c.execute(sql_search_statement, (re.sub(r"[ ']", '_', row['first_name'].strip()), re.sub(r"[ ']", '_',row['last_name'].strip()), parse_date(row['dob'])))
                except ValueError:
                    invregs.append(["DoB does not match {}".format(datefmt)] + list(row.values()))
                    continue
                
                # Convert required strings into dates
                try:
                    row['created'] = datetime.strptime(row['created'], datetimefmt)
                except ValueError:
                    invregs.append(["Timestamp does not match {}".format(datetimefmt)] + list(row.values()))
                    continue

                row['dob'] = parse_date(row['dob'])
                row['last_updated'] = row['created']

                # Add valid registration to the appropriate list
                search = c.fetchone()
                if search == None:
                    newregs.append(row)
                else:
                    updregs.append(row)

    except FileNotFoundError:
        print("ERROR: Could not find {}".format(reg_input))
        print("       Please check that this file exists before trying again.")
        exit()

    # Be verbose
    if emptyregs > 0:
        print("Skipped {} empty rows.".format(emptyregs))
    
    if len(invregs) > 1:
        print("Skipped {} invalid registrations. View them in {}".format(len(invregs) - 1, inv_output))
        conflict_dir.mkdir(exist_ok=True)
        with open(inv_output, 'w', newline='') as invfile:
            writer = csv.writer(invfile)
            writer.writerows(invregs)
    
    return newregs, updregs


def parse_date(date_str):
    """Attempt to format date_str as a date.
    
    It is assumed date_str will be in the form %d<sep>%m<sep>%Y. If a date
    object cannot be created from the string a ValueError is raised.
    """
    date_str = re.sub(r"[ .-]", '/', date_str.strip())
    date_time = datetime.strptime(date_str, "%d/%m/%Y")
    return date_time.date()


def add_registrations(conn, reglist):
    """Add registrations to the database.
    
    Returns a list of duplicate registrations, if any, that were not inserted."""
    duplicate_registrations = []    # registrations which could not be inserted due to primary key constraints
    
    c = conn.cursor()
    new_regs_num = 0
    with conn:
        sql_insert_statement = """INSERT INTO registrations(
                                    registration_id,
                                    first_name,
                                    last_name,
                                    gender,
                                    dob,
                                    club,
                                    email,
                                    medical_conditions,
                                    emergency_name,
                                    emergency_contact,
                                    created,
                                    last_updated
                                ) VALUES (
                                    (SELECT IFNULL(MAX(registration_id), 0) + 1 FROM registrations),
                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                                )"""
        for reg in reglist:
            try:
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
                        reg['created'],
                        reg['last_updated']
                        )
                c.execute(sql_insert_statement, reginfo)
                new_regs_num += 1
                
            except sqlite3.IntegrityError as e:
                # Likely a duplicate entry in the input file
                duplicate_registrations.append(reg)

            except sqlite3.Error as e:
                print(e)
                print("ERROR: Unable to insert row for: {}, {} ({})".format(
                    reg['last_name'].strip(), reg['first_name'].strip(), reg['dob']))
    
    print("Added {} registration(s)".format(new_regs_num))
    return duplicate_registrations


def update_registrations(conn, reglist):
    """Update existing registrations in the database."""
    c = conn.cursor()
    update_regs_num = 0
    with conn:
        sql_update_statement = """UPDATE registrations
                                SET
                                    gender = ?,
                                    club = ?,
                                    email = ?,
                                    medical_conditions = ?,
                                    emergency_name = ?,
                                    emergency_contact = ?,
                                    last_updated = ?
                                WHERE
                                    first_name = ? AND last_name = ? AND dob = ?"""
        for reg in reglist:
            try:
                reginfo = (
                        reg['gender'].strip(),
                        reg['club'].strip(),
                        reg['email'].strip(),
                        reg['medical_conditions'].strip(),
                        reg['emergency_name'].strip(),
                        reg['emergency_contact'].strip(),
                        reg['created'],
                        reg['first_name'].strip(),
                        reg['last_name'].strip(),
                        reg['dob']
                        )
                c.execute(sql_update_statement, reginfo)
                update_regs_num += 1
            except sqlite3.Error as e:
                print(e)
                print("ERROR: Unable to update row: {}, {} ({})".format(
                    reg['last_name'].strip(), reg['first_name'].strip(), reg['dob']))
    
    print("Updated {} registration(s)".format(update_regs_num))


def create_start_list(conn, race_date, file_name=""):
    """Generate a start list for Webscorer."""
    start_lists_dir = Path("startlists")
    start_lists_dir.mkdir(exist_ok=True)
    webscorer_headers = ('Bib', 'First name', 'Last name', 'Team name', 'Age', 'Gender', 'Distance')
    startlist = conn.execute("""SELECT registration_id, first_name, last_name, club, dob, registrations.gender, race_genders.gender
                                FROM registrations
                                LEFT JOIN race_genders USING(registration_id)
                                """).fetchall()
    
    if not file_name.strip():
        file_name = "startlist{}.csv".format(race_date.strftime('%Y%m%d'))
    elif not file_name.strip().endswith(".csv"):
        file_name = "{}.csv".format(file_name)
    outfile = start_lists_dir / file_name

    if len(startlist) > 0:
        for i,entry in enumerate(startlist):
            startlist[i] = list(entry)

            # Alter non-binary genders
            gender = startlist[i].pop()
            if gender != None:
                if startlist[i][5].lower() == "non-binary":
                    startlist[i][5] = gender
                else:
                    print("WARN: Conflicting genders for registration_id={}".format(startlist[i][0]))
                    print("\t Please check that entries in race_genders only match registrations with 'Non-binary' genders.")
            elif startlist[i][5].lower() == "non-binary":
                print("WARN: No race gender specified for registration_id={}".format(startlist[i][0]))
                print("\t Please add an entry to race_genders and recreate this startlist")
            
            # Replace DoB with age at time of race
            startlist[i][4] = years_between(startlist[i][4], race_date)
            
            # Race distance
            startlist[i].append('5km')
        
        # We don't know what distance each runner will undertake ahead of the
        # event. We just need to include each distance at least once.
        startlist[0][-1] = '10km'
    else:
        print("WARN: the database was empty when creating a start list")

    with open(outfile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(webscorer_headers)
        writer.writerows(startlist)
        print("New startlist located at: {}".format(outfile))


def create_registrations_list(conn):
    """Create a csv file with names and registration ids sorted by last name."""
    reg_lists_dir = Path("registration_lists")
    reg_lists_dir.mkdir(exist_ok=True)
    outfile = reg_lists_dir / "registrations_list_{}.csv".format(datetime.today().strftime("%Y%b%d-%H%M"))

    reglist = conn.execute("""SELECT last_name, first_name, registration_id
                                FROM registrations
                                ORDER BY LOWER(last_name), LOWER(first_name) ASC""").fetchall()
    regheaders = ('Last Name', 'First Name', 'Bib Number')

    if len(reglist)  == 0:
        print("WARN: the database was empty when creating a registrations list")

    with open(outfile, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(regheaders)
        writer.writerows(reglist)
        print("New registrations list located at: {}".format(outfile))


def years_between(date1, date2):
    """Return the number of years between two dates."""
    if date1 > date2:
        temp = date2
        date2 = date1
        date1 = temp
    try:
        date1_this_year = date(date2.year, date1.month, date1.day)
    except ValueError:
        # Encountered a leap year
        date1_this_year = date(date2.year, 3, 1)
    return date2.year - date1.year - (date1_this_year > date2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add registrations and produce start lists.")
    parser.add_argument("newregs", nargs='?', help="path to registrations csv file when -a is specified, default='new_registrations.csv'",
                        default=Path("new_registrations.csv"))
    parser.add_argument("-a", help="add new registrations to the database",
                        action="store_true")
    parser.add_argument("-s", help="create a startlist for Webscorer",
                        action="store_true")
    parser.add_argument("-n", help="optional name for the startlist file; Webscorer uses this for the race name by default",
                        default="")
    parser.add_argument("-d", help="optional date for the next race as YYYY-MM-DD, default=today",
                        default=date.today())
    parser.add_argument("-l", help="create registration list for the website",
                        action="store_true")
    args = parser.parse_args()
    
    conn = open_db()

    if args.a:
        new_registrations, updated_registrations = get_new_registrations(conn, args.newregs)
        duplicate_registrations = add_registrations(conn, new_registrations)
        update_registrations(conn, updated_registrations)
        if duplicate_registrations:
            print("Encountered {} duplicate registration(s), updating...".format(len(duplicate_registrations)))
            update_registrations(conn, duplicate_registrations)

    if args.s:
        if isinstance(args.d, str):
            try:
                input_date = datetime.strptime(args.d, "%Y-%m-%d").date()
            except ValueError:
                print("ERROR: date D must be given as YYYY-MM-DD")
                exit()
        else:
            input_date = args.d
        create_start_list(conn, input_date, args.n)

    if args.l:
        create_registrations_list(conn)

    conn.close()
