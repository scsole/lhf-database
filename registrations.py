"""Registrations module for the LHF database."""

import argparse
import csv
import re
import sqlite3
from datetime import datetime, date
from pathlib import Path


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
                    registration_timestamp timestamp NOT NULL,
                    PRIMARY KEY(last_name, first_name, dob)
                    )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS race_genders (
                    registration_id INTEGER NOT NULL UNIQUE,
                    gender TEXT NOT NULL,
                    FOREIGN KEY(registration_id) REFERENCES registrations(registration_id)
                    )""")


def get_new_registrations(conn, reg_input):
    """Read new registration csv file and return a list with new entries.

    Duplicate enties are loged to dup_output if any exist. Registrations
    are considered duplicate if they do not have a unique combination of
    First name, Last name, and DoB. Any duplicates in reg_input will NOT
    be detected.
    """
    confict_dir = Path("import_conflicts")
    dup_output = confict_dir / "duplicate_registrations.csv"
    inv_output = confict_dir / "invalid_registrations.csv"

    newregs = []    # new registrations w/o headers
    dupregs = []    # duplicate registrations w/ headers
    invregs = []    # invalid registrations w/ headers
    emptyregs = 0
    
    # Keys for newregs. These must match the order of the headers in reg_input.
    input_csv_headers = ('registration_timestamp', 'email', 'first_name', 'last_name', 'gender', 'dob', 'age', 'club', 'medical_conditions', 'emergency_name', 'emergency_contact', 'accepted_terms')

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
            dupregs.append(['Existing Registration ID'] + list(next(reader).values())) # skip csv headers
            invregs.append(['Invalid Reason'] + dupregs[0][1:-1])

            for row in reader:
                # Skip empty rows
                if (row['registration_timestamp'] == ''
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
                search = c.fetchone()
                if search == None:
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
                    # Add matched registration_id to the duplicate entry
                    dupregs.append([search[0]] + list(row.values()))
    except FileNotFoundError:
        print("Error: Could not find {}".format(reg_input))
        print("       Please check that this file exists before trying again.")
        exit()


    # Be verbose
    if emptyregs > 0:
        print("Skipped {} empty rows.".format(emptyregs))
    
    if len(dupregs) > 1:
        print("Skipped {} existing registrations. View them in {}".format(len(dupregs) - 1, dup_output))
        confict_dir.mkdir(exist_ok=True)
        with open(dup_output, 'w') as dupfile:
            writer = csv.writer(dupfile)
            writer.writerows(dupregs)

    if len(invregs) > 1:
        print("Skipped {} invalid registrations. View them in {}".format(len(invregs) - 1, inv_output))
        confict_dir.mkdir(exist_ok=True)
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


def add_registrations(conn, reglist):
    """Add registrations to the database."""
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
                                    registration_timestamp
                                ) VALUES (
                                    (SELECT IFNULL(MAX(registration_id), 0) + 1 FROM registrations),
                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
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
                        reg['registration_timestamp']
                        )
                c.execute(sql_insert_statement, reginfo)
                new_regs_num += 1
            except sqlite3.IntegrityError as e:
                # Likely a duplicate entry in the input file
                print(e)
                print("SKIPED: {}".format(reg.values()))
                print("\tThis entry was likely a duplicate within the input file")
    
    print("Added {} new registrations".format(new_regs_num))


def create_start_list(conn, race_date):
    """Generate a start list for Webscorer."""
    start_lists_dir = Path("startlists")
    start_lists_dir.mkdir(exist_ok=True)
    webscorer_headers = ('Bib', 'First name', 'Last name', 'Team name', 'Age', 'Gender', 'Distance')
    startlist = conn.execute("""SELECT registration_id, first_name, last_name, club, dob, registrations.gender, race_genders.gender
                                FROM registrations
                                LEFT JOIN race_genders USING(registration_id)
                                """).fetchall()
    outfile = start_lists_dir / "startlist{}.csv".format(race_date.strftime('%Y%m%d'))

    if len(startlist) > 0:
        for i,entry in enumerate(startlist):
            startlist[i] = list(entry)

            # Alter non-binary genders
            gender = startlist[i].pop()
            if gender != None:
                if startlist[i][5].lower() == "non-binary":
                    startlist[i][5] = gender
                else:
                    print("Warning: Conflicting genders for registration_id={}".format(startlist[i][0]))
                    print("\t Please check that entries in race_genders only match registrations with 'Non-binary' genders.")
            elif startlist[i][5].lower() == "non-binary":
                print("Warning: No race gender specified for registration_id={}".format(startlist[i][0]))
                print("\t Please add an entry to race_genders and recreate this startlist")
            
            # Replace DoB with age at time of race
            startlist[i][4] = years_between(startlist[i][4], race_date)
            
            # Race distance
            startlist[i].append('5km')
        
        # We don't know what distance each runner will undertake ahead of the
        # event. We just need to include each distance at least once.
        startlist[0][-1] = '10km'
    else:
        print("warning: the database was empty when creating a start list")

    with open(outfile, 'w') as csvfile:
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
        print("warning: the database was empty when creating a registrations list")

    with open(outfile, 'w') as csvfile:
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
        # Encounted a leap year
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
    parser.add_argument("-d", help="date of the next race as YYYY-MM-DD, default=today",
                        default=date.today())
    parser.add_argument("-l", help="create registration list for the website",
                        action="store_true")
    args = parser.parse_args()
    
    conn = open_db()

    if args.a:
        add_registrations(conn, get_new_registrations(conn, args.newregs))
    
    if args.s:
        if isinstance(args.d, str):
            try:
                input_date = datetime.strptime(args.d, "%Y-%m-%d").date()
            except ValueError:
                print("Error: date D must be given as YYYY-MM-DD")
                exit()
        else:
            input_date = args.d
        create_start_list(conn, input_date)

    if args.l:
        create_registrations_list(conn)

    conn.close()
