from mobaas.tests import run_tests

from mobaas.common import support

from mobaas.frontend_support import missing_resources as mr
from mobaas.frontend_support import supplied_resources as sr
from mobaas.frontend_support import pending_requests

def test_pending_request():
    missing_resource_1 = mr.MissingLinkCapacity(1)
    supplied_resource_1 = sr.SuppliedLinkCapacity(1)

    missing_resource_2 = mr.MissingFlowData([support.Range(1, 3, 1)])
    supplied_resource_2_1 = sr.SuppliedFlowData(support.Range(3, 5, 1))
    supplied_resource_2_2 = sr.SuppliedFlowData(support.Range(1, 3, 1))

    pending_request = pending_requests.PendingRequest( None
                                                     , "req_msg"
                                                     , [ missing_resource_1
                                                       , missing_resource_2
                                                       ]
                                                     )

    #Not empty
    run_tests.compare_answer(pending_request.ready_to_be_handled(), False, "Check if request not be handled after filled")
    run_tests.compare_answer(len(pending_request.missing_resources.items()), 2, "Check to see if both are added")

    #Supply 1
    pending_request.process_supplied_resource(supplied_resource_1)

    run_tests.compare_answer(pending_request.ready_to_be_handled(), False, "Check if request not be handled after first supply")
    run_tests.compare_answer(len(pending_request.missing_resources.items()), 1, "Check to see if one still exists")

    #Supply 2_1
    pending_request.process_supplied_resource(supplied_resource_2_1)
    run_tests.compare_answer(pending_request.ready_to_be_handled(), False, "Check if request not be handled after second supply")
    run_tests.compare_answer(len(pending_request.missing_resources.items()), 1, "Check to see if one still exists")

    #Supply 2_2
    pending_request.process_supplied_resource(supplied_resource_2_2)
    run_tests.compare_answer(pending_request.ready_to_be_handled(), True, "Check if request be handled after third supply")
    run_tests.compare_answer(len(pending_request.missing_resources.items()), 0, "Check to see if none still exist")


def test_pending_request_queue():
    missing_resource_1 = mr.MissingLinkCapacity(1)
    supplied_resource_1 = sr.SuppliedLinkCapacity(1)

    missing_resource_2 = mr.MissingFlowData([support.Range(1, 3, 1)])
    supplied_resource_2_1 = sr.SuppliedFlowData(support.Range(3, 5, 1))
    supplied_resource_2_2 = sr.SuppliedFlowData(support.Range(1, 3, 1))

    pending_request_queue = pending_requests.PendingRequestQueue()
    pending_request_queue.add_pending_request(None, "req_msg1", [missing_resource_1, missing_resource_2])
    pending_request_queue.add_pending_request(None, "req_msg2", [missing_resource_1])

    #Not empty
    run_tests.compare_answer(pending_request_queue.get_ready_to_be_handled_requests()
                            , []
                            , "Check to see if no requests initially are ready"
                            )
    run_tests.compare_answer(len(pending_request_queue.pending_requests)
                            , 2
                            , "Check to see if both requests are still there initially"
                            )

    #Supply 1
    pending_request_queue.process_supplied_resource(supplied_resource_1)
    requests = pending_request_queue.get_ready_to_be_handled_requests()
    run_tests.compare_answer(len(requests)
                            , 1
                            , "Check to see one request is ready after first supply"
                            )
    run_tests.compare_answer( requests[0].request_message
                            , "req_msg2"
                            , "Check to see if correct message is ready req1"
                            )
    run_tests.compare_answer(len(pending_request_queue.pending_requests)
                            , 1
                            , "Check to see if last request is still there after first supply"
                            )

    #Supply 2_1
    pending_request_queue.process_supplied_resource(supplied_resource_2_1)
    requests = pending_request_queue.get_ready_to_be_handled_requests()
    run_tests.compare_answer( len(requests)
                            , 0
                            , "Check to see if zero requests are ready after second supply"
                            )
    run_tests.compare_answer(len(pending_request_queue.pending_requests)
                            , 1
                            , "Check to see if last request is still there after second supply"
                            )

    #Supply 2_2
    pending_request_queue.process_supplied_resource(supplied_resource_2_2)
    requests = pending_request_queue.get_ready_to_be_handled_requests()
    run_tests.compare_answer(len(requests)
                            , 1
                            , "Check to see one request is ready after third supply"
                            )
    run_tests.compare_answer( requests[0].request_message
                            , "req_msg1"
                            , "Check to see if correct message is ready req2"
                            )
    run_tests.compare_answer(len(pending_request_queue.pending_requests)
                            , 0
                            , "Check to see if no request is still there after third supply"
                            )