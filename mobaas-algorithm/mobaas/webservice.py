#!flask/bin/python
from flask import Flask, jsonify, abort, make_response, request, url_for
import datetime
import calendar
import thread
import timeit
import requests

from threading import Timer # for the MP answer loop

'''from mobaas.algorithms import mobility_prediction as mp'''
from mobaas.algorithms import multi_user_prediction as mup

'''from mobaas.database_connections import db_connections
from mobaas.database_connections import db_layout

from mobaas.common import support'''

app = Flask(__name__)

'''@app.route('/mobaas/api/v1.0/prediction/single-user', methods=['POST'])
def su_prediction():
    if not request.json or not 'user_id' in request.json \
        or not 'future_time_delta' in request.json \
        or not 'reply_url' in request.json \
        or not 'current_cell_id' in request.json :
        abort(400)

    if 'current_time' in request.json and 'current_date' in request.json:
        req = (request.json['user_id'], request.json['current_time'],
                request.json['current_date'], request.json['future_time_delta'],
                request.json['current_cell_id'], request.json['reply_url']);
    else:
        req = (request.json['user_id'], datetime.datetime.now().strftime('%H:%M:%S'),
                datetime.datetime.now().strftime('%Y-%m-%d'), request.json['future_time_delta'],
                request.json['current_cell_id'], request.json['reply_url']);

    # handle the prediction request
    handle_incoming_mp_single_user_request(req)

    return jsonify({'su_request': su_request_to_dict(req)}), 201
'''
@app.route('/mobaas/api/v1.0/prediction/multi-user', methods=['POST'])
def mu_prediction():
    if not request.json or not 'user_id' in request.json \
        or not 'future_time_delta' in request.json \
        or not 'reply_url' in request.json :
        abort(400)

    if 'current_time' in request.json and 'current_date' in request.json:
        req = (request.json['user_id'], request.json['current_time'], 
                request.json['current_date'], request.json['future_time_delta'], 
                request.json['reply_url']);
    else:
        req = (request.json['user_id'], datetime.datetime.now().strftime('%H:%M'), 
                calendar.day_name[datetime.date.today().weekday()], 
                request.json['future_time_delta'], request.json['reply_url']);

    # create thread, thread will handle the multi_user prediction request
    thread.start_new_thread(handle_incoming_mp_multi_user_request, (req,))

    return jsonify({'mu_request': mu_request_to_dict(req)}), 201

