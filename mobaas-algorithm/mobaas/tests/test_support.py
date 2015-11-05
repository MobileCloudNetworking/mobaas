import datetime
import collections

from mobaas.common import support
from mobaas.common import config

from mobaas.tests import run_tests


def test_calc_minute_of_day():
    time1 = datetime.time(hour=0, minute=1, second=1)
    time2 = datetime.time(hour=1, minute=0, second=1)
    time3 = datetime.time(hour=0, minute=0, second=0)
    time4 = datetime.time(hour=23, minute=59, second=59)

    value1 = support.calc_minute_of_day(time1)
    value2 = support.calc_minute_of_day(time2)
    value3 = support.calc_minute_of_day(time3)
    value4 = support.calc_minute_of_day(time4)

    run_tests.compare_answer(value1, 1, "minute of day = 1")
    run_tests.compare_answer(value2, 60, "minute of day = 2")
    run_tests.compare_answer(value3, 0, "minute of day = 3")
    run_tests.compare_answer(value4, 1439, "minute of day = 4")


def test_calc_day():
    monday = support.calc_day(datetime.date(year=2014, month=06, day=30))
    tuesday = support.calc_day(datetime.date(year=2014, month=07, day=01))
    wednesday = support.calc_day(datetime.date(year=2014, month=07, day=02))
    thursday = support.calc_day(datetime.date(year=2015, month=01, day=15))
    friday = support.calc_day(datetime.date(year=2015, month=01, day=16))
    saturday = support.calc_day(datetime.date(year=2015, month=01, day=17))
    sunday = support.calc_day(datetime.date(year=2015, month=01, day=18))

    run_tests.compare_answer(monday, config.MONDAY, "monday")
    run_tests.compare_answer(tuesday, config.TUESDAY, "tuesday")
    run_tests.compare_answer(wednesday, config.WEDNESDAY, "wednesday")
    run_tests.compare_answer(thursday, config.THURSDAY, "thursday")
    run_tests.compare_answer(friday, config.FRIDAY, "friday")
    run_tests.compare_answer(saturday, config.SATURDAY, "saturday")
    run_tests.compare_answer(sunday, config.SUNDAY, "sunday")


def test_remove_none_from_list():
    l1 = [None, 1, 2, None, 3]
    support.remove_none_from_list(l1)
    run_tests.compare_answer(l1, [1,2,3], "")


def test_create_date_time():
    time_str = "14:30:31"
    date_str = "2014-10-17"

    dt = support.create_date_time(date_str, time_str)

    run_tests.compare_answer(dt.second, 31,"second")
    run_tests.compare_answer(dt.minute, 30,"minute")
    run_tests.compare_answer(dt.hour, 14,"hour")
    run_tests.compare_answer(dt.day, 17,"day")
    run_tests.compare_answer(dt.month, 10,"month")
    run_tests.compare_answer(dt.year, 2014,"year")


def test_create_date_str():
    d = datetime.date(year=2014, month=10, day=17)
    run_tests.compare_answer(support.create_date_str(d), "2014-10-17", "")


def test_create_time_str():
    t = datetime.time(hour=12, minute=30, second=31)
    run_tests.compare_answer(support.create_time_str(t), "12:30:31", "")


def test_time_total_seconds():
    t1 = datetime.time(hour=0, minute=0, second=0)
    t2 = datetime.time(hour=10, minute=10, second=10)

    run_tests.compare_answer(support.time_total_seconds(t1), 0, "total seconds 0")
    run_tests.compare_answer(support.time_total_seconds(t2), 36610, "total seconds 36610")


def test_from_unix_timestamp_to_datetime():
    unix_ts = 687702610010
    dt = support.from_unix_timestamp_ms_to_datetime(unix_ts)

    run_tests.compare_answer(dt.microsecond, 10000, "microsecond")
    run_tests.compare_answer(dt.second, 10,"second")
    run_tests.compare_answer(dt.minute, 30,"minute")
    run_tests.compare_answer(dt.hour, 12,"hour")
    run_tests.compare_answer(dt.day, 17,"day")
    run_tests.compare_answer(dt.month, 10,"month")
    run_tests.compare_answer(dt.year, 1991,"year")

def test_to_unix_timestamp_ms_from_date_and_time():
    t = datetime.time(hour=12, minute=30, second=10, microsecond=6000)
    d = datetime.date(year=1991, month=10, day=17)

    unix_ms = support.to_unix_timestamp_ms_from_date_and_time(d, t)

    run_tests.compare_answer(unix_ms, 687702610006, "")


