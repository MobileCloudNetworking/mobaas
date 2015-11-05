import urllib
import urllib.request
from urllib.request import urlopen


def func():
    url_ip = 'http://130.92.70.160/5000'
    ip = None
    try:
        ip = urlopen(url_ip)
    except:
        pass
    return ip


if __name__ == '__main__':
    print(func())
