import imp
import datetime
import collections
import os

from mobaas.common import config
from mobaas.common import error_logging as err

'''
Huge ass class of support functions
Should have been cut into multiple modules...oh well :P

Good luck!

Small overview of what to find here:
- The Range class
- Everything to calculate specialized functions of (date)(time)
  e.g. minute of the day, which day it is, unix_timestamp in days or weeks
- Group by (love this function)
- reduce_to_missing_ranges (Great one although a bit costly)

Most of the functions are self-descriptive or small enough to understand
Bigger ones have documentation
'''

'''
Determines the minute of that day ranging from 0 to 1439
    time - The time object of which to determine the minute of the day
Returns
    Int representing the minute of the day ranging from 0 to 1439
'''
def calc_minute_of_day(time):
    minutes = time.minute
    minutes_from_hours = time.hour * 60

    return minutes + minutes_from_hours

def calc_time_from_minute_of_day(minute_of_day):
    hours = int(minute_of_day / 60)
    minutes = minute_of_day % 60

    return datetime.time(hour=hours, minute=minutes, second=0)

'''
Determines the weekday using MOBaaS.config constants
    date - The date object of which to determine the weekday
Returns
    A string of config.MONDAY, config.TUESDAY, config.WEDNESDAY ...
'''
def calc_day(date):
    wd = date.isoweekday()

    if wd == 1:
        result = config.MONDAY
    elif wd == 2:
        result = config.TUESDAY
    elif wd == 3:
        result = config.WEDNESDAY
    elif wd == 4:
        result = config.THURSDAY
    elif wd == 5:
        result = config.FRIDAY
    elif wd == 6:
        result = config.SATURDAY
    elif wd == 7:
        result = config.SUNDAY
    else:
        result = False

    return result


def difference_of_days(day_1_str, day_2_str):
    days_of_the_week = [config.MONDAY, config.TUESDAY, config.WEDNESDAY, config.THURSDAY, config.FRIDAY, config.SATURDAY, config.SUNDAY] * 2
    i1 = days_of_the_week.index(day_1_str)
    i2 = days_of_the_week.index(day_2_str, i1)

    return days_of_the_week[i1:i2 + 1]


def func_to_day(day_str, func):
    i = config.DAYS_OF_THE_WEEK.index(day_str)
    j = func(i) % len(config.DAYS_OF_THE_WEEK)

    return config.DAYS_OF_THE_WEEK[j]


def next_day(day_str):
    return func_to_day(day_str, lambda i: i + 1)


def previous_day(day_str):
    return func_to_day(day_str, lambda i: i - 1)


def date_to_unix_weeks_timestamp(date):
    return int(date_to_unix_days_timestamp(date) / config.DAYS_IN_A_WEEK)


def unix_weeks_timestamp_to_date_range(unix_weeks):
    unix_days_start_of_week = 7 * unix_weeks
    unix_days_end_of_week = unix_days_start_of_week + config.DAYS_IN_A_WEEK - 1
    start_of_week = unix_days_timestamp_to_date(unix_days_start_of_week)
    end_of_week = unix_days_timestamp_to_date(unix_days_end_of_week)

    return Range(start_of_week, end_of_week, Range.RESOLUTION_DATETIME_DAY)


def date_to_unix_days_timestamp(date):
    time = datetime.time(0,0,0)
    date_time = datetime.datetime.combine(date, time)
    timedelta = date_time - config.UNIX_TIMESTAMP_BEGIN
    difference_seconds = timedelta.total_seconds()
    difference_days = int(difference_seconds / config.SECONDS_IN_A_DAY)

    return difference_days


def unix_days_timestamp_to_date(unix_day):
    date_time = datetime.timedelta(days=unix_day) + config.UNIX_TIMESTAMP_BEGIN

    return date_time.date()


def date_time_to_unix_minutes_timestamp(date_time):
    timedelta = date_time - config.UNIX_TIMESTAMP_BEGIN
    difference_seconds = timedelta.total_seconds()
    difference_minutes = int(difference_seconds / config.SECONDS_IN_A_MINUTE)

    return difference_minutes


def unix_minutes_timestamp_to_date_time(unix_minutes):
    timedelta = datetime.timedelta(seconds=unix_minutes * config.SECONDS_IN_A_MINUTE)
    date_time = timedelta + config.UNIX_TIMESTAMP_BEGIN

    return date_time