def test_to_unix_timestamp_from_date_and_time():
    t = datetime.time(hour=12, minute=30, second=10, microsecond=6000)
    d = datetime.date(year=1991, month=10, day=17)

    unix_ms = support.to_unix_timestamp_from_date_and_time(d, t)

    run_tests.compare_answer(unix_ms, 687702610, "")


def test_to_grid():
    l1 = [1, 2, 3, 3, 4, 5, 5]
    grid1 = support.to_grid(l1, 1, lambda x: x, 1, 5)
    run_tests.compare_answer(grid1, [1,2,3,4,5], "grid1")

    l2 = [100, 130, 100, 100, 150, 130, 100]
    grid2 = support.to_grid(l2, 10, lambda x: x, 100, 150)
    run_tests.compare_answer(grid2, [100, None, None, 130, None, 150], "grid2")


def test_find_all_in_list():
    l1 = [1, 5, 2, 3, None, 5]
    indices1 = support.find_all_in_list(l1, 5)
    run_tests.compare_answer(indices1, [1, 5], "indices1")

    l2 = [None, 123, "asd", None, datetime.datetime(year=1991, month=10, day=10)]
    indices2 = support.find_all_in_list(l2, None)
    run_tests.compare_answer(indices2, [0, 3], "indices2")


def test_group_by():
    l1 = [1, 2, 3, 4, 5] * 2
    answer1 = collections.OrderedDict({1: [1] * 2, 2: [2] * 2, 3: [3] * 2, 4: [4] * 2, 5: [5] * 2})
    run_tests.compare_answer(support.group_by(l1, lambda x:x), answer1, "group_by 1")


def test_reduce_to_missing_ranges():
    l1 = [1, 2, 10, 40, 41, 50]
    answer1 = [support.Range(3, 9, 1), support.Range(11, 39, 1), support.Range(42, 49, 1)]
    result1 = support.reduce_to_missing_ranges(l1, lambda x: x, 1, 1, 50)
    run_tests.compare_answer(result1, answer1, "missing_support.Ranges 1")

    #Difficult one because one value is outside of the (start value, end value) support.Range while the resolution allows it
    l2 = [9, 11]
    answer2 = [support.Range(1, 6, 3), support.Range(10, 10, 3)]
    result2 = support.reduce_to_missing_ranges(l2, lambda x: x, 3, 1, 10)
    run_tests.compare_answer(result2, answer2, "missing_ranges 2")


def test_ranges_add():
    run_tests.compare_answer(support.Range(1,2,1) + support.Range(2,3,1), [support.Range(1,3,1)], "Testing ranges add (1,2) and (2,3)")
    run_tests.compare_answer(support.Range(1,2,1) + support.Range(3,4,1), [support.Range(1,2,1), support.Range(3,4,1)], "Testing ranges add (1,2) and (3,4)")
    run_tests.compare_answer(support.Range(2,3,1) + support.Range(1,2,1), [support.Range(1,3,1)], "Testing ranges add (2,3) and (1,2)")
    run_tests.compare_answer(support.Range(1,2,1) + support.Range(1,2,1), [support.Range(1,2,1)], "Testing ranges add (1,2) and (1,2)")


def test_ranges_sub():
    #Same ranges
    run_tests.compare_answer(support.Range(1,3,1) - support.Range(1,3,1), [], "Test ranges sub (1,3) - (1,3)")
    
    #Right border overlap
    run_tests.compare_answer(support.Range(1,3,1) - support.Range(2,4,1), [support.Range(1,1,1)], "Test ranges sub (1,3) - (2,4)")
    run_tests.compare_answer(support.Range(1,2,1) - support.Range(2,4,1), [support.Range(1,1,1)], "Test ranges sub (1,2) - (2,4)")
    
    #Left border overlap
    run_tests.compare_answer(support.Range(3,5,1) - support.Range(1,4,1), [support.Range(5,5,1)], "Test ranges sub (3,5) - (1,4)")
    run_tests.compare_answer(support.Range(3,5,1) - support.Range(1,3,1), [support.Range(4,5,1)], "Test ranges sub (3,5) - (1,3)")
    
    #Complete overlap
    run_tests.compare_answer(support.Range(3,5,1) - support.Range(2,6,1), [], "Test ranges sub (3,5) - (2,6)")
    run_tests.compare_answer(support.Range(3,5,1) - support.Range(3,5,1), [], "Test ranges sub (3,5) - (3,5)")
    
    #Falls in
    run_tests.compare_answer(support.Range(2,6,1) - support.Range(3,4,1), [support.Range(2,2,1), support.Range(5,6,1)], "Test ranges sub (2,6) - (3,4)")

    #Falls in but on a border so actually a border overlap
    run_tests.compare_answer(support.Range(2,6,1) - support.Range(4,6,1), [support.Range(2,3,1)], "Test ranges sub (2,6) - (4,6)")
    run_tests.compare_answer(support.Range(2,6,1) - support.Range(2,3,1), [support.Range(4,6,1)], "Test ranges sub (2,6) - (2,3)")
    

