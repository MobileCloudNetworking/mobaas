import datetime

from mobaas.tests import run_tests
from mobaas.tests import config

from mobaas.database_connections import db_objects
from mobaas.database_connections import db_connections

ORDER = [ "init"
        , "test_create_object"
        , "test_create_and_delete_object_table"
        , "test_save_and_delete_object"
        , "test_update"
        , "test_multiple_objects"
        , "test_object_from_row"
        , "test_equals"
        , "test_retrieve_objects"
        , "shutdown"
        ]

class TestObject(db_objects.DBObject):
    database_name = config.TESTDB
    table_name = config.TEST_TABLE
    layout = db_objects.DBObject.layout + \
             config.TEST_TABLE_LAYOUT

def _test_column_names_values(values):
    result = []

    for column_name, _ in config.TEST_TABLE_LAYOUT:
        result.append((column_name, values.pop(0)))

    return result

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

DATA1_DICT = _test_column_names_values(list(DATA1))
DATA2_DICT = _test_column_names_values(list(DATA2))

def _dict_values_only(dict_):
    result = []
    for name, _ in config.TEST_TABLE_LAYOUT:
        result.append(dict_[name])

    return result

def _check_object_attributes(obj, values):
    for name, value in _test_column_names_values(values):
        if hasattr(obj, name):
            run_tests.compare_answer(getattr(obj, name), value, "Sees if the correct attribute " + name + " is set")
        else:
            run_tests.compare_answer(None, value, "Could not find the attribute in object " + str(obj))

DBCC = db_connections.DBConnectionCollection("Test db_objects")


def setup_object():
    return TestObject.new(DBCC, DOUBLE1, TEXT1, INT1, TIME1, DATE1, UNIX1)

def setup_object_2():
    return TestObject.new(DBCC, DOUBLE2, TEXT2, INT2, TIME2, DATE2, UNIX2)


def setup_table():
    return TestObject.create_table(DBCC)


def delete_table():
    return TestObject.delete_table(DBCC)


def init():
    DBCC.create_multiple_connections([config.TESTDB])
    DBCC.start_all_connections()


def test_create_object():
    obj = setup_object()

    _check_object_attributes(obj, list(DATA1))


def test_create_and_delete_object_table():
    run_tests.compare_answer(TestObject.create_table(DBCC), True, "Was able to create the table")
    run_tests.compare_answer(TestObject.delete_table(DBCC), True, "Was able to delete the table")


def test_save_and_delete_object():
    setup_table()

    obj = setup_object()

    #delete before saving and an ID is given
    run_tests.compare_answer(obj.delete(), False, "Try to delete before saving an object")

    #save
    save_result = obj.save()
    run_tests.compare_answer(save_result, True, "See if the save of the object succeeded")

    #retrieve1
    retrieve1 = DBCC.retrieve_connection(config.TESTDB).retrieve_data("*", config.TEST_TABLE, [])
    run_tests.compare_answer(len(retrieve1), 1, "Sees if only one row has been inserted")

    retrieve1_ = db_connections.DatabaseType.format_mysql_row_from_db(retrieve1[0], TestObject.layout)
    values1 = _dict_values_only(retrieve1_)
    _check_object_attributes(obj, values1)

    #delete
    result = obj.delete()
    run_tests.compare_answer(result, True, "Sees if the delete has succeeded")

    #retrieve2
    retrieve2 = DBCC.retrieve_connection(config.TESTDB).retrieve_data("*", config.TEST_TABLE, [])
    run_tests.compare_answer(len(retrieve2), 0, "Checks to see if the table is empty")

    delete_table()