def is_installed(module_str):
    result = False
    try:
        imp.find_module(module_str)
        result = True
        err.log_error(err.INFO, "Found " + module_str + " correctly")
    except ImportError:
        err.log_error(err.INFO, "Could not find the " + module_str + " module. Is it installed?")

    return result


def everything_installed():
    return all(map(is_installed, config.REQUIRED_MODULES))


def remove_none_from_list(xs):
    i = len(xs) - 1

    while i >= 0:
        if xs[i] is None:
            del xs[i]
        i -= 1


def create_date_time(date_str, time_str):
    result = None
    try:
        result = datetime.datetime.strptime(date_str + " " + time_str, config.ISO_FORMAT_DATETIME)
    except ValueError:
        err.log_error(err.ERROR, "Received a date and/or time string that does not match iso 8601 format! Excepted [Time: %H-%M-%S, Date: %Y-%m-%d] Found [Time: " + time_str + " Date: " + date_str + "]")

    return result


def create_date(date_str):
    result = None
    try:
        result = datetime.datetime.strptime(date_str, config.ISO_FORMAT_DATE).date()
    except ValueError:
        err.log_error(err.ERROR, "Received a date string that does not match iso 8601 format! Excepted [Date: %Y-%m-%d] Found [Date: " + date_str + "]")

    return result


def create_time(time_str):
    result = None
    try:
        result = datetime.datetime.strptime(time_str, config.ISO_FORMAT_TIME).time()
    except ValueError:
        err.log_error(err.ERROR, "Received a time string that does not match iso 8601 format! Excepted [Time: %H-%M-%S] Found [Time: " + time_str + "]")

    return result


def create_date_str(date):
    return date.strftime(config.ISO_FORMAT_DATE)


def create_time_str(time):
    return time.strftime(config.ISO_FORMAT_TIME)


def time_total_seconds(time):
    return time.hour * config.SECONDS_IN_A_HOUR + time.minute * config.SECONDS_IN_A_MINUTE + time.second


def from_unix_timestamp_ms_to_datetime(unix_timestamp_ms):
    total_seconds = int(unix_timestamp_ms / 1000)
    ms = unix_timestamp_ms % 1000
    datetime_obj = config.UNIX_TIMESTAMP_BEGIN + datetime.timedelta(seconds=total_seconds)
    datetime_obj = datetime_obj.replace(microsecond=(ms * 1000))
    return datetime_obj


def from_unix_timestamp_to_datetime(unix_timestamp):
    return from_unix_timestamp_ms_to_datetime(unix_timestamp * 1000)


def to_unix_timestamp_ms_from_date_and_time(date, time):
    td = datetime.datetime.combine(date, time) - config.UNIX_TIMESTAMP_BEGIN
    unix_timestamp = int(td.total_seconds())
    ms = int(td.microseconds / 1000)
    unix_timestamp_ms = unix_timestamp * 1000 + ms
    return unix_timestamp_ms


def to_unix_timestamp_from_date_and_time(date, time):
    return int(to_unix_timestamp_ms_from_date_and_time(date, time) / 1000)


'''
Function to create a grid between the starting value and end value with a certain
resolution. It is actually a list with as many spaces as the resolution fits
 between the start and end value. Places ONE item of the list of items that fit a spot
 and returns that list
'''
def to_grid(items, resolution, func_item_to_value, start_value, end_value):
    total_places = int((end_value - start_value) / resolution) + 1
    places = [None] * total_places


    for item in items:
        value = func_item_to_value(item)
        if value <= end_value:
            place = int((value - start_value) / resolution)
            if not places[place]:
                places[place] = item

    return places


def find_all_in_list(items, to_find):
    result = []

    i = 0
    while i < len(items):
        if items[i] == to_find:
            result.append(i)
        i += 1

    return result


'''
Groups a list of user info by value in an ordereddict with sublists
All are unsorted
Respects order
'''
def group_by(items, func_item_to_value):
    result = collections.OrderedDict()

    for item in items:
        value = func_item_to_value(item)
        if value in result:
            sublist = result.get(value)
            sublist.append(item)
        else:
            sublist = [item]

        result[value] = sublist

    return result

'''
Takes a list of items and reduced it to ranges by first calling the to_grid function
and returning the result of reduce_to_missing_ranges_already_grid
'''
def reduce_to_missing_ranges(items, func_item_to_value, resolution, start_value, end_value):
    grid = to_grid(items, resolution, func_item_to_value, start_value, end_value)
    return reduce_to_missing_ranges_already_grid(grid, resolution, start_value, end_value)

