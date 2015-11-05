import numpy

from mobaas.common import support
from mobaas.algorithms import config
from mobaas.database_connections import db_layout

'''
Calculate the prediction based on a list of BPFetched data
'''
def bandwidth_prediction(bpfetched):
    list_time_throughput_bps = map(db_layout.BPFetched.to_tuple_without_link_id, bpfetched)
    list_time, list_throughput_bps = zip(*list_time_throughput_bps)
    xs = list_time
    ys = list_throughput_bps

    return numpy.mean(ys) + (1/config.BP_TIME_SCALE) * numpy.sqrt(-2*numpy.log10(config.BP_EPS)) * numpy.sqrt(numpy.var(ys)*config.BP_TIME_SCALE)


'''
Retrieve the link capacity data for a certain link_id in a list
'''
def retrieve_link_capacity_data(dbcc, link_id):

    conditions = [ ("link_id", "+", link_id)
                 ]

    list_link_capacity_data = db_layout.LinkCapacityData.retrieve_objects(dbcc, conditions)
    return list_link_capacity_data

'''
Retrieve the BP fetch data in a list for a certain link_id.
Uses the date and end_time to determine how far back we should use data
from. algorithms.config.BP_USE_DATA_FROM_LAST_SECONDS determines this history range
'''
def retrieve_bandwidth_prediction_data(dbcc, link_id, date, end_time):
    end_time_unix = support.to_unix_timestamp_from_date_and_time(date, end_time)
    start_time_unix = end_time_unix - config.BP_USE_DATA_FROM_LAST_SECONDS

    conditions = [ ("link_id", "=", link_id)
                 , ("time", ">=", start_time_unix)
                 , ("time", "<=", end_time_unix)
                 ]

    bp_fetched = db_layout.BPFetched.retrieve_objects(dbcc, conditions)
    return bp_fetched

time_resolution = 1 # in seconds

'''
Checks from a list of bpfetched data if any holes exist within the data
Uses the date and end_time to determine how far back we should use data
from. algorithms.config.BP_USE_DATA_FROM_LAST_SECONDS determines this history range
Returns a list of support.Range with unix timestamps in seconds of missing ranges (if any)
'''
def check_integrity_bandwidth_prediction_data(bpfetched, date, end_time):
    end_time_unix = support.to_unix_timestamp_from_date_and_time(date, end_time)
    start_time_unix = end_time_unix - config.BP_USE_DATA_FROM_LAST_SECONDS

    list_time_throughput_bps = map(db_layout.BPFetched.to_tuple_without_link_id, bpfetched)

    missing_ranges = support.reduce_to_missing_ranges( list_time_throughput_bps
                                                     , lambda (time, throughput): time
                                                     , 1
                                                     , start_time_unix
                                                     , end_time_unix
                                                     )

    return missing_ranges