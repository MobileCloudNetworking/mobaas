from mobaas.tests import run_tests

from mobaas.common import support

from mobaas.frontend_support import missing_resources as mr
from mobaas.frontend_support import supplied_resources as sr

ORDER = [
        ]


def test_missing_flow_data():
    missing_ranges = [support.Range(1,5,1), support.Range(8,10,1)]
    missing_resource = mr.MissingFlowData(missing_ranges)

    supplied_range1 = support.Range(3,5,1)
    supplied_range2 = support.Range(6,9,1)
    supplied_resource1 = sr.SuppliedFlowData(supplied_range1)
    supplied_resource2 = sr.SuppliedFlowData(supplied_range2)

    #Not empty
    run_tests.compare_answer(missing_resource.is_not_missing_anything(), False, "Test empty after filled")

    #Applied first
    missing_resource.update_missing_from_supplied_info(supplied_resource1)
    now_missing_ranges1 = missing_resource.missing

    run_tests.compare_answer(now_missing_ranges1, [support.Range(1,2,1), support.Range(8,10,1)], "Test missing after first supplied")

    #Applied second
    missing_resource.update_missing_from_supplied_info(supplied_resource2)
    now_missing_ranges2 = missing_resource.missing
    run_tests.compare_answer(now_missing_ranges2, [support.Range(1,2,1), support.Range(10,10,1)], "Test missing after second supplied")

    #Dismiss all and test empty
    supplied_range_dismiss = support.Range(1,10,1)
    supplied_resource_dismiss = sr.SuppliedFlowData(supplied_range_dismiss)
    missing_resource.update_missing_from_supplied_info(supplied_resource_dismiss)

    now_missing_ranges_dismiss = missing_resource.missing

    run_tests.compare_answer(now_missing_ranges_dismiss, [], "Test if missing list is now empty")
    run_tests.compare_answer(missing_resource.is_not_missing_anything(), True, "Test to see if missing resource is not missing anything")


def test_missing_link_capacity():
    missing_link_id = 2
    missing_resource = mr.MissingLinkCapacity(missing_link_id)

    supplied_link_id1 = 1
    supplied_link_id2 = 2
    supplied_resource1 = sr.SuppliedLinkCapacity(supplied_link_id1)
    supplied_resource2 = sr.SuppliedLinkCapacity(supplied_link_id2)

    #Not empty
    run_tests.compare_answer(missing_resource.is_not_missing_anything(), False, "Test empty after filled")

    #Applied first
    missing_resource.update_missing_from_supplied_info(supplied_resource1)
    run_tests.compare_answer(missing_resource.is_not_missing_anything(), False, "Test after first supplied")
    run_tests.compare_answer(missing_resource.missing, missing_link_id, "Test to see if missing stayed the same")

    #Applied second
    missing_resource.update_missing_from_supplied_info(supplied_resource2)
    run_tests.compare_answer(missing_resource.is_not_missing_anything(), True, "Test to see if empty after link id is supplied")


