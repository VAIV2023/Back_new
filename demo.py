# import os
# import sys
import shutil
from os import path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from predict_newDemo import discover
from backtesting import backtest
import find_sell as yd
from stockdata import load_naver, load_csv_data, modifyStock, nullCheck
# from temp import find_sell_date
# from pykrx import stock
# import FinanceDataReader as fdr
import pandas as pd
# import numpy as np
import multiprocessing as mp
import torch
import time
import requests
import exchange_calendars as xcals
from datetime import datetime, timedelta
import json
import random
from pymongo import MongoClient
app = Flask(__name__)

trade_date = ''
yolo_detect = {'Kospi': {}, 'Kosdaq': {}}
stockInfo = pd.read_csv('/home/ubuntu/2022_VAIV_Dataset/flask/static/Stock.csv', index_col=0)


def current_close_by_ticker(ticker):
    currentClose = None
    try:
        s = requests.Session()
        url = "https://finance.naver.com/item/main.nhn?code=" + ticker[1:]
        resp = s.get(url)
        currentClose = resp.text.split("<dd>현재가 ")[1].split(' ')[0].replace(",","")
    except:
        currentClose = 0
    return currentClose


def date_from_buy(buy_date):
    # 오늘날짜
    today = datetime.today().strftime("%Y-%m-%d")

    # 개장일 불러오기
    XKRX = xcals.get_calendar("XKRX")  # 개장일 가져오기
    pred_dates = XKRX.sessions_in_range(buy_date, today)
    open_dates = pred_dates.strftime("%Y%m%d").tolist()

    return open_dates


def yolo_buy(tickerlist, s_date, market):
    global trade_date
    global yolo_detect
    label = {'buy': 1.0, 'sell': 0.0, 'hold': 0.0, 'FileNotFoundError': 0.0}
    market = market.lower().capitalize()
    XKRX = xcals.get_calendar("XKRX")
    t_date = XKRX.next_session(s_date).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    start = time.time()
    # if trade_date != t_date:
    #     yolo_detect.update({'Kospi': {}, 'Kosdaq': {}})
    #     trade_date = t_date
    #     try:
    #         shutil.rmtree('/home/ubuntu/2022_VAIV_Dataset/flask/static/predict')
    #     except FileNotFoundError:
    #         pass
    # if not yolo_detect.get(market):
    #     # detect = yd.detect_list(tickerlist, trade_date, market=market)
    #     detect = yd.detect_first(tickerlist, today, market=market)
    #     yolo_detect[market] = detect
    detect = yd.detect_first(tickerlist, t_date, market=market)
    # else:
    #     detect = yolo_detect.get(market)
    print(f'{len(tickerlist)} ticker Time: {time.time() - start}s')
    detectlist = [['Yolo', label[detect[ticker][0]], round(100 * detect[ticker][1], 1)] for ticker in tickerlist]
    # print(detectlist)
    return detectlist, detect


#  HTML 화면 보여주기
@app.route('/')
def homework():
    return render_template('tragedy.html')


# simulate.html
@app.route('/simulate')
def simulate():
    return render_template('simulate.html')
# CORS 해결하는 방법??


@app.route('/login')
def login():
    return render_template('login.html')


# login API
@app.route('/isvalid', methods=['POST'])
def isValid():
    result = {}
    success = -1
    data = None

    id = request.form.get('id')
    password = request.form.get('password')

    # 로그인 성공 1) id가 db에 존재하지 않거나 (이 경우 새로 추가)
    # 2) id가 db에 존재하면서 pw가 맞을 경우
    client = MongoClient("mongodb://localhost:27017/")

    db = client.user_asset

    # prevent duplicate id
    # if user_id is not exist, return -1
    # if user_password is incorrect, return 0
    # if success, return 1
    for d in db['asset'].find():
        if d['id'] == id:
            if d['password'] == password:
                # data = d   # TypeError: Object of type ObjectId is not JSON serializable
                success = 1
            else:
                success = 0
            break

    if success == -1:
        print("\nAdd new account\n")
        data = {
            'id': id,
            'password' : password,
            'total buy' : 0,
            'real gain' : 0,
            'asset_list' : [],
            'sell_list' : []
        }
        # insert user data
        dpInsert = db.asset.insert_one(data)

    # print("\n\n user_data")
    # print(data)
    # print("\n\n")
    result['success'] = success
    # result['user_data'] = data

    return result


