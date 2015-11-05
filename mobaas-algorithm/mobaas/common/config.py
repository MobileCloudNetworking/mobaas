import datetime

'''
The values that are used for days in the week
'''
MONDAY = "monday"
TUESDAY = "tuesday"
WEDNESDAY = "wednesday"
THURSDAY = "thursday"
FRIDAY = "friday"
SATURDAY = "saturday"
SUNDAY = "sunday"

'''
All days of the week in order
'''
DAYS_OF_THE_WEEK = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]

SECONDS_IN_A_MINUTE = 60
SECONDS_IN_A_HOUR = 3600

SECONDS_IN_A_DAY = 86400
MINUTES_IN_A_DAY = 1440

SECONDS_IN_A_WEEK = 604800

DAYS_IN_A_WEEK = 7

'''
The formats used to express date, time and datetime in string form throughout MOBaaS
'''
ISO_FORMAT_DATE = "%Y-%m-%d"
ISO_FORMAT_TIME = "%H:%M:%S"
ISO_FORMAT_DATETIME = ISO_FORMAT_DATE + " " + ISO_FORMAT_TIME

'''
The day of the beginning of the unix timestamp
'''
UNIX_TIMESTAMP_BEGIN = datetime.datetime( year=1970
                                        , month=1
                                        , day=1
                                        , hour=0
                                        , minute=0
                                        , second=0
                                        , microsecond=0
                                        )

'''
Which modules are request to be able to run MOBaaS in python naming
'''
REQUIRED_MODULES = ["MySQLdb", "numpy", "pykov"]