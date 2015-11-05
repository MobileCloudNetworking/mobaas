import importlib
import inspect
import traceback
import os
import glob

from mobaas.common import support
from mobaas.common import error_logging as err
from mobaas.tests import config

FILE_ERRORS = 0


def end_file_message(current_file, file_errors):
    err.log_error_test(err.INFO, "[Test][File] Ended tests in file " + current_file + " with " + str(file_errors) + " errors")


def compare_answer(result, should_be, test_str):

    r = True
    if not result == should_be:
        err.log_error_test(err.CRITICAL, "[Test][Fault] {" + test_str + "} Expected: " + str(should_be) + " but found: " + str(result) + " in test " + config.CURRENT_TEST)
        r = False
        config.TEST_ERRORS += 1

    return r


def run_test(name_func, func):
    global FILE_ERRORS
    config.CURRENT_TEST = name_func
    try:
        func()
    except Exception as e:
        err.log_error_test(err.CRITICAL, "[Test][Fault] {" + config.CURRENT_TEST + "} caused an exception: " + e.message)
        config.TEST_ERRORS += 1
        print traceback.format_exc()

    err.log_error_test(err.INFO, "[Test] {" + config.CURRENT_TEST + "} has completed with " + str(config.TEST_ERRORS) + " errors")
    FILE_ERRORS += config.TEST_ERRORS
    config.TEST_ERRORS = 0


def find_all_test_scripts():
    module_path_strings = glob.glob(os.path.dirname(__file__)+"/test_*.py")
    base_names = map(os.path.basename, module_path_strings)
    roots_exts = map(os.path.splitext, base_names)
    module_names = map(lambda (root, ext): root, roots_exts)
    module_names.sort()

    return module_names


def run_tests():
    global FILE_ERRORS
    total_errors = 0

    for test_file in find_all_test_scripts():
        module = importlib.import_module(test_file, "mobaas.tests")

        names_funcs = inspect.getmembers(module, inspect.isfunction)

        if "ORDER" in dict(inspect.getmembers(module)):
            order = module.ORDER
            names_funcs_dict = dict(names_funcs)

            for func_name in order:
                if func_name in names_funcs_dict:
                    run_test(func_name, names_funcs_dict[func_name])
                    del names_funcs_dict[func_name]

            names_funcs = names_funcs_dict.items()

        for name_func, func in names_funcs:
            if name_func.startswith("test_"):
                run_test(name_func, func)

        end_file_message(test_file, FILE_ERRORS)
        total_errors += FILE_ERRORS
        FILE_ERRORS = 0

    err.log_error_test(err.INFO, "[Test][Total] Ended testing with in total " + str(total_errors) + " errors")


if __name__ == "__main__":
    if support.everything_installed():
        err.TEST_MODUS = True
        run_tests()
