import inspect

from mobaas.common import support
from mobaas.common import error_logging as err

from mobaas.database_connections import db_connections
from mobaas.database_connections import db_layout

'''
Setup all tables within the databases. The tables are found within db_layout
'''
def databases_setup():
    dbcc = db_connections.DBConnectionCollection("Setting up all tables")
    dbcc.create_multiple_connections(db_layout.DATABASE_NAMES)
    all_started = dbcc.start_all_connections()

    if all_started:
        err.log_error(err.INFO, "Succesfully started all db connections. Doing maintenance...")
        all_classes = inspect.getmembers(db_layout, inspect.isclass)

        for _, class_p in all_classes:
            class_p.create_table(dbcc)

    else:
        err.log_error(err.CRITICAL, "Could not connect to all databases. Not doing any maintence...")

    dbcc.close_all_connections()

'''
Only call if this module is started directly
'''
if __name__ == "__main__":
    if support.everything_installed():
        databases_setup()