def test_ranges_has_overlap():
    #Same ranges
    run_tests.compare_answer(support.Range(1,3,1).has_overlap(support.Range(1,3,1)), True, "Test ranges has overlap (1,3) and (1,3)")
    
    #Right border overlap
    run_tests.compare_answer(support.Range(1,3,1).has_overlap(support.Range(2,4,1)), True, "Test ranges has overlap (1,3) and (2,4)")
    run_tests.compare_answer(support.Range(1,2,1).has_overlap(support.Range(2,4,1)), True, "Test ranges has overlap (1,2) and (2,4)")
    
    #Left border overlap
    run_tests.compare_answer(support.Range(3,5,1).has_overlap(support.Range(1,4,1)), True, "Test ranges has overlap (3,5) and (1,4)")
    run_tests.compare_answer(support.Range(3,5,1).has_overlap(support.Range(1,3,1)), True, "Test ranges has overlap (3,5) and (1,3)")
    
    #Complete overlap
    run_tests.compare_answer(support.Range(3,5,1).has_overlap(support.Range(2,6,1)), True, "Test ranges has overlap (3,5) and (2,6)")
    run_tests.compare_answer(support.Range(3,5,1).has_overlap(support.Range(3,5,1)), True, "Test ranges has overlap (3,5) and (3,5)")
    
    #Falls in
    run_tests.compare_answer(support.Range(2,6,1).has_overlap(support.Range(3,4,1)), True, "Test ranges has overlap (2,6) and (3,4)")
    
    #No overlap
    run_tests.compare_answer(support.Range(1,3,1).has_overlap(support.Range(4,6,1)), False, "Test ranges has overlap (1,3) and (4,6)")
    run_tests.compare_answer(support.Range(4,6,1).has_overlap(support.Range(1,3,1)), False, "Test ranges has overlap (4,6) and (1,3)")
    

def test_ranges_other_same_range():
    #Same range
    run_tests.compare_answer(support.Range(1,3,1).other_same_range(support.Range(1,3,1)), True, "Test ranges other same range (1,3) and (1,3)")
    
    #Right border overlap
    run_tests.compare_answer(support.Range(1,3,1).other_same_range(support.Range(2,4,1)), False, "Test ranges other same range (1,3) and (2,4)")
    
    #Left border overlap
    run_tests.compare_answer(support.Range(3,5,1).other_same_range(support.Range(1,4,1)), False, "Test ranges other same range (3,5) and (1,4)")
    
    #No overlap
    run_tests.compare_answer(support.Range(1,3,1).other_same_range(support.Range(4,6,1)), False, "Test ranges other same range (1,3) and (4,6)")
    
    #Falls in
    run_tests.compare_answer(support.Range(2,6,1).other_same_range(support.Range(3,4,1)), False, "Test ranges other same range (2,6) and (3,4)")
    
    #Complete overlap
    run_tests.compare_answer(support.Range(3,4,1).other_same_range(support.Range(2,6,1)), False, "Test ranges other same range (2,6) and (3,4)")


def test_ranges_other_completely_overlaps():
    #Same range
    run_tests.compare_answer(support.Range(1,3,1).other_completely_overlaps(support.Range(1,3,1)), True, "Test ranges other completely overlaps (1,3) and (1,3)")
    
    #Right border overlap
    run_tests.compare_answer(support.Range(1,3,1).other_completely_overlaps(support.Range(2,4,1)), False, "Test ranges other completely overlaps (1,3) and (2,4)")
    
    #Left border overlap
    run_tests.compare_answer(support.Range(3,5,1).other_completely_overlaps(support.Range(1,4,1)), False, "Test ranges other completely overlaps (3,5) and (1,4)")
    
    #No overlap
    run_tests.compare_answer(support.Range(1,3,1).other_completely_overlaps(support.Range(4,6,1)), False, "Test ranges other completely overlaps (1,3) and (4,6)")
    
    #completely overlaps
    run_tests.compare_answer(support.Range(2,6,1).other_completely_overlaps(support.Range(3,4,1)), False, "Test ranges other completely overlaps (2,6) and (3,4)")
    
    #Complete overlap
    run_tests.compare_answer(support.Range(3,4,1).other_completely_overlaps(support.Range(2,6,1)), True, "Test ranges other completely overlaps (2,6) and (3,4)")