# Update asset 1 : add stock : 매수버튼 클릭
@app.route('/updateasset1', methods=['POST'])
def update_asset_1():
    result = {}
    data = request.form.to_dict()
    print(f"\n\ndata : {data}\n\n")
    user_id = data['user_id']
    ticker = data['ticker']
    name = data['name']
    buy_date = data['buy_date']
    buy_close = data['buy_close']
    buy_count = data['buy_count']
    buy_total = data['buy_total']
    market = data['market']

    stock_info = {
        "market" : market,
        "ticker" : ticker,   #fixed
        "name" : name,   #fixed
        "buy date" : buy_date,   #fixed
        "buy count" : int(buy_count),   #fixed
        "buy close" : int(buy_close),   #fixed
        "buy total" : int(buy_total),   #fixed
    }

    client = MongoClient("mongodb://localhost:27017/")
    db = client.user_asset

    for d in db['asset'].find():
        try:
            if d['id'] == user_id:
                # modify 'asset_list'
                asset_list = d['asset_list']
                print(f"\nbefore add : {asset_list}\n")
                asset_list.append(stock_info)
                print(f"\nafter add : {asset_list}\n")
                db.asset.update_one(
                    {"id":user_id},
                    {
                        "$set": {
                            "asset_list" : asset_list
                        }
                    }
                )

                # modify 'total buy'
                total_buy = d['total buy']  # 총 매입

                total_buy += int(buy_total)

                print(f"\ntotal buy : {total_buy}")

                db.asset.update_one(
                    {"id":user_id},
                    {
                        "$set": {
                            "total buy" : total_buy,
                        }
                    }
                )
                break
        except Exception as e:
            print(e)

    return result




