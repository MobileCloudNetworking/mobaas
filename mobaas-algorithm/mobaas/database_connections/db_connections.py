try:
    import MySQLdb as mdb
except ImportError:
    mdb = None

import datetime

from mobaas.common import error_logging as err
from mobaas.common import connection_collection
from mobaas.common import support

from mobaas import config as central_config


'''
Column types of the database
Expresses how a value should be formatted
between the sql and python types and the
sql format of that type
'''
class DatabaseType():
    column_type = None

    '''
    row should be a dict!
    layout should be a list!
    '''
    @staticmethod
    def format_mysql_row_from_db(row, layout):
        result = {}
        layout_ = dict(layout)

        for column_name, value in row.items():
            result[column_name] = layout_[column_name].format_from_db_value(value)

        return result

    @staticmethod
    def format_mysql_rows_from_db(rows, layout):
        return map(lambda row: DatabaseType.format_mysql_row_from_db(row, layout), rows)

    @staticmethod
    def format_from_db_value(value):
        pass

    @staticmethod
    def format_to_db_value(value):
        pass


class DB_Double(DatabaseType):
    column_type = "DOUBLE(16,4)"
    @staticmethod
    def format_from_db_value(value):
        return float(value)

    @staticmethod
    def format_to_db_value(value):
        return str(value)


class DB_Text(DatabaseType):
    column_type = "TEXT"

    @staticmethod
    def format_from_db_value(value):
        return str(value)

    @staticmethod
    def format_to_db_value(value):
        return "\"" + str(value) + "\""


class DB_Int(DatabaseType):
    column_type = "INT"

    @staticmethod
    def format_from_db_value(value):
        return int(value)

    @staticmethod
    def format_to_db_value(value):
        return str(value)


class DB_Time(DatabaseType):
    column_type = "TIME"

    @staticmethod
    def format_from_db_value(value):
        return (datetime.datetime(year=1970, month=01, day=01, hour=0, minute=0, second=0) + value).time()

    @staticmethod
    def format_to_db_value(value):
        return "\"" + support.create_time_str(value) + "\""


class DB_Date(DatabaseType):
    column_type = "DATE"

    @staticmethod
    def format_from_db_value(value):
        return value

    @staticmethod
    def format_to_db_value(value):
        return "\"" + support.create_date_str(value) + "\""


class DB_Unix_Timestamp_With_MSec(DatabaseType):
    column_type = "BIGINT(15)"

    @staticmethod
    def format_from_db_value(value):
        return long(value)

    @staticmethod
    def format_to_db_value(value):
        return str(value)


class DB_Unix_Timestamp(DatabaseType):
    column_type = "BIGINT(12)"
    @staticmethod
    def format_from_db_value(value):
        return long(value)

    @staticmethod
    def format_to_db_value(value):
        return str(value)


'''
A connection collection to hold database connections (dbcc)
'''
class DBConnectionCollection(connection_collection.ConnectionCollection):
    def __init__(self, name):
        connection_collection.ConnectionCollection.__init__(self, name)

    '''
    Create multiple connections within this dbcc but does not start them yet
    '''
    def create_multiple_connections(self, db_names):
        err.log_error(err.INFO, "Create multiple database connections")
        for db_name in db_names:
            cid = self.next_connection_id()
            DBConnection(cid, self, db_name)

    '''
    Start all connections within this dbcc
    '''
    def start_all_connections(self):
        result = True
        to_start_connections = [connection for connection in self.connections if connection.db_connection is None]

        for connection in to_start_connections:
            result = result and connection.start()

        return result

    '''
    Retrieves a connection to the database that
    is registered with the db_name
    '''
    def retrieve_connection(self, db_name):
        db_connections = [db_connection for db_connection in self.connections if db_connection.db_name == db_name]

        if db_connections:
            result = db_connections[0]
        else:
            result = None

        return result

    '''
    Closes all connections
    '''
    def close_all_connections(self):
        result = True
        err.log_error(err.INFO, "All database connections are being closed...")
        for db_connection in self.connections:
            result = result and db_connection.close()

        return result


