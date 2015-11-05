import os.path
import datetime

from mobaas.common import error_logging as err

from mobaas.database_connections import db_connections

ID_OF_OBJECT = "oid"
ID_OF_OBJECT_TYPE = db_connections.DB_Int

'''
ORM of MOBaaS
Each inheritor of DBObject has a lot of cool automated functions
to insert, update or delete data from the corresponding database

DBObject also keeps track of all the available object id's(oids)
so there will be a lot of fewer queries to the database.
Each instance of DBObject will have it's own returned_oids list which
is initiated upon the first save or save many.

All of the other functions are pretty much self explanatory and follow
the common ORM structure.
'''
class DBObject:
    database_name = ""
    table_name = ""
    layout = [(ID_OF_OBJECT, ID_OF_OBJECT_TYPE)]
    returned_oids = None
    max_given_oid = -1

    def __init__(self, db_connection, oid):
        self.db_connection = db_connection
        self.oid = oid

    def save(self):
        if self.is_not_saved():
            self.__class__._set_oid_variables(self.db_connection)

            #First time save, give an id
            self.oid = self.__class__.next_id()
            values = self._get_all_values()

            result = self.db_connection.insert_data(self.table_name, self.layout, [values])
        else:
            #Already in the database, update all fields
            column_names_values_types = self._get_all_column_names_values_types()
            result = self.db_connection.update_data_eq(self.table_name, column_names_values_types, [(ID_OF_OBJECT, self.oid, ID_OF_OBJECT_TYPE)])

        return result

    def is_not_saved(self):
        return self.oid is None

    def delete(self):
        if not (self.oid is None):
            result = self.db_connection.delete_data_eq(self.table_name, [(ID_OF_OBJECT, self.oid, ID_OF_OBJECT_TYPE)])
            self.__class__.returned_oids.append(self.oid)
        else:
            result = False

        return result

    def column_names(self):
        result = []

        for name, _ in self.layout:
            result.append(name)

        return result

    def _get_all_column_names_values_types(self):
        column_names_values_types = []
        result = False

        values = self._get_all_values()

        if values:
            result = True

            i = 0
            while i < len(values):
                value = values[i]
                column_name, type = self.layout[i]
                column_names_values_types.append((column_name, value, type))
                i += 1

        return column_names_values_types if result else None

    def _get_all_values(self):
        values = []
        result = True

        for column_name, _ in self.layout:
            if hasattr(self, column_name):
                values.append(getattr(self, column_name))
            else:
                err.log_error(err.ERROR, "Tried to use an object from table " + self.table_name + " but the object \
                                          didn't have the attribute " + column_name)
                result = False

        return values if result else None

    @classmethod
    def _set_oid_variables(cls, db_connection):
        if cls.max_given_oid == -1:
            cls.max_given_oid = cls._get_max_id_in_table(db_connection)
            cls.returned_oids = cls._find_missing_oids(db_connection, cls.max_given_oid)

    @classmethod
    def _unset_oid_variables(cls):
        cls.max_given_oid = -1
        cls.returned_oids = []

    @classmethod
    def _find_missing_oids(cls, db_connection, max_oid):
        oids_mysql_rows = db_connection.retrieve_data([ID_OF_OBJECT], cls.table_name, [])
        oids = [db_connections.DB_Int.format_from_db_value(row[ID_OF_OBJECT]) for row in oids_mysql_rows]
        oids_with_max = oids + [max_oid]
        missing_oids = []

        i = 0
        while i < len(oids_with_max) - 1:
            if not (oids_with_max[i + 1] - oids_with_max[i] == 1):
                missing_oids.extend(range(oids_with_max[i] + 1, oids_with_max[i + 1] - 1))
            i += 1

        return missing_oids


    @classmethod
    def _get_max_id_in_table(cls, db_connection):
        retrieved_list = db_connection.retrieve_data(["MAX("+ID_OF_OBJECT+") AS max_id"], cls.table_name, [])
        max_id_sql = retrieved_list[0]["max_id"]

        if max_id_sql is None:
            max_id = -1
        else:
            max_id = db_connections.DB_Int.format_from_db_value(max_id_sql)

        return max_id

    def __eq__(self, other):
        column_names_1 = self.column_names()
        column_names_2 = other.column_names()
        column_names = list(set(column_names_1 + column_names_2)) #remove duplicates

        result = True
        for column_name in column_names:
            if hasattr(self, column_name) and hasattr(other, column_name):
                result = getattr(self, column_name) == getattr(other, column_name)
            else:
                result = False

        return result

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        column_names = self.column_names()
        columns_and_values = []

        for column_name in column_names:
            columns_and_values.append(column_name + ": " + str(getattr(self, column_name)))

        return "|" + ", ".join(columns_and_values) + "|"

    def __repr__(self):
        return str(self)

    @classmethod
    def retrieve_connection(cls, dbcc):
        return dbcc.retrieve_connection(cls.database_name)

    @classmethod
    def next_id(cls):
        if len(cls.returned_oids) == 0:
            result = cls.max_given_oid + 1
            cls.max_given_oid = result
        else:
            result = cls.returned_oids.pop(0)

        return result


    @classmethod
    def object_from_mysql_row(cls, dbcc, mysql_row):
        values_dict = db_connections.DatabaseType.format_mysql_row_from_db(mysql_row, cls.layout)

        obj = cls(dbcc.retrieve_connection(cls.database_name), values_dict[ID_OF_OBJECT])
        obj.db_connection = cls.retrieve_connection(dbcc)

        del values_dict[ID_OF_OBJECT]

        for column_name, column_value in values_dict.items():
            setattr(obj, column_name, column_value)

        return obj

    '''
    conditions is a list of tuples. (column_name, operator, condition)
    '''
    @classmethod
    def retrieve_objects(cls, dbcc, conditions):
        con = dbcc.retrieve_connection(cls.database_name)

        layout_dict = dict(cls.layout)
        columns_ops_values_types = []

        for column_name, op, value in conditions:
            columns_ops_values_types.append((column_name, op, value, layout_dict[column_name]))

        start_time_retrieve = datetime.datetime.now()

        rows = con.retrieve_data("*", cls.table_name, columns_ops_values_types)
        result = []

        start_time_create = datetime.datetime.now()
        for row in rows:
            result.append(cls.object_from_mysql_row(dbcc, row))

        return result

    @classmethod
    def new(cls, dbcc, *args):
        new_object = cls(cls.retrieve_connection(dbcc), None)
        column_names = [column_name for column_name, column_type in cls.layout]
        column_names.remove(ID_OF_OBJECT) #Remove from list to add values to.

        for column_name, arg in zip(column_names, args):
            setattr(new_object, column_name, arg)

        return new_object

    @classmethod
    def save_many(cls, dbcc, objects):
        conn = cls.retrieve_connection(dbcc)
        cls._set_oid_variables(conn)

        to_insert_values = []
        result = True

        for obj in objects:
            if obj.is_not_saved():
                obj.oid = cls.next_id()
                to_insert_values.append(obj._get_all_values())
            else:
                #Just need an update. Do immediately
                result = result and obj.save()

        if to_insert_values:
            result = result and conn.insert_data(cls.table_name, cls.layout, to_insert_values)

        return result


    @classmethod
    def create_table(cls, dbcc):
        db_connection = cls.retrieve_connection(dbcc)
        if not db_connection.table_exists(cls.table_name):
            result = db_connection.create_table(cls.table_name, cls.layout)

            if result:
                err.log_error(err.INFO, "Table created: " + cls.table_name)
            else:
                err.log_error(err.CRITICAL, "Table " + cls.table_name +  " couldn't be created!")
        else:
            result = False
            err.log_error(err.ERROR, "Table " + cls.table_name +  " already exists!")

        return result

    @classmethod
    def table_exists(cls, dbcc):
        return cls.retrieve_connection(dbcc).table_exists(cls.table_name)

    @classmethod
    def clear_table(cls, dbcc):
        db_connection = cls.retrieve_connection(dbcc)
        if db_connection.table_exists(cls.table_name):
            result = cls.delete_table(db_connection)

            if result:
                result = result and cls.create_table(db_connection)

                if result:
                    err.log_error(err.INFO, "Table " + cls.table_name + " has been cleared")

            if not result:
                err.log_error(err.CRITICAL, "Table " + cls.table_name + " could not be cleared!")
        else:
            result = False
            err.log_error(err.ERROR, "Table " + cls.table_name +  " does not exist!")

        return result

    @classmethod
    def delete_table(cls, dbcc):
        db_connection = cls.retrieve_connection(dbcc)
        if db_connection.table_exists(cls.table_name):
            result = db_connection.delete_table(cls.table_name)

            if result:
                cls._unset_oid_variables()
                err.log_error(err.INFO, "Table deleted: " + cls.table_name)
            else:
                err.log_error(err.CRITICAL, "Table " + cls.table_name +  " couldn't be deleted!")
        else:
            result = False
            err.log_error(err.INFO, "Table " + cls.table_name +  " does not exist!")

        return result

    '''
    func_str_to_obj expects filename, extension and an array of words and should return a list of arguments
    '''
    @classmethod
    def fill_table_from_file(cls, dbcc, delimiter, filepath, func_str_to_obj_args):
        result = True

        err.log_error(err.INFO, "Filling table " + cls.table_name + " with data from file " + filepath)
        try:
            f = open(filepath, 'r')
        except IOError as e:
            err.log_error(err.CRITICAL, "Tried to read a file but it failed: [" + str(e.errno) + "] " + str(e.message))
            result = False
        else:
            i = 0
            path, extension = os.path.splitext(filepath)
            _, filename = os.path.split(path)
            objects = []

            for line in f:
                i += 1

                arguments = func_str_to_obj_args(filename, extension, line.split(delimiter))
                obj = cls.new(dbcc, *arguments)
                objects.append(obj)

            cls.save_many(dbcc, objects)
            f.close()

        return result

    '''
    func_str_to_obj expects filename, extension and an array of words and should return a list of arguments
    '''
    @classmethod
    def fill_table_from_files(cls, dbcc, delimiter, filepaths, func_str_to_obj_args):
        result = True

        for filepath in filepaths:
            result = result and cls.fill_table_from_file(dbcc, delimiter, filepath, func_str_to_obj_args)

        return result
