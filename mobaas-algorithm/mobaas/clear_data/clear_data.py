import flows_ts
import datetime

from mobaas.frontend_support import supplied_resources as sr

from mobaas.database_connections import db_layout

from mobaas.common import support
from mobaas.common import error_logging as err

'''
This module takes data in the MaaS format and converts it to
a format usable for the Mobility Prediction and Bandwidth Prediction algorithm.
'''

'''
Clears a user_information_maas_message (mobaas_protocol.message_objects.MaaSSingleUserDataAnswer) by
putting it into the mean database, calculating the corresponding mp_fetched objects and putting the mp_fetched
objects into the mp_fetch database. Assumes MaaS supplies all data it has between the start_date_time and the timespan
in the message and fills in all the missing minute_of_day on each data with cell id 0
'''
def clear_user_information_maas_message(dbcc, msg):
    user_id = msg.user_id
    db_user_mobility_information_list = []

    #Save it in mean database and convert to db layout object
    for movement in msg.user_information:
        db_user_mobility_information = db_layout.UserMobilityInformation.new(dbcc, user_id, movement.time, movement.date, movement.cell_id)
        db_user_mobility_information_list.append(db_user_mobility_information)

    db_layout.UserMobilityInformation.save_many(dbcc, db_user_mobility_information_list)

    mp_fetched_list = []
    #Clear the data and save it in the fetched database
    for db_user_mobility_information in db_user_mobility_information_list:
        minute_of_day = support.calc_minute_of_day(db_user_mobility_information.time)
        day = support.calc_day(db_user_mobility_information.date)

        mp_fetched = db_layout.MPFetched.new( dbcc
                                            , user_id
                                            , minute_of_day
                                            , db_user_mobility_information.date
                                            , day
                                            , db_user_mobility_information.cell_id
                                            )
        mp_fetched_list.append(mp_fetched)

    #Fill in gaps
    end_date_time = datetime.datetime.combine(msg.start_date, msg.start_time) + datetime.timedelta(seconds=msg.time_span)

    gaps_mp_fetched = find_the_gaps_user_info_to_mp_fetched( dbcc
                                                           , msg.user_id
                                                           , msg.start_date
                                                           , msg.start_time
                                                           , end_date_time.date()
                                                           , end_date_time.time()
                                                           , db_user_mobility_information_list
                                                           )

    mp_fetched_list.extend(gaps_mp_fetched)
    db_layout.MPFetched.save_many(dbcc, mp_fetched_list)

    err.log_error(err.INFO, "Cleared " + str(len(msg.user_information)) + " rows user information data")
    err.log_error(err.INFO, "Filled in " + str(len(gaps_mp_fetched)) + " holes with mp fetched data")

    return sr.SuppliedUserInfo.from_maas_user_info_message_to_supplied_info(msg)


'''
Finds all missing mp_fetched objects in a certain date and time range and a list of user_info objects
Used to create complete blocks of data in clear_user_information_maas_message
'''
def find_the_gaps_user_info_to_mp_fetched(dbcc, user_id, start_date, start_time, end_date, end_time, user_info_list):
    start_unix_minutes = support.date_time_to_unix_minutes_timestamp(datetime.datetime.combine(start_date, start_time))
    end_unix_minutes = support.date_time_to_unix_minutes_timestamp(datetime.datetime.combine(end_date, end_time))

    missing_ranges_unix_minutes = support.reduce_to_missing_ranges( user_info_list
                                                                  , lambda x: support.date_time_to_unix_minutes_timestamp(datetime.datetime.combine(x.date, x.time))
                                                                  , 1
                                                                  , start_unix_minutes
                                                                  , end_unix_minutes
                                                                  )

    mp_fetched = []

    for missing_range_unix_minutes in missing_ranges_unix_minutes:
        progression = missing_range_unix_minutes.get_progression()

        for missing_unix_minute in progression:
            date_time = support.unix_minutes_timestamp_to_date_time(missing_unix_minute)
            time = date_time.time()
            date = date_time.date()
            minute_of_day = support.calc_minute_of_day(time)
            day = support.calc_day(date)
            cell_id = 0

            new_mp_fetched = db_layout.MPFetched.new( dbcc
                                                    , user_id
                                                    , minute_of_day
                                                    , date
                                                    , day
                                                    , cell_id
                                                    )

            mp_fetched.append(new_mp_fetched)

    return mp_fetched


'''
Clears a single message of flow data from MaaS by saving all the data into the mean database
and by pushing all the rows of flow data through the flows_ts module. The answers of this
last part are put into the BP_fetched database table
'''
def clear_single_link_maas_message(dbcc, msg):
    link_id = msg.link_id
    db_flow_data_list = []
    #Save it in mean database and convert to db layout object

    for flow_data in msg.flow_data:
        db_flow_data = db_layout.FlowData.new(dbcc
                                              , link_id
                                              , flow_data.start_time
                                              , flow_data.stop_time
                                              , flow_data.source_ip
                                              , flow_data.destination_ip
                                              , flow_data.num_of_packets
                                              , flow_data.num_of_bytes
                                             )
        db_flow_data_list.append(db_flow_data)
    db_layout.FlowData.save_many(dbcc, db_flow_data_list)

    #Process flowdata
    flows_ts_data = map(db_layout.FlowData.to_tuple_without_link_id, db_flow_data_list)
    flows_ts_output_list = flows_ts.process_flow_data(flows_ts_data)

    #Save it in fetched database
    bp_fetched_objects = []
    for unix_timestamp_time, throughput_bps in flows_ts_output_list:
        bp_fetched_objects.append(db_layout.BPFetched.new(dbcc, link_id, unix_timestamp_time, throughput_bps))

    db_layout.BPFetched.save_many(dbcc, bp_fetched_objects)

    err.log_error(err.INFO, "Cleared " + str(len(msg.flow_data)) + " rows of flow data")

    return sr.SuppliedFlowData.from_bp_fetched_list_to_supplied_info(bp_fetched_objects)


'''
Clears a single link capacity message of MaaS by putting the capacity in link capacity table
msg should be of type mobaas_protocol.message_objects.MaaSSingleLinkCapacityAnswer
'''
def clear_single_link_capacity_message(dbcc, msg):
    link_capacity_data = db_layout.LinkCapacityData.new(dbcc, msg.link_id, msg.capacity)
    link_capacity_data.save()

    err.log_error(err.INFO, "Cleared link capacity information for link " + str(link_capacity_data.link_id))

    return sr.SuppliedLinkCapacity.from_link_capacity_data_to_supplied_info(link_capacity_data)
