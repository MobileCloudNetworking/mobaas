from mobaas.database_connections import db_connections as d

TESTDB = "test_database"

TEST_TABLE = "test_table"
TEST_TABLE_LAYOUT = [ ("double_c", d.DB_Double)
                    , ("text_c", d.DB_Text)
                    , ("int_c", d.DB_Int)
                    , ("time_c", d.DB_Time)
                    , ("date_c", d.DB_Date)
                    , ("unix_c", d.DB_Unix_Timestamp_With_MSec)
                    ]

TEST_ERRORS = 0
CURRENT_TEST = ""