class DBConnection(connection_collection.Connection):
    def __init__(self, cid, db_connection_collection, db_name):
        connection_collection.Connection.__init__(self, cid, db_connection_collection)
        self.db_connection = None
        self.db_name = db_name

    '''
    Starts the database connection to the database.
    '''
    def start(self):
        result = False
        try:
            con = mdb.connect(central_config.DB_SERVER_HOSTNAME, central_config.DB_USER, central_config.DB_PWD, self.db_name)
            result = True
        except mdb.Error as e:
            err.log_error(err.CRITICAL, "Could not connect to database " + self.db_name + " because " + str(e.message))
        else:
            self.db_connection = con

        return result

    def close(self):
        result = False
        try:
            self.db_connection.close()
            result = True
        except mdb.Error as e:
            err.log_error(err.ERROR, "Tried to close the db connection but could not. Removed it anyways")
            err.log_error(err.ERROR, "Error: " + e.message)
        self.connection_collection.remove_connection(self.cid)

        return result

    '''
    Generates a where class based on the where values
        where - List of tuples where each tuple consists of (name, operator, value, type) with types (str, str, str, DatabaseType)
    '''
    @staticmethod
    def _generate_where_clause(where):
        if where:
            column_names_formatted_values = [n + " " + op + " " + t.format_to_db_value(v) for n, op, v, t in where] #First, format all conditions in the where clause
            where_clause_meat = " AND ".join(column_names_formatted_values) #Finally, collapse the list by joining everything with AND
            where_clause = "WHERE " + where_clause_meat + " "
        else:
            where_clause = ""

        return where_clause

    def retrieve(self, select, table, where_query):
        cur = self.db_connection.cursor(mdb.cursors.DictCursor)

        select_str = "SELECT " + ", ".join(select)
        table_str = "FROM " + table
        query = select_str + " " + table_str + " " + where_query + ";"

        try:
            cur.execute(query)
            result = cur.fetchall()
            cur.close()
        except mdb.Error:
            result = False

        return result

    '''
    Function to retrieve data from a table
        select - List of strings on which fields you should select
        table - String of the table name
        where - List of tuples representing the conditions. Each tuple consists of (column name, operator, value, type) with types (str, str, str, DatabaseType)
    It returns a list of dictionaries where the keys are the column names in each entry in the list
    '''
    def retrieve_data(self, select, table, where):
        where_clause = DBConnection._generate_where_clause(where)
        return self.retrieve(select, table, where_clause)



    '''
    Function to retrieve data from a table where all columns equal a certain value
        select - List of strings on which fields you should select
        table - String of the table name
        where - List of tuples representing the conditions. Each tuple consists of (column name, value, type) with types (str, str, DatabaseType)
    It returns a list of dictionaries where the keys are the column names in each entry in the list
    '''
    def retrieve_data_eq(self, select, table, where):
        return self.retrieve_data(select, table, [(n, "=", v, t) for n, v, t in where])

    '''
    Convenience function to insert data. Assumes data row is new
    and does not already exist.
        table_name - Name of the table that the data is inserted into
        column_names_types - List of tuples. Each tuple consist of column name followed by type.
        list_of_values - A list containing lists. Each sub-list contains the values to insert in order with the column_names_types
                         e.g. [[1,2,3], [1,2,3], [4,5,6]] where the table has 3 int columns
    Returns boolean to determine if succeeded
    '''
    def insert_data(self, table_name, column_names_types, list_of_values):
        result = False
        if self.table_exists(table_name) and column_names_types and list_of_values:
            column_names, types = zip(*column_names_types)

            list_of_values_str = []
            for values in list_of_values:
                list_of_value_str = []
                for i, value in enumerate(values):
                    formatted_value = types[i].format_to_db_value(value)
                    list_of_value_str.append(formatted_value)

                list_of_values_str.append("(" + ", ".join(list_of_value_str) + ")")

            values_str = ", ".join(list_of_values_str)
            columns_str = ", ".join(column_names)

            query = "INSERT INTO " + table_name + " (" + columns_str + ") VALUES " + values_str + ";"

            result = self.execute(query)
        return result


    '''
    Convenience function to update data.
        table_name - Name of the table where the data is updated
        set_ - List of tuples. Each tuple consist of column name followed by the value followed by the type
        where - List of tuples representing the conditions. Each tuple consists of (column name, operator, value, type) with types (str, str, str, DatabaseType)
    Returns boolean to determine if succeeded
    '''
    def update_data(self, table_name, set_, where):
        result = False

        if self.table_exists(table_name) and set_:
            set_column_names_formatted_values_str = [str(n) + " = " + str(t.format_to_db_value(v)) for n, v, t in set_]
            set_str = ", ".join(set_column_names_formatted_values_str)

            where_clause = DBConnection._generate_where_clause(where)

            result = self.execute("UPDATE " + table_name + " SET " + set_str + " " + where_clause + ";")

        return result

    '''
    Convenience function to update data.
        table_name - Name of the table where the data is updated
        set_ - List of tuples. Each tuple consist of column name followed by the value followed by the type
        where - List of tuples representing the conditions. Each tuple consists of (column name, value, type) with types (str, str, DatabaseType)
    Returns boolean to determine if succeeded
    '''
    def update_data_eq(self, table_name, set_, where):
        return self.update_data(table_name, set_, [(n, "=", v, t) for n, v, t in where])

    '''
    Deletes a certain data set from the table in the database.
    If an empty where list is supplied, all data is deleted from the table.
        table_name - Name of the table
        where - List of tuples representing the conditions. Each tuple consists of (column name, operator, value, type) with types (str, str, str, DatabaseType)
    Returns boolean to determine if succeeded
    '''
    def delete_data(self, table_name, where):
        where_clause = DBConnection._generate_where_clause(where)

        result = self.execute("DELETE FROM " + table_name + " " + where_clause + ";")

        return result

    def delete_data_eq(self, table_name, where):
        return self.delete_data(table_name, [(n, "=", v, t) for n, v, t in where])

    '''
    Conveniance function to create simple tables. If it already exists, nothing is done.
        table_name - String of the new table name
        column_names_types - List of tuples with each tuple representing a column. Each tuple first has the column name followed by the DatabaseType
    '''
    def create_table(self, table_name, column_names_types):
        result = False

        if column_names_types and not self.table_exists(table_name):
            column_string_1 = [column_name + " " + column_type.column_type for column_name, column_type in column_names_types] #First set all the names and types in 1 string
            column_string_2 = ", ".join(column_string_1) #Collapse all column names and types with a seperating comma
            column_string_3 = "(" + column_string_2 + ")"  #Put quotes around the whole

            result = self.execute("CREATE TABLE " + table_name + " " + column_string_3 + ";")

        return result

    '''
    Checks if a certain table exists
        table_name - Name of the table
    Returns a boolean True if the table exists or False if the table doesn't exist
    '''
    def table_exists(self, table_name):
        results = self.retrieve_data(["*"], "information_schema.tables", [("table_schema", "=", self.db_name, DB_Text), ("table_name", "=", table_name, DB_Text)])
        return len(results) != 0

    '''
    Deletes the table from the given database
        table_name - Name of the table to drop
    '''
    def delete_table(self, table_name):
        result = False

        if self.table_exists(table_name):
            result = self.execute("DROP TABLE " + table_name + ";")

        return result

    '''
    Executes a certain query on the database. Usable for non-returning results only
        query - String of the query to execute
    Returns a boolean if it succeeds(True) or fails(False)
    '''
    def execute(self, query):
        result = False
        cur = self.db_connection.cursor(mdb.cursors.DictCursor)

        try:
            cur.execute(query)
            self.db_connection.commit()
            cur.close()
            result = True
        except mdb.Error as e:
            err.log_error(err.CRITICAL, "Tried to perform a query on the database, but it wasn't able to!")
            err.log_error(err.CRITICAL, "Query: " + query)
            err.log_error(err.CRITICAL, "Database: " + self.db_name)
            err.log_error(err.CRITICAL, "Error: " + e.message)

            if self.db_connection:
                try:
                    self.db_connection.rollback()
                except mdb.Error as e_rollback:
                    err.log_error(err.CRITICAL, "Tried to rollback the failed query but this failed as well. Your database might have become corrupted!")
                    err.log_error(err.CRITICAL, "Error: " + e_rollback.message)

        return result