'''
Takes a grid (returned by to_grid) and checks which ranges are missing in the grid
Returns a list of Range objects with the correct ranges that are missing
(So if [1,2,3,5,6,7] reduced to [Range(1,1,1), Range(4,4,1)] with res 1 starting 0 and end 7)
'''
def reduce_to_missing_ranges_already_grid(grid, resolution, start_value, end_value):
    result = []
    begin_of_missing_range = None

    i = 0
    while i < len(grid):
        item = grid[i]

        if begin_of_missing_range is None:
            if item is None:
                begin_of_missing_range = i * resolution + start_value
            else:
                #In a range
                pass
        else:
            if item is None:
                #In missing range
                pass
            else:
                last_of_missing_range = (i - 1) * resolution + start_value + (resolution - 1)
                result.append(Range(begin_of_missing_range, last_of_missing_range, resolution))
                begin_of_missing_range = None
        i += 1

    #Check if list didn't end with a missing range
    if not(begin_of_missing_range is None):
        #last missing range hasn't ended, so add end_value (this also makes sure we don't
        #go above the end_value for a missing range)
        result.append(Range(begin_of_missing_range, end_value, resolution))

    return result


def directory_to_list_of_filepaths(directory_path):
    try:
        all = os.listdir(directory_path)
    except OSError:
        result = []
    else:
        all_abs = map(lambda f: os.path.join(directory_path, f), all)
        result = [f for f in all_abs if os.path.isfile(f)]

    return result

'''
Class to express a range between things
A real pain in the ass to program the correct overlapping cases
Pretty much self explanatory
'''
class Range():
    RESOLUTION_DATETIME_SECOND = datetime.timedelta(seconds=1)
    RESOLUTION_DATETIME_MINUTE = datetime.timedelta(seconds=60)
    RESOLUTION_DATETIME_DAY = datetime.timedelta(days=1)

    def __init__(self, min_range, max_range, resolution):
        self.min_range = min_range
        self.max_range = max_range
        self.resolution = resolution

    def __add__(self, other):
        if self.has_overlap(other):
            min_range = min(self.min_range, other.min_range)
            max_range = max(self.max_range, other.max_range)
            result = [Range(min_range, max_range, self.resolution)]
        else:
            result = [self, other]

        return result

    def __sub__(self, other):
        if self.other_completely_overlaps(other):
            #Completely overshadowed by other
            result = []
        elif self.other_falls_in(other):
            #Split up by other
            result = [ Range(self.min_range, other.min_range - self.resolution, self.resolution)
                     , Range(other.max_range + self.resolution, self.max_range, self.resolution)
                     ]
        elif self.other_overlaps_left_border(other):
            #Subtracts partially on the left
            result = [Range(other.max_range + self.resolution, self.max_range, self.resolution)]
        elif self.other_overlaps_right_border(other):
            #Subtracts partially on the right
            result = [Range(self.min_range, other.min_range - self.resolution, self.resolution)]
        else:
            #Do not overlap whatsoever
            result = [self]

        return result

    def __str__(self):
        return "|Range (" + str(self.min_range) + ", " + str(self.max_range) + ", res: " + str(self.resolution) + ")|"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.other_same_range(other) and self.resolution == other.resolution

    def __ne__(self, other):
        return not (self == other)

    def has_overlap(self, other):
        return (  self.other_falls_in(other)
               or self.other_completely_overlaps(other)
               or self.other_overlaps_left_border(other)
               or self.other_overlaps_right_border(other)
               )

    def other_same_range(self, other):
        return other.min_range == self.min_range and other.max_range == self.max_range

    def other_falls_in(self, other):
        return other.min_range > self.min_range and other.max_range < self.max_range

    def other_completely_overlaps(self, other):
        return other.min_range <= self.min_range and other.max_range >= self.max_range

    def other_overlaps_left_border(self, other):
        return other.min_range <= self.min_range <= other.max_range < self.max_range

    def other_overlaps_right_border(self, other):
        return self.min_range < other.min_range <= self.max_range <= other.max_range

    def get_progression(self):
        return range(self.min_range, self.max_range + self.resolution, self.resolution)

    @staticmethod
    def get_progressions(ranges):
        result = []

        for range in ranges:
            result.extend(range.get_progression())

        return result