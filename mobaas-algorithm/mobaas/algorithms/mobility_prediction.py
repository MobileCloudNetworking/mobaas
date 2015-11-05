import pykov
import datetime

from mobaas.common import support
from mobaas.common import config as common_config
from mobaas.common import error_logging as err

from mobaas.algorithms import config

from mobaas.database_connections import db_layout

from mobaas.mobaas_protocol import data_objects


'''
Class used in order to prepare the data for the Pykov Chain.
It has all the data the Pykov Chain needs to calculate a prediction.
'''
class UserEntry():
    def __init__(self, day, minute_of_day, cell_id):
        self.day = day
        self.minute_of_day = minute_of_day
        self.cell_id = cell_id

    '''
    Checks to see if the other UserEntry should be the next one in the
    Pykov Chain. It is based on same day, next minute of day
    '''
    def other_is_next(self, other):
        if self.minute_of_day == common_config.MINUTES_IN_A_DAY - 1:
            next_day = support.next_day(self.day)

            result = other.minute_of_day == 0 and other.day == next_day
        else:
            result = self.minute_of_day + 1 == other.minute_of_day and self.day == other.day

        return result

    '''
    Checks to see if the other UserEntry should be the previous one in the
    Pykov Chain. It is based on same day, previous minute of day
    '''
    def previous_day_minute_of_day(self):
        if self.minute_of_day - 1 < 0:
            day = support.previous_day(self.day)
            minute_of_day = common_config.MINUTES_IN_A_DAY - 1
        else:
            day = self.day
            minute_of_day = self.minute_of_day - 1

        return day, minute_of_day

    '''
    Returns the day and minute of day of the user entry that should be the
    next one in the pykov chain. It checks to see if it should already be
    the next day or not.
    '''
    def next_day_minute_of_day(self):
        if self.minute_of_day + 1 > common_config.MINUTES_IN_A_DAY - 1:
            day = support.next_day(self.day)
            minute_of_day = 0
        else:
            day = self.day
            minute_of_day = self.minute_of_day + 1

        return day, minute_of_day

    '''
    Returns the unique pykov key of this user entry
    '''
    def to_pykov_key(self):
        return "c" + "_".join([str(self.cell_id), self.day, str(self.minute_of_day)])

    '''
    Creates a user entry from a pykov key
    '''
    @staticmethod
    def from_pykov_key(pykov_key):
        c_str = pykov_key[0]
        info_str = pykov_key[1:]
        words = info_str.split("_")

        cell_id = int(words[0])
        day_str = words[1]
        minute_of_day = int(words[2])

        return UserEntry(day_str, minute_of_day, cell_id)

    def __eq__(self, other):
        return self.cell_id == other.cell_id and self.day == other.day and self.minute_of_day == other.minute_of_day

    def __ne__(self, other):
        return not (self == other)

    '''
    Hashes the user entry according to its unique characteristics by putting all numbers next to each other
    of the day, minute of day and the cell_id
    '''
    def __hash__(self):
        numbers = map(ord, self.day)
        numbers.append(self.minute_of_day)
        numbers.append(self.cell_id)
        numbers = map(str, numbers)
        hash = "".join(numbers)
        return int(hash)

    def __str__(self):
        return "| UserEntry {" + str(self.day) + "," + str(self.minute_of_day) + "," + str(self.cell_id) + "}"

    def __repr__(self):
        return str(self)


'''
Retrieves all data from the history_date until the current_date with respect to which
days should be included. Which days are dependant on the days between the current_date and
the predicted date (so friday till sunday for instance).
Returns a list of mp_fetched
'''
def retrieve_user_mobility_data_single_user(dbcc, user_id, current_date, predicted_date):
    history_date = calculate_mp_history_date(current_date)

    current_week_date_range = support.unix_weeks_timestamp_to_date_range(support.date_to_unix_weeks_timestamp(current_date))
    history_week_date_range = support.unix_weeks_timestamp_to_date_range(support.date_to_unix_weeks_timestamp(history_date))
    begin_of_history_week = history_week_date_range.min_range
    end_of_current_week = current_week_date_range.max_range

    current_day = support.calc_day(current_date)
    predicted_day = support.calc_day(predicted_date)
    applicable_days = support.difference_of_days(current_day, predicted_day)

    con = dbcc.retrieve_connection(db_layout.MPFetched.database_name)
    select = "*"
    table = db_layout.MPFetched.table_name
    layout_dict = dict(db_layout.MPFetched.layout)
    user_id_sql = layout_dict["user_id"].format_to_db_value(user_id)
    end_date_sql = layout_dict["date"].format_to_db_value(end_of_current_week)
    start_date_sql = layout_dict["date"].format_to_db_value(begin_of_history_week)
    applicable_days_sql = map(layout_dict["day"].format_to_db_value, applicable_days)


    applicable_days_query = " AND (day = " + " OR day = ".join(applicable_days_sql) + ")"

    where_query = ("WHERE user_id = " + user_id_sql +
                   " AND date <= " + end_date_sql +
                   " AND date >= " + start_date_sql +
                   applicable_days_query
                  )

    err.log_error(err.INFO, "Retrieving data for MP between " + str(history_date) + " and " + str(current_date))
    mysql_rows = con.retrieve(select, table, where_query)

    result = []
    for mysql_row in mysql_rows:
        result.append(db_layout.MPFetched.object_from_mysql_row(dbcc, mysql_row))

    return result