def test_update():
    setup_table()
    obj = setup_object()

    obj.save()
    id_1 = obj.oid

    obj.double_c = DOUBLE2
    obj.text_c = TEXT2
    obj.int_c = INT2
    obj.time_c = TIME2
    obj.date_c = DATE2
    obj.unix_c = UNIX2

    #Update
    update_result = obj.save()
    run_tests.compare_answer(update_result, True, "Check to see if update succeeded")

    #Retrieve1
    retrieve1 = DBCC.retrieve_connection(config.TESTDB).retrieve_data("*", config.TEST_TABLE, [])
    run_tests.compare_answer(len(retrieve1), 1, "Sees if only one row has been inserted")

    retrieve1_ = db_connections.DatabaseType.format_mysql_row_from_db(retrieve1[0], TestObject.layout)
    values2 = _dict_values_only(retrieve1_)
    _check_object_attributes(obj, values2)
    run_tests.compare_answer(retrieve1_["oid"], id_1, "Check to see if the id still matches")

    obj.delete()

    delete_table()


def test_multiple_objects():
    setup_table()
    obj_1 = setup_object()
    obj_2 = setup_object()

    obj_1.save()
    obj_2.save()

    #Check to see if id matches
    run_tests.compare_answer(obj_1.oid, 0, "Check to see if first id = 0")
    run_tests.compare_answer(obj_2.oid, 1, "Check to see if second id = 1")

    #Check to see if both are in the table
    retrieve1 = DBCC.retrieve_connection(config.TESTDB).retrieve_data("*", config.TEST_TABLE, [])
    run_tests.compare_answer(len(retrieve1), 2, "Sees if both rows have been inserted")

    #Check first object values
    retrieve1_ = db_connections.DatabaseType.format_mysql_row_from_db(retrieve1[0], TestObject.layout)
    values1 = _dict_values_only(retrieve1_)
    _check_object_attributes(obj_1, values1)

    #check second object values
    retrieve2_ = db_connections.DatabaseType.format_mysql_row_from_db(retrieve1[1], TestObject.layout)
    values2 = _dict_values_only(retrieve2_)
    _check_object_attributes(obj_2, values2)

    #Check if one can be deleted and one still exists
    obj_1.delete()

    retrieve2 = DBCC.retrieve_connection(config.TESTDB).retrieve_data("*", config.TEST_TABLE, [])
    run_tests.compare_answer(len(retrieve2), 1, "Sees if one row still exists")

    retrieve3_ = db_connections.DatabaseType.format_mysql_row_from_db(retrieve2[0], TestObject.layout)
    values3 = _dict_values_only(retrieve3_)
    _check_object_attributes(obj_2, values3)

    #delete last one
    obj_2.delete()

    retrieve3 = DBCC.retrieve_connection(config.TESTDB).retrieve_data("*", config.TEST_TABLE, [])
    run_tests.compare_answer(len(retrieve3), 0, "Sees if no rows still exists")

    delete_table()


def test_object_from_row():
    setup_table()
    obj_1 = setup_object()
    obj_1.save()

    #Retrieve from table and build object
    retrieve1 = DBCC.retrieve_connection(config.TESTDB).retrieve_data("*", config.TEST_TABLE, [])
    obj_1_ = TestObject.object_from_mysql_row(DBCC, retrieve1[0])

    run_tests.compare_answer(obj_1 == obj_1_, True, "Compare if both objects are the same")

    obj_1.delete()

    delete_table()


def test_equals():
    obj_1 = setup_object()
    obj_2 = setup_object()

    run_tests.compare_answer(obj_1 == obj_2, True, "Testing two same objects")


def test_retrieve_objects():
    setup_table()
    obj_1 = setup_object()
    obj_2 = setup_object_2()
    obj_2.double_c = DOUBLE1

    obj_1.save()
    obj_2.save()

    objects = TestObject.retrieve_objects(DBCC, [("double_c", "=", DOUBLE1)])

    obj_1_ = [obj for obj in objects if obj.oid == 0][0]
    obj_2_ = [obj for obj in objects if obj.oid == 1][0]

    run_tests.compare_answer(obj_1 == obj_1_, True, "Test to see if first object matches")
    run_tests.compare_answer(obj_2 == obj_2_, True, "Test to see if second object matches")
    run_tests.compare_answer(len(objects), 2, "Test to see if only 2 objects are created")

    delete_table()


def shutdown():
    DBCC.close_all_connections()