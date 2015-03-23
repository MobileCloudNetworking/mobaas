import requests
from retrying import retry

from mcn.sm import CONFIG
from mcn.sm import LOG


WAIT = CONFIG.get('cloud_controller', 'wait_time', 2000)
ATTEMPTS = CONFIG.get('cloud_controller', 'max_attempts', 5)


def retry_if_http_error(exception):
    """
    Defines which type of exceptions allow for a retry of the request

    :param exception: the raised exception
    :return: True if retrying the request is possible
    """
    error = False
    if isinstance(exception, requests.HTTPError):
        if exception.response.status_code == 503:
            LOG.info('Requesting retry: response code: ' + str(exception.response.status_code))
            LOG.error('Exception: ' + exception.__repr__())
            error = True
    elif isinstance(exception, requests.ConnectionError):
        LOG.info('Requesting retry: ConnectionError')
        LOG.error('Exception: ' + exception.__repr__())
        error = True
    return error


@retry(retry_on_exception=retry_if_http_error, wait_fixed=WAIT, stop_max_attempt_number=ATTEMPTS)
def http_retriable_request(verb, url, headers={}, authenticate=False, params={}):
    """
    Sends an HTTP request, with automatic retrying in case of HTTP Errors 500 or ConnectionErrors
    _http_retriable_request('POST', 'http://cc.cloudcomplab.ch:8888/app/', headers={'Content-Type': 'text/occi', [...]}
                            , authenticate=True)
    :param verb: [POST|PUT|GET|DELETE] HTTP keyword
    :param url: The URL to use.
    :param headers: Headers of the request
    :param kwargs: May contain authenticate=True parameter, which is used to make requests requiring authentication,
                    e.g. CC requests
    :return: result of the request
    """
    LOG.debug(verb + ' on ' + url + ' with headers ' + headers.__repr__())

    auth = ()
    if authenticate:
        user = CONFIG.get('cloud_controller', 'user')
        pwd = CONFIG.get('cloud_controller', 'pwd')
        auth = (user, pwd)

    if verb in ['POST', 'DELETE', 'GET', 'PUT']:
        try:
            r = None
            if verb == 'POST':
                if authenticate:
                    r = requests.post(url, headers=headers, auth=auth, params=params)
                else:
                    r = requests.post(url, headers=headers, params=params)
            elif verb == 'DELETE':
                if authenticate:
                    r = requests.delete(url, headers=headers, auth=auth, params=params)
                else:
                    r = requests.delete(url, headers=headers, params=params)
            elif verb == 'GET':
                if authenticate:
                    r = requests.get(url, headers=headers, auth=auth, params=params)
                else:
                    r = requests.get(url, headers=headers, params=params)
            elif verb == 'PUT':
                if authenticate:
                    r = requests.put(url, headers=headers, auth=auth, params=params)
                else:
                    r = requests.put(url, headers=headers, params=params)
            r.raise_for_status()
            return r
        except requests.HTTPError as err:
            LOG.error('HTTP Error: should do something more here!' + err.message)
            raise err