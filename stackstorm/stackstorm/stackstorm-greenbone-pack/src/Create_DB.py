import sqlite3

def dict_factory(cursor, row):
    """
    allows outputting of SQL queries as dictionaries
    :param cursor: sqlite cursor object
    :param row: a row of db query results to output (as list)
    :return:
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def ConnectToDatabase(db_path):
    """
    Connects to database and gets connection object
    :param db_path: Path to database
    :return: sqlite3 db connection object
    """
    db = sqlite3.connect(db_path)
    db.row_factory = dict_factory
    return db

def CreateTable(db):
    """
    Tables for storing vulnerability information will be created in database file
    :param db: sqlite3 db connection object
    :return: updated db object
    """

    db_cursor = db.cursor()
    db_cursor.execute("PRAGMA foreign_keys = 3")
    db_cursor.executescript('''
    CREATE TABLE IF NOT EXISTS Vulnerabilities(
        NVT_OID                     VARCHAR(30)     PRIMARY KEY,
        NVT_Name                    VARCHAR(255)    NOT NULL,
        Port                        INTEGER         NULL,
        Protocol                    TEXT CHECK( Protocol IN ('tcp', 'udp', NULL))               NULL,
        Severity                    TEXT CHECK( Severity IN ('Log','Low','Medium','High'))      NOT NULL,
        Solution_Type               VARCHAR(255)    NULL,
        Summary                     TEXT            NOT NULL,
        Specific_Result             TEXT            NOT NULL,
        Solution                    TEXT            NULL,
        Impact                      TEXT            NULL,
        Detection_Method            TEXT            NOT NULL,
        Insight                     TEXT            NULL,
        Affected_Software           TEXT            NULL,
        Product_Detection_Result    TEXT            NULL,
        Other_References            TEXT            NULL
    );

    CREATE TABLE IF NOT EXISTS CVEs(
        NVT_OID     VARCHAR(30)     NOT NULL,
        CVE         VARCHAR(255)    NOT NULL,
        FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID)
    );

    CREATE TABLE IF NOT EXISTS BIDs(
        NVT_OID     VARCHAR(30)     NOT NULL,
        BID         VARCHAR(255)    NOT NULL,
        FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID)
    );

    CREATE TABLE IF NOT EXISTS CERTs(
        NVT_OID     VARCHAR(30)     NOT NULL,
        CERT        VARCHAR(255)    NOT NULL,
        FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID)
    );

    CREATE TABLE IF NOT EXISTS Hosts(
        IP          VARCHAR(255)    PRIMARY KEY,
        Resource_ID VARCHAR(255)    NULL,
        Hostname    VARCHAR(255)    NULL,
        User_ID     VARCHAR(255)    NULL
    );

    CREATE TABLE IF NOT EXISTS Metadata(
        Task_ID     VARCHAR(255)    PRIMARY KEY,
        Task_Name   VARCHAR(255)    NOT NULL
    );

    CREATE TABLE IF NOT EXISTS Greenbone_Vulnerabilities(
        Result_ID   VARCHAR(255)    PRIMARY KEY,
        Timestamp   TEXT            NOT NULL,
        IP_Status   TEXT CHECK ( IP_Status IN ('Active', 'Inactive', 'Server Changed')) Not NULL Default 'Active',
        IP          VARCHAR(255)    Not NULL,
        NVT_OID     VARCHAR(30)     NOT NULL,
        Task_ID     VARCHAR(255)    NOT NULL,
        FOREIGN KEY(IP) REFERENCES Hosts(IP),
        FOREIGN KEY(NVT_OID) REFERENCES Vulnerabilities(NVT_OID),
        FOREIGN KEY(Task_ID) REFERENCES Metadata(Task_ID)
    );

    ''')
    db.commit()
    return db

if __name__ == "__main__":
    db = ConnectToDatabase("Greenbone.db")
    CreateTable(db)
