import requests
from datetime import datetime
from time import mktime
from dateutil.relativedelta import relativedelta
import xmltodict


def _get_crumbs_and_cookies(ticker):
    """
    get crumb and cookies for historical data csv download from yahoo finance
    parameters: stock - short-handle identifier of the company
    returns a tuple of header, crumb and cookie
    """

    url = 'https://finance.yahoo.com/quote/{}/history'.format(ticker)
    with requests.session():
        header = {
            'Connection': 'keep-alive',
            'Expires': '-1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) \
                   AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
        }

        website = requests.get(url, headers=header)

        return (header, website.cookies)


def convert_to_unix(date):
    """
    converts date to unix timestamp

    parameters: date - in format (dd-mm-yyyy)

    returns integer unix timestamp
    """

    return int(mktime(date.timetuple()))


def load_csv_data(ticker, interval='1d', period1=(datetime.now()-relativedelta(years=1)), period2=datetime.now()):
    """
    queries yahoo finance api to receive historical data in csv file format

    parameters:
        stock - short-handle identifier of the company

        interval - 1d, 1wk, 1mo - daily, weekly monthly data

        day_begin - starting date for the historical data (format: dd-mm-yyyy)

        day_end - final date of the data (format: dd-mm-yyyy)

    returns a list of comma seperated value lines
    """

    header, cookies = _get_crumbs_and_cookies(ticker)
    period1 = convert_to_unix(period1)
    period2 = convert_to_unix(period2)

    with requests.session():
        url = 'https://query1.finance.yahoo.com/v7/finance/download/' \
              '{ticker}?period1={period1}&period2={period2}&interval={interval}' \
              .format(ticker=ticker, period1=period1, period2=period2, interval=interval)

        website = requests.get(url, headers=header, cookies=cookies)
        return website.text.split('\n')[1:]  # not include 0: Date,Open,High,Low,Close,AdjClose,Volume


def modifyNaver(object):
    date, open, high, low, close, volume = object['@data'].split('|')
    if volume == 0:
        return None
    else:
        date = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
        return [date, open, high, low, close]


def load_naver(ticker):
    url = 'https://fchart.stock.naver.com/sise.nhn'
    params = {'symbol': ticker, 'requestType': 0, 'count': 245, 'timeframe': 'day'}
    res = requests.get(url, params=params)
    ret = xmltodict.parse(res.text)['protocol']['chartdata']['item']
    ret = list(filter(None, list(map(modifyNaver, ret))))
    return ret


def modifyStock(string):
    date, open, high, low, close, _, volume = string.split(',')
    try:
        open = int(float(open))
    except ValueError:
        print(string)
        return

    high = int(float(high))
    low = int(float(low))
    close = int(float(close))
    # volume = int(float(volume))
    return [date, open, high, low, close]
    # return {'time': date, 'open': open, 'high': high, 'low': low, 'close': close, 'value': volume}


def nullCheck(string):
    data = string.split(',')
    if 'null' in data:
        return False
    elif float(data[-1]) == 0:
        return False
    else:
        return True