'''
Checks the integrity of the data that is retrieved by retrieve_user_mobility_data_single_user.
Assumes data is supplied by maas in weeks. Therefore, entire days that are missing are checked in weeks.
Weeks are calculated from the unix_timestamp. Returns a list of all datetime ranges that are missing.
Code also still checks to see if certain time ranges within a date are missing, but this can be skipped
and absoleted probably.
'''
def check_user_mobility_data_single_user_integrity(grouped_by_date_grid_by_minute_of_day_mp_fetched, current_date):
    missing_ranges_date_time_date_time = []

    current_unix_days = support.date_to_unix_days_timestamp(current_date)
    history_unix_days = current_unix_days - config.MP_USE_DATA_FROM_LAST_DAYS
    current_unix_week = int(current_unix_days / common_config.DAYS_IN_A_WEEK)
    history_unix_week = int(history_unix_days / common_config.DAYS_IN_A_WEEK)


    #Find missing weeks
    all_weeks = map(lambda x: support.date_to_unix_weeks_timestamp(x), grouped_by_date_grid_by_minute_of_day_mp_fetched.keys())

    missing_ranges_unix_weeks = support.reduce_to_missing_ranges( all_weeks
                                                                , lambda i: i
                                                                , 1
                                                                , history_unix_week
                                                                , current_unix_week
                                                                )

    missing_ranges_date = map( lambda x: support.Range( support.unix_weeks_timestamp_to_date_range(x.min_range).min_range
                                                      , support.unix_weeks_timestamp_to_date_range(x.max_range).max_range
                                                      , support.Range.RESOLUTION_DATETIME_DAY
                                                      )
                             , missing_ranges_unix_weeks
                             )

    #Add the missing days
    begin_of_day_time = datetime.time(0, 0, 0)
    end_of_day_time = datetime.time(23, 59, 59)
    for missing_range_date in missing_ranges_date:
        start_date_time = datetime.datetime.combine(missing_range_date.min_range, begin_of_day_time)
        end_date_time = datetime.datetime.combine(missing_range_date.max_range, end_of_day_time)

        missing_ranges_date_time_date_time.append(support.Range(start_date_time, end_date_time, support.Range.RESOLUTION_DATETIME_MINUTE))

    #Calculate the missing time ranges in each day that already exists
    for date, grid_by_minute_of_day_mp_fetched in grouped_by_date_grid_by_minute_of_day_mp_fetched.items():
        missing_ranges_in_minutes = support.reduce_to_missing_ranges_already_grid( grid_by_minute_of_day_mp_fetched
                                                                                 , 1
                                                                                 , 0
                                                                                 , common_config.MINUTES_IN_A_DAY - 1
                                                                                 )

        missing_ranges_in_time = map( lambda missing_range: support.Range( support.calc_time_from_minute_of_day(missing_range.min_range)
                                                                         , support.calc_time_from_minute_of_day(missing_range.max_range)
                                                                         , support.Range.RESOLUTION_DATETIME_SECOND
                                                                         )
                                    , missing_ranges_in_minutes
                                    )

        #Add the missing times for a certain day
        for missing_range_in_time in missing_ranges_in_time:
            start_date_time = datetime.datetime.combine(date, missing_range_in_time.min_range)
            end_date_time = datetime.datetime.combine(date, missing_range_in_time.max_range)

            missing_ranges_date_time_date_time.append(support.Range(start_date_time, end_date_time, support.Range.RESOLUTION_DATETIME_MINUTE))

    return missing_ranges_date_time_date_time