# Update asset 2 : My Asset Tab 클릭 -> 총 자산 정보, 현재가 정보를 포함한 asset list 보여줌
@app.route('/updateasset2', methods=['POST'])
def update_asset_2():
    result = {}
    new_asset_list = []
    total_list = []
    total_gain = 0  # 총 손익
    total_profit = 0    # 총 수익률
    total_buy = 0   # 총 매입
    total_current = 0   # 총 평가
    real_gain = 0

    user_id = request.form.get('user_id')
    client = MongoClient("mongodb://localhost:27017/")
    db = client.user_asset

    print(f"\nuser id : {user_id}\n")

    # yolo detection 추가 (시작)
    global yolo_detect
    tickerlist = {'Kospi': [], 'Kosdaq': []}  # ticker 전체
    today = datetime.today()
    yesterday = today - timedelta(1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    print('Yesterday: ', yesterday)
    XKRX = xcals.get_calendar("XKRX")
    print(XKRX.sessions_in_range('2022-11-22', '2022-11-24'))
    trade_date = XKRX.next_session(yesterday).strftime('%Y-%m-%d')
    print('trade_date: ', trade_date)
    # yolo detection 추가 (끝)

    print("\nyolo detection has finished\n")

    for d in db['asset'].find():
        try:
            if d['id'] == user_id:
                # asset_list의 정보 업데이트
                asset_list = d['asset_list']
                print(asset_list)
                real_gain = d['real gain']
                print(f"\nbefore changed : real gain = {real_gain}\n")
                sell_list = d['sell_list']
                #sell_list = []
                for stock in asset_list:
                    ticker = stock['ticker'][1:]
                    ticker_full = stock['ticker']

                    market = stock['market'].lower().capitalize()
                    tickerlist[market].append(ticker)  # yolo detection 추가

                    dir_path = '/home/ubuntu/2022_VAIV_SeoHwan/make_graph/2022_stcok_data'
                    if stock['market'] == 'KOSDAQ':
                        dir_path = '/home/ubuntu/2022_VAIV_SeoHwan/make_graph/2022_kosdaq_data'
                    file_path = f"{dir_path}/{ticker_full}.csv"
                    stock_df = pd.read_csv(file_path, index_col=0)
                    stock_df.reset_index(inplace=True, drop=True)

                    # 현재가 가져오기
                    current_close = float(current_close_by_ticker(ticker_full))
                    stock['current close'] = current_close

                    # 평가손익, 수익률, 평가금액 계산
                    stock['difference'] = int(( current_close * 0.9975 - stock['buy close'] ) * stock['buy count'])
                    stock['profit'] = round(( current_close * 0.9975 - stock['buy close'] ) / stock['buy close'] * 100, 1)
                    stock['current total'] = int(( current_close) * stock['buy count'])

                    # 1day~5day 업데이트
                    # 오늘과 buy_date의 gap 계산
                    dayprofit = []
                    open_dates = date_from_buy(stock['buy date'])

                    print(f"open dates : {open_dates}")

                    # open_dates 수가 7개 이상이면 -> 총 자산 정보 변경하고(real gain, ), sell_list에 추가, asset_list에서 제외 (continue)
                    if len(open_dates) > 6:
                        print(f"open_dates[5] : {open_dates[5]}")
                        row = stock_df.loc[stock_df['Date'] == int(open_dates[5])]
                        close = float(row.values[0][2])
                        real_gain += int(( close * 0.9975 - stock['buy close'] ) * stock['buy count'])
                        stock['sell close'] = close
                        stock['sell_date'] = open_dates[5]
                        sell_list.append(stock)
                        continue


                    total_buy += int(stock['buy total'])
                    total_current += int(stock['current total'])


                    for i in range(len(open_dates) - 1):
                        # if dayprofit[i][0] == 1:
                        #     continue
                        try:    # 종가가 저장된 파일에서 불러와지면 fixed
                            row = stock_df.loc[stock_df['Date'] == int(open_dates[i+1])]
                            index = int(row.values[0][0])
                            close = float(row.values[0][2])
                            sub = []
                            sub.append(1)
                            sub.append(close)
                            sub.append(round(( close * 0.9975 - float(stock['buy close']) ) / float(stock['buy close']) * 100 , 1))
                            dayprofit.append(sub)
                        except Exception as e2:
                            #print(f"\nIt is current close : {open_dates[i+1]}")
                            sub = []
                            sub.append(0)
                            sub.append(current_close)
                            sub.append(round(( float(current_close) * 0.9975 - float(stock['buy close'] )) / float(stock['buy close']) * 100, 1))
                            dayprofit.append(sub)

                    # day1이면 len=2 -> 나머지 4개도 append해야됨, day2이면 len=3, ... , day5이면 len=6
                    for i in range(6 - len(open_dates)):
                        sub = []
                        sub.append(-1)
                        sub.append(0)
                        sub.append(0)
                        dayprofit.append(sub)

                    stock['dayprofit'] = dayprofit

                    new_asset_list.append(stock)

                print(f"\nafter changed : real gain = {real_gain}\n")
                # DB의 asset_list 업데이트
                db.asset.update_one(
                    {"id":user_id},
                    {
                        "$set": {
                        "asset_list" : new_asset_list,
                        "sell_list" : sell_list
                        }
                    }
                )

                # total info 업데이트
                total_gain = total_current - total_buy  # 총 손익
                total_profit = round((float(total_current) * 0.9975 - float(total_buy))/ float(total_buy) * 100, 2)    # 총 수익률

                # DB의 total info 업데이트
                db.asset.update_one(
                    {"id":user_id},
                    {
                        "$set": {
                            "total buy" : total_buy,
                            "real gain" : real_gain
                        }
                    }
                )

                break

        except Exception as e:
            print(e)

    detection = dict()
    print('ticker list: ', tickerlist)
    # detection.update(yd.detect_list(tickerlist['Kospi'], trade_date, market='Kospi'))
    # detection.update(yd.detect_list(tickerlist['Kosdaq'], trade_date, market='Kosdaq'))
    today = datetime.now().strftime('%Y-%m-%d')
    if tickerlist['Kospi']:
        kospi = yd.detect_first(list(set(tickerlist['Kospi'])), today, market='Kospi')
        # print(kospi)  # ticker: signal, prob, price, start, end
        detection.update(kospi)
    if tickerlist['Kosdaq']:
        detection.update(yd.detect_first(list(set(tickerlist['Kosdaq'])), today, market='Kosdaq'))
    detect_asset = dict()
    print('Detection: ', detection)
    for ticker, v in detection.items():
        detect = {
            ticker: [stockInfo.FullCode.loc[ticker], stockInfo.Symbol.loc[ticker], v[0], v[1], v[3], v[4]]
        }
        detect_asset.update(detect)
    result['detect'] = detect_asset
    print(f'Detect Result: {detect_asset}')

    total_list.append(total_gain)
    total_list.append(total_buy)
    total_list.append(real_gain)
    total_list.append(total_current)
    total_list.append(total_profit)

    print(f"return value in update2 : {new_asset_list}")
    result['asset_list'] = new_asset_list
    result['total_list'] = total_list
    print('------------------------------------------------------------------')
    return result

# Update asset 3 : 매도 API
@app.route('/updateasset3', methods=['POST'])
def update_asset_3():
    result = {}
    data = request.form.to_dict()
    print(f"\n\ndata : {data}\n\n")
    user_id = data['user_id']
    ticker = data['ticker']
    buy_date = data['buy_date']
    sell_count = data['sell_count']

    remove_buy = 0

    client = MongoClient("mongodb://localhost:27017/")
    db = client.user_asset

    for d in db['asset'].find():
        try:
            if d['id'] == user_id:
                # modify 'asset_list'
                asset_list = d['asset_list']
                sell_list = d['sell_list']
                print(f"\nbefore remove : {asset_list}\n")

                for i in range(len(asset_list)):
                    asset = asset_list[i]
                    if asset['ticker'] == ticker and asset['buy date'] == buy_date:
                        if asset['buy count'] == sell_count:
                            remove_buy = asset['buy total']
                            stock = asset_list[i]
                            stock['sell date'] = datetime.today().strftime("%Y%m%d")
                            sell_list.append(stock)
                            del asset_list[i]
                        elif asset['buy count'] < sell_count:
                            asset_list[i]['buy count'] -= sell_count
                            asset_list[i]['buy total'] -= (sell_count * asset_list[i]['buy close'])
                            remove_buy = (sell_count * asset_list[i]['buy close'])
                            stock = asset_list[i]
                            stock['sell date'] = datetime.today().strftime("%Y%m%d")
                            stock['sell close'] = current_close_by_ticker(ticker_full)
                            stock['sell count'] = sell_count
                            sell_list.append(stock)
                        else:
                            return result
                        break

                print(f"\nafter remove : {asset_list}\n")
                db.asset.update_one(
                    {"id":user_id},
                    {
                        "$set": {
                            "asset_list" : asset_list,
                            "sell list" : sell_list
                        }
                    }
                )

                # modify 'total buy'
                total_buy = d['total buy']  # 총 매입

                total_buy -= int(remove_buy)

                print(f"\ntotal buy : {total_buy}")

                # modify 'real gain'
                real_gain = d['real gain']  # 실현 손익
                real_gain += int((float(current_close_by_ticker(ticker_full)) * float(sell_count) * 0.9975 - float(remove_buy)))

                db.asset.update_one(
                    {"id":user_id},
                    {
                        "$set": {
                            "total buy" : total_buy,
                            "real gain" : real_gain,
                        }
                    }
                )
                break
        except Exception as e:
            print(e)

    return result

# Today's discover 예측
@app.route('/discover', methods=['POST', 'GET'])
def predict_discover():
    if request.method == 'POST':
    # return values
        result_dict = {}
        isOpen = True
        stocklist = None

        stockMarket = request.form.get('stockMarket')
        numOfStock = int(request.form.get('numOfStock'))

        selectedDate = datetime.today().strftime("%Y-%m-%d")
        #print(f"\n\n\nSelectedDate : {selectedDate}\n\n\n")

        t_buy_date = datetime.strptime(selectedDate, "%Y-%m-%d")
        t_prev_date = t_buy_date - timedelta(days=10)
        s_prev_date = t_prev_date.strftime("%Y-%m-%d")

        XKRX = xcals.get_calendar("XKRX") #개장일 가져오기
        pred_dates = XKRX.sessions_in_range(s_prev_date, selectedDate)
        open_dates = pred_dates.strftime("%Y-%m-%d").tolist()

        date = None
        temp = XKRX.sessions_in_range(selectedDate, selectedDate).tolist()
        print(f"\n\n\ntemp : {temp}\n\n\n")
        if len(temp) == 0:
            date = open_dates[-1]
        else:
            date = open_dates[-2]   #어제 날짜 입력
        print(open_dates)

        filename = f'/home/ubuntu/2022_VAIV_Dataset/flask/static/today_results/{date}_{stockMarket}_{numOfStock}.json'

        ensemble_prob = []
        ensemble_result = []
        if not path.isfile(filename):
            stocklist = discover(stockMarket, date, numOfStock)

            # yolo detection 추가
            tickerlist = [result[0][1:] for result in stocklist]

            result_dict['isOpen'] = isOpen
            result_dict['results'] = stocklist
            result_dict['realDate'] = date
            #ensemble_data = pd.read_csv('/home/ubuntu/2022_VAIV_HyunJoon/Stacking/prob.csv') #임시적 앙상블 모델 예측값

            #ensemble_prob = ensemble_data['Probablity'].tolist()
            #ensemble_result = ensemble_data['Prediction'].tolist()

            # 임시 코드 (앙상블 모델) - 난수 생성
            # for i in range(len(stocklist)):
            #     prob = round(random.random() * 100, 2)
            #     res = random.randint(0, 1)
            #     ensemble_prob.append(prob)
            #     ensemble_result.append(res)

            # result_dict['ensemble_prob'] = ensemble_prob
            # result_dict['ensemble_result'] = ensemble_result

            with open(filename, 'w') as outfile:
                json.dump(result_dict, outfile, indent=4)
        else:
            with open(filename, 'r') as json_file:
                result_dict = json.load(json_file)

        currentlist = []
        # result_dict에 currentClose 추가
        loadStocklist = result_dict['results']

        # yolo detection 추가
        tickerlist = [result[0][1:] for result in loadStocklist]
        detectlist, detect = yolo_buy(tickerlist, date, stockMarket)
        for i in range(len(loadStocklist)):
            loadStocklist[i][3].append(detectlist[i])
        result_dict['results'] = loadStocklist
        result_dict['yolo'] = detect
        # torch.multiprocessing.set_start_method('spawn')
        # p = mp.Process(target=yolo_buy, args=(tickerlist, date, stockMarket, ))
        # p.start()
        # p.join()

        start = time.time()
        for row in loadStocklist:
            ticker = row[0]
            currentClose = None
            try:
                s = requests.Session()
                url = "https://finance.naver.com/item/main.nhn?code=" + ticker[1:]
                resp = s.get(url)
                currentClose = resp.text.split("<dd>현재가 ")[1].split(' ')[0].replace(",","")
            except:
                currentClose = 0
            currentlist.append(currentClose)
        end = time.time()

        #print("\n\n\n")
        #print(end - start)
        #print("\n\n\n")

        result_dict['currentlist'] = currentlist
        print('Result Dict: ')
        print(result_dict)
        return result_dict


# 현재가 불러오기
@app.route('/current', methods=['POST'])
def get_current_close():
    result_dict = {}
    ticker = request.form.get('ticker')
    s_date = request.form.get('s_date')
    currentClose = None
    try:
        s = requests.Session()
        url = "https://finance.naver.com/item/main.nhn?code=" + ticker[1:]
        resp = s.get(url)
        currentClose = resp.text.split("<dd>현재가 ")[1].split(' ')[0].replace(",","")
    except:
        currentClose = 0
    result_dict['currentClose'] = currentClose
    return result_dict

# # 현재가 리스트 불러오기
# @app.route('/currentlist', methods=['POST'])
# def get_current_close_list():
#     result_dict = {}
#     currentlist = []
#     tickerlist = request.form.getlist('tickerlist[]')
#     currentClose = None

#     print(tickerlist)

#     for ticker in tickerlist:
#         try:
#             s = requests.Session()
#             url = "https://finance.naver.com/item/main.nhn?code=" + ticker[1:]
#             resp = s.get(url)
#             currentClose = resp.text.split("<dd>현재가 ")[1].split(' ')[0].replace(",","")
#             print(currentClose)
#         except:
#             currentClose = 0
#         currentlist.append(currentClose)

#     result_dict['currentlist'] = currentlist
#     return result_dict

# Back Testing 예측
@app.route('/backtest', methods=['POST'])
def predict_backtest():
    result_dict = {}
    startDate = request.form.get('startDate')   # 2022-01-01
    endDate = request.form.get('endDate')   # 2022-10-10
    numOfStocks = request.form.get('stocks')    # 20
    stockMarket = request.form.get('stockMarket')   # KOSPI | KOSDAQ
    model = request.form.getlist('model[]')   # VGG16 | EfficientNet : list
    sellCondition = request.form.get('sellcondition')   # -20

    ticker_data = pd.read_csv('/home/ubuntu/2022_VAIV_Dataset/Stock_Data/Kosdaq.csv')
    if(stockMarket == 'KOSPI'):
      ticker_data = pd.read_csv('/home/ubuntu/2022_VAIV_Dataset/Stock_Data/Kospi.csv')

    ticker_list = ticker_data['Symbol'].values

    model_list = []
    pr_list=[]
    label_list = []
    for i in range(len(model)):
      if(model[i]=='EfficientNet'):
        if(stockMarket == 'KOSPI'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSPI/new_efficient_4.csv')
          pr_list.append(0.625)
        elif(stockMarket == 'KOSDAQ'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSDAQ/new_efficient_kosdaq.csv')
          pr_list.append(0.55)
        label_list.append('EffiB7')
      elif(model[i]=='VGG16'):
        if(stockMarket == 'KOSPI'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSPI/new_vgg16_4.csv')
          pr_list.append(0.625)
        elif(stockMarket == 'KOSDAQ'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSDAQ/new_vgg16_kosdaq.csv')
          pr_list.append(0.675)
        label_list.append('VGG16')

    size = 224
    fore = 5

    kos = None
    if stockMarket == 'KOSPI':
        kos = 'Kospi'
    else:
        kos = 'Kosdaq'

    print("\n\n\n")
    print(f"startDate : {startDate}")
    print(f"endDate : {endDate}")
    print(f"model_list : {model_list}")
    print(f"fore : {fore}")
    print(f"numOfStocks : {numOfStocks}")
    print(f"ticker_list : {ticker_list}")
    print(f"sellCondition : {type(sellCondition)}")
    print(f"kos : {kos}")
    print(f"pr_list : {pr_list}")
    print(f"label_list: {label_list}")
    print("\n\n\n")
    result_dict = backtest( startDate, endDate, model_list, fore, int(numOfStocks), int(sellCondition), kos, label_list)
    print(result_dict['profit'])
    #result_dict['profit'] = profit
    print("re : ",result_dict)
    return result_dict

# 날짜 길이 불러오기
@app.route('/getopendates', methods=['POST'])
def getopendates():
    startDate = request.form.get('startDate')
    endDate = request.form.get('endDate')

    # XKRX = xcals.get_calendar("XKRX") #개장일 가져오기
    # dateList = XKRX.sessions_in_range(startDate, endDate).tolist()
    # dateLength = len(dateList)

    s_date = datetime.strptime(startDate, "%Y-%m-%d")
    e_date = datetime.strptime(endDate, "%Y-%m-%d")
    diff = e_date - s_date
    dateLength = diff.days

    result_dict = {}
    result_dict['countDates'] = dateLength
    return result_dict

@app.route('/sell', methods=['POST'])
def sell():
    print('----------------Sell----------------')
    # global yolo_detect
    # print(yolo_detect)
    ticker = request.form.get('ticker')[1:]
    s_date = request.form.get('s_date')
    market = request.form.get('stockMarket').lower().capitalize()
    XKRX = xcals.get_calendar("XKRX")
    trade_date = XKRX.next_session(s_date).strftime('%Y-%m-%d')
    result_dict = {}
    # if ticker in yolo_detect.get(market).keys():
    #     ret = yolo_detect.get(market)
    # else:
    #     ret = yd.detect_list([ticker], trade_date, market=market)
    today = datetime.now().strftime('%Y-%m-%d')
    ret = yd.detect_first([ticker], today, market=market)

    # print('Detect Return: ', ret)
    result_dict['trade_date'] = trade_date
    result_dict['signal'] = ret[ticker][0]
    result_dict['probability'] = ret[ticker][1]
    result_dict['start'] = ret[ticker][2]
    result_dict['end'] = ret[ticker][3]
    # print('Yolo Result: ', result_dict)
    return result_dict


@app.route('/stock', methods=['GET'])
def stockData():
    ticker = request.args.get('ticker')
    timeframe = request.args.get('timeframe')
    start = time.time()
    # stock = load_csv_data(ticker, interval=timeframe)
    # print(ticker, timeframe)
    # print('Stock------------------------------')
    # print(stock)
    # # df = stock.get_market_ohlcv(ticker, fromdate='1990-01-01', todate=today)
    # stock = list(filter(nullCheck, stock))
    # stock = list(map(modifyStock, stock))
    stock = load_naver(ticker.split('.')[0])
    doc = {'stock': stock}
    end = time.time()
    print('Graph time: {0:.2f}'.format(end-start))
    return jsonify(doc)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
