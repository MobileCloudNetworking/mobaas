import datetime

from mobaas.tests import run_tests
from mobaas.tests import config

from mobaas.database_connections import db_connections as d


ORDER = ["test_open_and_close_database_connection"
        , "test_retrieve_connection"
        , "test_execute_something"
        , "test_create_and_delete_table"
        , "test_insert_retrieve_update_retrieve_delete_data"
        ]

def setup_database_connection():
    dbcc = d.DBConnectionCollection("Test")
    dbcc.create_multiple_connections([config.TESTDB])

    return dbcc


def setup_table(dbcc):
    con = dbcc.retrieve_connection(config.TESTDB)
    con.create_table(config.TEST_TABLE, config.TEST_TABLE_LAYOUT)


def teardown_table(dbcc):
    con = dbcc.retrieve_connection(config.TESTDB)
    con.delete_table(config.TEST_TABLE)


def test_open_and_close_database_connection():
    dbcc = setup_database_connection()

    run_tests.compare_answer(dbcc.start_all_connections(), True, "Start all connections")
    run_tests.compare_answer(dbcc.close_all_connections(), True, "Close all connections")


def test_retrieve_connection():
    dbcc = setup_database_connection()

    run_tests.compare_answer(dbcc.retrieve_connection(config.TESTDB).db_name, config.TESTDB, "Retrieve connection")


def test_create_and_delete_table():
    dbcc = setup_database_connection()
    dbcc.start_all_connections()

    con = dbcc.retrieve_connection(config.TESTDB)
    result = con.create_table(config.TEST_TABLE, config.TEST_TABLE_LAYOUT)
    run_tests.compare_answer(result, True, "Check if table was created")
    run_tests.compare_answer(con.table_exists(config.TEST_TABLE), True, "Does the table exist")
    run_tests.compare_answer(con.delete_table(config.TEST_TABLE), True, "Has the table been deleted")
    run_tests.compare_answer(con.table_exists(config.TEST_TABLE), False, "Has the table actually been deleted?")

    dbcc.close_all_connections()


def test_execute_something():
    dbcc = setup_database_connection()
    dbcc.start_all_connections()
    setup_table(dbcc)
    con = dbcc.retrieve_connection(config.TESTDB)

    result = con.execute("SELECT * FROM " + config.TEST_TABLE + ";")
    run_tests.compare_answer(result, True, "Was able to execute something on the database")

    teardown_table(dbcc)
    dbcc.close_all_connections()

DOUBLE1 = 1.1
DOUBLE2 = 2.2
TEXT1 = "1b"
TEXT2 = "2a"
INT1 = 11
INT2 = 23
TIME1 = datetime.time(hour=18, minute=54, second=16)# "18:54:16"
TIME2 = datetime.time(hour=19, minute=31, second=54)# "19:31:54"
DATE1 = datetime.date(year=2004, month=05, day=18)# "2004-05-18"
DATE2 = datetime.date(year=1991, month=10, day=17)# "1991-10-17"
UNIX1 = 1305810474
UNIX2 = 1305810460

DATA1 = [DOUBLE1, TEXT1, INT1, TIME1, DATE1, UNIX1]
DATA2 = [DOUBLE2, TEXT2, INT2, TIME2, DATE2, UNIX2]
FORMAT = [ d.DB_Double
         , d.DB_Text
         , d.DB_Int
         , d.DB_Time
         , d.DB_Date
         , d.DB_Unix_Timestamp_With_MSec
         ]

def _test_column_names_values_types(values):
    result = []

    for column_name, column_type in config.TEST_TABLE_LAYOUT:
        result.append((column_name, values.pop(0), column_type))

    return result


def test_insert_retrieve_update_retrieve_delete_data():
    dbcc = setup_database_connection()
    dbcc.start_all_connections()
    setup_table(dbcc)
    con = dbcc.retrieve_connection(config.TESTDB)

    #insert
    result_insert1 = con.insert_data(config.TEST_TABLE, config.TEST_TABLE_LAYOUT, [DATA1])
    run_tests.compare_answer(result_insert1, True, "Has the data been inserted succesfully?")

    #retrieve1
    data1 = _test_column_names_values_types(list(DATA1))
    retrieve1 = con.retrieve_data_eq("*", config.TEST_TABLE, data1)
    run_tests.compare_answer(len(retrieve1), 1, "Check if there is only 1 row inserted")
    retrieve1_ = d.DatabaseType.format_mysql_row_from_db(retrieve1[0], config.TEST_TABLE_LAYOUT)
    run_tests.compare_answer(retrieve1_["double_c"], DOUBLE1, "Check double 1 value")
    run_tests.compare_answer(retrieve1_["text_c"], TEXT1, "Check text 1 value")
    run_tests.compare_answer(retrieve1_["int_c"], INT1, "Check int 1 value")
    run_tests.compare_answer(retrieve1_["time_c"], TIME1, "Check time 1 value")
    run_tests.compare_answer(retrieve1_["date_c"], DATE1, "Check date 1 value")
    run_tests.compare_answer(retrieve1_["unix_c"], UNIX1, "Check unix 1 value")

    #update
    data2 = _test_column_names_values_types(list(DATA2))
    update1 = con.update_data_eq(config.TEST_TABLE, data2, data1)
    run_tests.compare_answer(update1, True, "Did the update succesfully happen?")
    
    #retrieve2
    retrieve2 = con.retrieve_data_eq("*", config.TEST_TABLE, data2)
    run_tests.compare_answer(len(retrieve2), 1, "Check if there is still only 1 row")
    retrieve2_ = d.DatabaseType.format_mysql_row_from_db(retrieve2[0], config.TEST_TABLE_LAYOUT)
    run_tests.compare_answer(retrieve2_["double_c"], DOUBLE2, "Check double 2 value")
    run_tests.compare_answer(retrieve2_["text_c"], TEXT2, "Check text 2 value")
    run_tests.compare_answer(retrieve2_["int_c"], INT2, "Check int 2 value")
    run_tests.compare_answer(retrieve2_["time_c"], TIME2, "Check time 2 value")
    run_tests.compare_answer(retrieve2_["date_c"], DATE2, "Check date 2 value")
    run_tests.compare_answer(retrieve2_["unix_c"], UNIX2, "Check unix 2 value")

    #delete
    delete1 = con.delete_data_eq(config.TEST_TABLE, data2)
    run_tests.compare_answer(delete1, True, "Could we delete the data?")
    retrieve3 = con.retrieve_data_eq("*", config.TEST_TABLE, data2)
    run_tests.compare_answer(len(retrieve3), 0, "Has the data actually been deleted?")

    teardown_table(dbcc)
    dbcc.close_all_connections()