'''def handle_incoming_mp_single_user_request(request):
    predicted_date_time = datetime.datetime.combine(datetime.datetime.strptime(request[2],'%Y-%m-%d'), datetime.datetime.strptime(request[1],'%H:%M:%S').time()) + datetime.timedelta(seconds=int(request[3]))
    predicted_date = predicted_date_time.date()
    predicted_time = predicted_date_time.time()

    dbcc = db_connections.DBConnectionCollection("MOBaaS Databases")
    dbcc.create_multiple_connections(db_layout.DATABASE_NAMES)
    db_connections.DBConnectionCollection.start_all_connections(dbcc)
    
    #if user_id is 0000 (i.e. 0, because it is an integer), we need to use multi-user prediction, not single user prediction
    if int(request[0]) != 0:
        mp_fetched = mp.retrieve_user_mobility_data_single_user(dbcc, int(request[0]), datetime.datetime.strptime(request[2],'%Y-%m-%d'), predicted_date)
        grouped_by_date_mp_fetched = support.group_by(mp_fetched, lambda x: x.date)

        grouped_by_date_grid_by_minute_of_day_mp_fetched = {}
        for date, mp_fetched_list in grouped_by_date_mp_fetched.items():
            minute_of_day_grid = support.to_grid( mp_fetched_list
                                                , 1
                                                , lambda x: x.minute_of_day
                                                , 0
                                                , common_config.MINUTES_IN_A_DAY - 1
                                                )
            grouped_by_date_grid_by_minute_of_day_mp_fetched[date] = minute_of_day_grid

        missing_ranges = mp.check_user_mobility_data_single_user_integrity( grouped_by_date_grid_by_minute_of_day_mp_fetched
                                                                          , datetime.datetime.strptime(request[2],'%Y-%m-%d')
                                                                          )

        if len(missing_ranges) > 0:
            return
            #Missing user information data, queue request and ask data from supplier
            # missing_resource = mr.MissingUserInfo(missing_ranges)
            # frontend.queue_as_pending_request(connection, msg, [missing_resource])

            # err.log_error(err.INFO, "Did not have enough user info data. Asking supplier for: " + str(missing_ranges))

            # error_message = mo.Error(102, "MP Request will take longer than expected because user data is missing at MOBaaS")
            # connection.add_message(error_message)

            # for missing_range in missing_ranges:
            #     start_time = missing_range.min_range.time()
            #     start_date = missing_range.min_range.date()
            #     time_span = int((missing_range.max_range - missing_range.min_range).total_seconds())

            #     supplier_message = mo.MaaSSingleUserDataRequest(msg.user_id, start_time, start_date, time_span, 60)
            #     frontend.ask_at_supplier(supplier_message)
        else:
            #There is all the info we need, calculate the spots
            current_day_str = support.calc_day(datetime.datetime.strptime(request[2],'%Y-%m-%d'))
            predicted_day_str = support.calc_day(predicted_date)

            pykov_chain = mp.prepare_pykov_chain_with_single_user_mobility_states(grouped_by_date_grid_by_minute_of_day_mp_fetched
                                                                                 , current_day_str
                                                                                 , predicted_day_str
                                                                                 )
            chance_distribution_dict = mp.mobility_prediction(pykov_chain, int(request[4]), datetime.datetime.strptime(request[2],'%Y-%m-%d'), datetime.datetime.strptime(request[1],'%H:%M:%S').time(), predicted_date, predicted_time)

            #Create mobaas_protocol.prediction objects from the answers
            mobaas_protocol_predictions = mp.from_pykov_distribution_dict_to_predictions(chance_distribution_dict)

            #Send answer
            send_su_message(request[5], request[0], predicted_time, predicted_date, mobaas_protocol_predictions)
    else:
        print 'error: should not get here!'
'''
def handle_incoming_mp_multi_user_request(request, iteration=1):

    # For demo purpose, only send back one prediction result by commenting the timer for the next prediction
    # Timer(int(request[3])*60, handle_incoming_mp_multi_user_request, [request, iteration+1]).start()

    #err.log_error(err.INFO, "Using MP multi-user algorithm, iteration %d" % iteration)
    start_time = timeit.default_timer()

    current_time_in_min = sum(int(x) * 60 ** i for i,x in enumerate(reversed(request[1].split(':'))))
    next_time_in_min = current_time_in_min + (iteration * int(request[3]))
    next_time_formatted = '{:02d}:{:02d}'.format(*divmod(next_time_in_min, 60))

    if next_time_in_min > 1440 - int(request[3]):
        return;

    result = mup.mp(int(request[0]), next_time_formatted, request[2], int(request[3]))

    mu_predictions = []

    for k in result.keys():
        (user_id, current_cell_id, next_time) = k
        probabilities = result[k]
        predictions = []
        for p in probabilities:
            (cell_id, probability) = p
            predictions.append([cell_id, probability])
        mu_prediction = [user_id, current_cell_id, next_time, predictions]
        mu_predictions.append(mu_prediction)

    # Send answer
    send_mu_message(request[4], mu_predictions)

    #err.log_error(err.INFO, "Execution time for this run (iteration %d) is : %d , Second" % (iteration, timeit.default_timer() - start_time))
    #Timer(int(request[3])*60, handle_incoming_mp_multi_user_request, [request, iteration+1]).start()

'''def su_request_to_dict(request):
    out = {
        'user_id' : request[0], 
        'current_time' : request[1],
        'current_date' : request[2],
        'future_time_delta' : request[3],
        'current_cell_id' : request[4],
        'reply_url' : request[5]
    }
    return out
'''
def mu_request_to_dict(request):
    out = {
        'user_id' : request[0], 
        'current_time' : request[1],
        'current_date' : request[2],
        'future_time_delta' : request[3],
        'reply_url' : request[4]
    }
    return out

'''def send_su_message(reply_url, user_id, predicted_time, predicted_date, mobaas_protocol_predictions):
    #values = dict(data=json.dumps({"jsonkey2": "jsonvalue2", "jsonkey2": "jsonvalue2"}))
    print mobaas_protocol_predictions

    data = urllib.urlencode(values)
    req = urllib2.Request(reply_url, data)
    rsp = urllib2.urlopen(req)
    content = rsp.read()
    return content
'''
def send_mu_message(reply_url, mu_predictions):
    parsed_predictions = [
    {
        'user_id' : user_id, 
        'current_cell_id' : current_cell_id,
        'next_time' : next_time,
        'predictions' : [{
            'cell_id' : cell_id,
            'probability' : probability
        } for cell_id, probability in pred]
    } for user_id, current_cell_id, next_time, pred in mu_predictions
    ]

    r = requests.post(reply_url, json={'multiple_user_predictions': [prediction for prediction in parsed_predictions]})
    return r.status_code

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