def test_ranges_other_falls_in():
    #Same range
    run_tests.compare_answer(support.Range(1,3,1).other_falls_in(support.Range(1,3,1)), False, "Test ranges other falls in (1,3) and (1,3)")
    
    #Right border overlap
    run_tests.compare_answer(support.Range(1,3,1).other_falls_in(support.Range(2,4,1)), False, "Test ranges other falls in (1,3) and (2,4)")
    
    #Left border overlap
    run_tests.compare_answer(support.Range(3,5,1).other_falls_in(support.Range(1,4,1)), False, "Test ranges other falls in (3,5) and (1,4)")
    
    #No overlap
    run_tests.compare_answer(support.Range(1,3,1).other_falls_in(support.Range(4,6,1)), False, "Test ranges other falls in (1,3) and (4,6)")
    
    #Falls in
    run_tests.compare_answer(support.Range(2,6,1).other_falls_in(support.Range(3,4,1)), True, "Test ranges other falls in (2,6) and (3,4)")
    
    #Complete overlap
    run_tests.compare_answer(support.Range(3,4,1).other_falls_in(support.Range(2,6,1)), False, "Test ranges other falls in (2,6) and (3,4)")
    

def test_ranges_other_overlaps_left_border():
    #Same range
    run_tests.compare_answer(support.Range(1,3,1).other_overlaps_left_border(support.Range(1,3,1)), False, "Test ranges other overlaps left border (1,3) and (1,3)")
    
    #Right border overlap
    run_tests.compare_answer(support.Range(1,3,1).other_overlaps_left_border(support.Range(2,4,1)), False, "Test ranges other overlaps left border (1,3) and (2,4)")
    
    #Left border overlap
    run_tests.compare_answer(support.Range(3,5,1).other_overlaps_left_border(support.Range(1,4,1)), True, "Test ranges other overlaps left border (3,5) and (1,4)")
    
    #No overlap
    run_tests.compare_answer(support.Range(1,3,1).other_overlaps_left_border(support.Range(4,6,1)), False, "Test ranges other overlaps left border (1,3) and (4,6)")
    
    #Falls in
    run_tests.compare_answer(support.Range(2,6,1).other_overlaps_left_border(support.Range(3,4,1)), False, "Test ranges other overlaps left border (2,6) and (3,4)")
    
    #Complete overlap
    run_tests.compare_answer(support.Range(3,4,1).other_overlaps_left_border(support.Range(2,6,1)), False, "Test ranges other overlaps left border (2,6) and (3,4)")


def test_ranges_other_overlaps_right_border():
    #Same range
    run_tests.compare_answer(support.Range(1,3,1).other_overlaps_right_border(support.Range(1,3,1)), False, "Test ranges other overlaps right border (1,3) and (1,3)")
    
    #Right border overlap
    run_tests.compare_answer(support.Range(1,3,1).other_overlaps_right_border(support.Range(2,4,1)), True, "Test ranges other overlaps right border (1,3) and (2,4)")
    
    #Left border overlap
    run_tests.compare_answer(support.Range(3,5,1).other_overlaps_right_border(support.Range(1,4,1)), False, "Test ranges other overlaps right border (3,5) and (1,4)")
    
    #No overlap
    run_tests.compare_answer(support.Range(1,3,1).other_overlaps_right_border(support.Range(4,6,1)), False, "Test ranges other overlaps right border (1,3) and (4,6)")
    
    #Falls in
    run_tests.compare_answer(support.Range(2,6,1).other_overlaps_right_border(support.Range(3,4,1)), False, "Test ranges other overlaps right border (2,6) and (3,4)")
    
    #Complete overlap
    run_tests.compare_answer(support.Range(3,4,1).other_overlaps_right_border(support.Range(2,6,1)), False, "Test ranges other overlaps right border (2,6) and (3,4)")

