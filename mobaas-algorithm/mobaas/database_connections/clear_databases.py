import inspect

from mobaas.common import error_logging as err
from mobaas.common import support

from mobaas.database_connections import db_connections
from mobaas.database_connections import db_layout

'''
Clears all databases from tables as found in db_layout.DATABASE_NAMES
'''
def clear_databases():
    dbcc = db_connections.DBConnectionCollection("Clearing all databases")
    dbcc.create_multiple_connections(db_layout.DATABASE_NAMES)
    all_started = dbcc.start_all_connections()

    if all_started:
        err.log_error(err.INFO, "Succesfully started all db connections. Doing maintenance...")
        all_classes = inspect.getmembers(db_layout, inspect.isclass)

        for _, class_p in all_classes:
            class_p.delete_table(dbcc)


    else:
        err.log_error(err.CRITICAL, "Could not connect to all databases. Not doing any maintence...")

    dbcc.close_all_connections()

'''
Only call if this module is started directly
'''
if __name__ == "__main__":
    if support.everything_installed():
        clear_databases()