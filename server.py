from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from flask_caching import Cache
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning) # FutureWarning 제거

from datetime import datetime, timedelta
import exchange_calendars as ecals 
import pandas as pd
from time import time

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

client = MongoClient('mongodb://vaivwinter:vaivwinter2023!@43.201.8.26', 27017)

@app.route("/example", methods=['GET', 'POST'])
def example():
    option = request.json
    print(option)
    result = { 'stocks' : 'samsung'}
    
    return jsonify(result)

@app.route("/login", methods=['GET', 'POST'])
def login():
    # success(1) : 로그인 성공
    # success(0) : 계정 등록
    # success(-1) : 에러
    res_dict = {}
    success = -1

    if request.method == 'POST':
        option = request.json
        id = option['id']

        db = client.portfolio
        for d in db['user'].find():
            if d['user_id'] == id:
                success = 1
        
        if success == -1:
            # DB에 계정 새로 등록
            print("=== Resigter ===")
            print(f"id : {id}")
            user_info = {
                'user_id': id,
                'accounts': {}
            }
            db.user.insert_one(user_info)
            success = 0
        
    res_dict['success'] = success
    return res_dict

@app.route("/createaccount", methods=['GET', 'POST'])
def createAccount():
    # success(1) : 계좌 생성 성공
    # success(0) : 같은 코드를 가진 계좌가 이미 존재
    # success(-1) : 에러 또는 id 존재x
    option = request.json
    id = option['id']
    code = option['code']
    name = option['name']
    date = datetime.today().strftime("%Y-%m-%d")
    res_dict = {}
    success = -1

    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            accounts = d['accounts']
            
            if code not in accounts:
                print("?")
            else:
                print("계좌 생성 - 이미 존재!!")


@app.route("/showtoppick", methods=['GET', 'POST'])
@cache.cached(timeout=50)
def toppick_show():
    # 오늘 날짜 그대로 넣으면 안되는구나..
    # 오늘이 개장일이면 오늘 날짜 그대로 입력
    # 오늘이 폐장일이면 ?? 다음에 올 개장일로 입력해야 됨.
    start = time()

    # 이거 오래걸리는 코드니까 수정하기
    #XKRX = ecals.get_calendar("XKRX") # 한국 코드
    #date = datetime.today().strftime("%Y-%m-%d")
    #if not XKRX.is_session(date):
    #    next_date = XKRX.next_open(pd.Timestamp.today()) # 다음 개장일은 언제인지 확인
    #    date = next_date.strftime("%Y-%m-%d")
    
    # temp code
    date = "2023-02-06"

    res_dict = {'KOSPI' : [], 'KOSDAQ' : []}
    market_list = ['KOSPI', 'KOSDAQ']
    # static/toppick_csv/{market}/날짜.txt 에 저장되어있는 toppick 종목
    # line by line으로 읽어와서 리턴
    for market in market_list:
        f = open(f"/home/ubuntu/Back_new/static/toppick/{market}/{date}.txt", "r")
        lst = []
        while True:
            line = f.readline().strip()
            if not line: break
            lst.append(line)

        res_dict[market] = lst

    print(res_dict)

    end = time()
    print(f"{end - start:.5f} sec")

    return jsonify(res_dict)


@app.route("/buytoppick", methods=['GET', 'POST'])
def toppick_buy():
    # success(1) : 새롭게 구매
    # success(0) : 기존 구매 내역에 수량만 추가
    # success(-1) : 에러 또는 id/account가 존재하지 않음

    option = request.json
    id = option['id']
    code = option['account']
    ticker = option['ticker']
    stockName = option['stockName']
    quantity = option['quantity']
    buyPrice = option['buyPrice']
    date = datetime.today().strftime("%Y-%m-%d")
    success = -1
    res_dict = {}
    
    # 존재하는 id, account인지 확인
    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            accounts = d['accounts']
            if code in accounts:
                account = accounts[code]

                # 같은 날에 이미 담은 종목이 있는지 확인
                holdingStock = accounts[code]['holdingStock']
                for i in range(len(holdingStock)):
                    stock = holdingStock[i]
                    if stock['ticker'] == ticker and stock['buyDate'] == date:
                        # 기존에 담은 거에다가 수량만 추가 (같은 날에 어느 시기에 사든 전날 종가는 변하지 않으니까!!)
                        stock['quantity'] += quantity
                        # holdingStock에 stock 정보 업데이트
                        holdingStock[i] = stock
                        success = 0
                        break
                
                if success == -1:   # 기존 구매 내역이 없을 경우
                    buyTotalPrice = quantity * buyPrice
                    stock = {
                        'ticker': ticker,   # 종목 코드
                        'stockName': stockName,
                        'quantity': quantity,   # 수량
                        'buyDate': date,     # 매수 날짜
                        'buyPrice': buyPrice,   # 매수 가격
                        'buyTotalPrice': buyTotalPrice,     # 총 매수 가격    
                    }
                    # holdingStock에 stock 정보 업데이트
                    holdingStock.append(stock)
                    success = 1

                # accounts에 holdingStock 정보 업데이트
                accounts[code]['holdingStock'] = holdingStock

                # accounts 업데이트 (DB)
                db.user.update_one(
                    {"user_id": id},
                    {
                        "$set": {
                            "accounts": accounts,
                        }
                    }
                )

            else:
                # 해당 account가 존재하지 않음
                success = -1
            
            break

    res_dict['success'] = success
    return success
            


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)