'''
Prepares a pykov chain based on the supplied mp fetched data. Data should be given grouped by date and on each date the mp fetched should be gridded
by minute of the day. Checks also to see if the date is actually an applicable day or not(a day between current_day and predicted_day) but as
retrieve_user_mobility_data_single_user retrieves only the data for a certain day, this should not be necassary in a normal situation.
Returns the corresponding pykov chain.
'''
def prepare_pykov_chain_with_single_user_mobility_states(grouped_by_date_grid_by_minute_of_day_mp_fetched, current_day_str, predicted_day_str):
    list_of_day_str_applicable = support.difference_of_days(current_day_str, predicted_day_str)

    from_to_user_entry_dict = {}
    for date, grid_by_minute_of_day_mp_fetched in grouped_by_date_grid_by_minute_of_day_mp_fetched.items():
        if support.calc_day(date) in list_of_day_str_applicable:

            #It seems this day is a contender in the prediction.
            #For each minute of the day look at the cell id(source) and look at the next because that is the destination
            #Each pair of source and destination should be added to the from_to user_entry_dict (date doesn't matter anymore as link is formed)
            #Using the source as the key and adding the destination to the list

            i = 0
            for source_mp_fetched in grid_by_minute_of_day_mp_fetched:
                if i == common_config.MINUTES_IN_A_DAY - 1:
                    #We have reached the end of the day, must look at the next if possible in the next day

                    next_date = date + support.Range.RESOLUTION_DATETIME_DAY
                    if support.calc_day(next_date) in list_of_day_str_applicable:
                        #It seems the adjoining day is also a contender in the prediction. Configure the destination correctly
                        destination_mp_fetched = grouped_by_date_grid_by_minute_of_day_mp_fetched[next_date][0]
                    else:
                        #There is no connection to the next day
                        destination_mp_fetched = None
                else:
                    #In the middle of the day, destination is next in the grid
                    destination_mp_fetched = grid_by_minute_of_day_mp_fetched[i+1]

                if destination_mp_fetched:
                    source_user_entry = UserEntry(source_mp_fetched.day, source_mp_fetched.minute_of_day, source_mp_fetched.cell_id)
                    destination_user_entry = UserEntry(destination_mp_fetched.day, destination_mp_fetched.minute_of_day, destination_mp_fetched.cell_id)

                    #Add it to the from to user entry dict but with the source_user_entry as key
                    #Add it as a key if it doesn't exist yet
                    if source_user_entry in from_to_user_entry_dict:
                        from_to_user_entry_dict[source_user_entry].append(destination_user_entry)
                    else:
                        from_to_user_entry_dict[source_user_entry] = [destination_user_entry]

                i += 1

    #Calculate all percentages the same from and to user entry coincide
    pykov_chain_entries = {}
    for starting_user_entry, destinations in from_to_user_entry_dict.items():
        starting_key = starting_user_entry.to_pykov_key()
        total_amount = float(len(destinations))
        grouped_by_cell_id = support.group_by(destinations, lambda user_entry: user_entry.cell_id)

        for destination_cell_id, destinations_with_same_cell_id in grouped_by_cell_id.items():
            destination_key = destinations_with_same_cell_id[0].to_pykov_key()
            amount_of_destinations_with_same_cell_id = len(destinations_with_same_cell_id)
            percentage = float(amount_of_destinations_with_same_cell_id) / total_amount

            pykov_chain_entries[starting_key, destination_key] = percentage

    return pykov.Chain(pykov_chain_entries)

'''
Does a mobility prediction based on a pykov chain and the initial cell_id of the user. Checks n minutes
in advance where n is the difference in minutes between current_date_time and predicted_date_time
Returns a pykov probability distribution dict {'<destination': <probability>, ...}
'''
def mobility_prediction(pykov_chain, current_cell_id, current_date, current_time, predicted_date, predicted_time):
    initial_minute_of_day = support.calc_minute_of_day(current_time)
    initial_day = support.calc_day(current_date)

    initial_key = UserEntry(initial_day, initial_minute_of_day, current_cell_id).to_pykov_key()
    initial_pykov_vector = pykov.Vector({initial_key: 1})

    difference_in_seconds = (datetime.datetime.combine(predicted_date, predicted_time) - datetime.datetime.combine(current_date, current_time)).total_seconds()
    difference_in_minutes = int(difference_in_seconds / 60)

    distribution_dict = pykov_chain.pow(initial_pykov_vector, difference_in_minutes)
    print 'eeeeeee', distribution_dict

    return distribution_dict

'''
Converts a pykov distribution dict to the corresponding list of mobaas_protocol.data_objects.Predictions
'''
def from_pykov_distribution_dict_to_predictions(pykov_distribution_dict):
    predictions = []

    for pykov_key, probability in pykov_distribution_dict.items():
        user_entry = UserEntry.from_pykov_key(pykov_key)
        prediction = data_objects.Prediction(user_entry.cell_id, probability)

        predictions.append(prediction)

    return predictions

'''
Calculates the history datetime based on the current date and time
'''
def calculate_mp_history_datetime(current_date, current_time):
    current_date_time = datetime.datetime.combine(current_date, current_time)
    difference = datetime.timedelta(days=config.MP_USE_DATA_FROM_LAST_DAYS)

    return current_date_time - difference

'''
Calculates the history date based on the current date
'''
def calculate_mp_history_date(current_date):
    current_time = datetime.time(hour=0, minute=0, second=0, microsecond=0)

    return calculate_mp_history_datetime(current_date, current_time).date()
