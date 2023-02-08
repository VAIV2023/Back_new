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

client = MongoClient('mongodb://vaivwinter:vaivwinter2023!@3.37.180.191', 27017)

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
                'account_list': [],
            }
            db.user.insert_one(user_info)
            success = 0
        
    res_dict['success'] = success
    return jsonify(res_dict)

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
            account_list = d['account_list']
            
            if code not in account_list:
                account = {
                    'name': name,
                    'createDate': date,
                    'isOperating': 0,
                    'balance': 20000000,
                    'buyStockNum': 0,
                    'dailyRealProfit': {}, 
                    'dailyMarketValue': {},
                    'sellStock': [],
                    'holdingStock': [],
                    'totalBuy': 0,
                    'realGain': 0,
                    'realProfit': 0,
                }

                # account_list에 account 추가
                account_list.append(code)

                # account_list 업데이트, account 추가 (DB)
                db.user.update_one(
                    {"user_id": id},
                    {
                        "$set": {
                            code: account,
                            "account_list": account_list,
                        }
                    }
                )
                success = 1

            else:
                print("계좌 생성 - 이미 존재!!")
                success = 0

            break
    
    res_dict['success'] = success
    return jsonify(res_dict)

@app.route("/deleteaccount", methods=['GET', 'POST'])
def deleteAccount():
    # success(1) : 계좌 삭제 성공
    # success(0) : 해당 코드를 가진 계좌가 존재하지 않음
    # success(-1) : 에러 또는 id 존재x
    option = request.json
    id = option['id']
    code = option['code']
    res_dict = {}
    success = -1

    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            
            if code in account_list:
                # account_list에서 해당 code 제거
                account_list.remove(code)

                # 해당 code가 key인 field 제거 (DB)
                db.user.update_one(
                    {"user_id": id},
                    {
                        "$unset": {
                            code: True,
                        }
                    }
                )

                # account_list 업데이트 (DB)
                db.user.update_one(
                    {"user_id": id},
                    {
                        "$set": {
                            "account_list": account_list,
                        }
                    }
                )
                success = 1

            else:
                print("계좌 삭제 - 존재하지 않는 계좌 코드!!!")
                success = 0

            break
    
    res_dict['success'] = success
    return jsonify(res_dict)

@app.route("/checkaccount", methods=['GET', 'POST'])
def checkAccount():
    option = request.json
    id = option['id']
    res_dict = {}
    success = -1

    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            for code in account_list:
                account = {
                    'name': d[code]['name'],
                    'createDate': d[code]['createDate'],
                }
                res_dict[code] = account
            success = 1
            break
    
    res_dict['success'] = success
    return jsonify(res_dict)

    

@app.route("/dailymarketvalue", methods=['GET', 'POST'])
def dailyMarketValue():
    # success(1) : 성공
    # success(-1) : 에러 또는 id 존재x
    option = request.json
    id = option['id']
    code = option['code']
    res_dict = {}
    success = -1

    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            
            if code in account_list:
                res_dict = d[code]['dailyMarketValue']
                success = 1

    return jsonify(res_dict)

@app.route("/dailyrealprofit", methods=['GET', 'POST'])
def dailyRealProfit():
    # success(1) : 성공
    # success(-1) : 에러 또는 id 존재x
    option = request.json
    id = option['id']
    code = option['code']
    res_dict = {}
    success = -1

    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            
            if code in account_list:
                res_dict = d[code]['dailyRealProfit']
                success = 1

    return jsonify(res_dict)



@app.route("/showtoppick", methods=['GET', 'POST'])
def showToppick():
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
    date = "2023-02-08"
    last_date = "20230207"

    res_dict = {'KOSPI' : [], 'KOSDAQ' : []}
    market_list = ['KOSPI', 'KOSDAQ']
    # static/toppick/{market}/날짜.csv 에 저장되어있는 toppick 종목
    # line by line으로 읽어와서 리턴
    for market in market_list:
        df = pd.read_csv(f"/home/ubuntu/Back_new/static/toppick/{market}/{date}.csv", index_col=False)
        buyPick = df.loc[df['Signal'] == 'buy']
        todayPick = buyPick.loc[df['End'] == int(last_date)]

        # confidence score 순으로 정렬
        sortedPick = todayPick.sort_values('Probability', ascending=False)

        lst = []
        for row in sortedPick.values:
            # ticker가 integer로 저장되면서 앞에 있는 0 없어지는 오류 수정 (6자리로 만들기)
            ticker = str(row[1])
            while len(ticker) < 6:
                ticker = '0' + ticker
            data = {
                'ticker': ticker,
                'start': str(row[4]),
                'end': str(row[5]),
            }
            lst.append(data)

        res_dict[market] = lst

    print(res_dict)

    end = time()
    print(f"{end - start:.5f} sec")

    return jsonify(res_dict)

@app.route("/buytoppick", methods=['GET', 'POST'])
def buytoppick():
    # success(1) : 새롭게 구매
    # success(0) : 기존 구매 내역에 수량만 추가
    # success(-1) : 에러 또는 id/account가 존재하지 않음 또는 잔고부족

    option = request.json
    id = option['id']
    code = option['code']
    ticker = option['ticker']
    stockName = option['stockName']
    quantity = option['quantity']
    buyPrice = option['buyPrice']
    date = datetime.today().strftime("%Y-%m-%d")
    success = -1
    res_dict = {}
    
    # 오늘이 거래일이 아닌 경우 막아놓도록 해야됨

    # 존재하는 id, account인지 확인
    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            if code in account_list:
                account = d[code]
                # 잔고가 부족한지 확인
                if account['balance'] < (int(quantity) * int(buyPrice)):
                    success = -1

                # 같은 날에 이미 담은 종목이 있는지 확인
                holdingStock = account['holdingStock']
                for i in range(len(holdingStock)):
                    stock = holdingStock[i]
                    if stock['ticker'] == ticker and stock['buyDate'] == date:
                        # 기존에 담은 거에다가 수량만 추가 (같은 날에 어느 시기에 사든 전날 종가는 변하지 않으니까!!)
                        stock['quantity'] = int(stock['quantity']) + int(quantity)
                        # holdingStock에 stock 정보 업데이트
                        holdingStock[i] = stock
                        success = 0
                        break
                
                if success == -1:   # 기존 구매 내역이 없을 경우
                    buyTotalPrice = int(quantity) * int(buyPrice)
                    stock = {
                        'ticker': ticker,   # 종목 코드
                        'stockName': stockName,
                        'quantity': quantity,   # 수량
                        'buyDate': date,     # 매수 날짜
                        'buyPrice': buyPrice,   # 매수 가격  
                    }
                    # holdingStock에 stock 정보 업데이트
                    holdingStock.append(stock)
                    success = 1

                # account에 holdingStock 정보 업데이트
                account['holdingStock'] = holdingStock

                # 해당 account 업데이트 (DB)
                db.user.update_one(
                    {"user_id": id},
                    {
                        "$set": {
                            code: account,
                        }
                    }
                )

            else:
                # 해당 account가 존재하지 않음
                success = -1
            
            break

    res_dict['success'] = success
    return jsonify(res_dict)


@app.route("/startportfolio", methods=['GET', 'POST'])
def startPortfolio():
    # success(1) : 성공
    # success(0) : id 존재 x
    # success(-1) : 에러 또는 거래일이 아님
    option = request.json
    id = option['id']
    code = option['code']
    res_dict = {}
    success = -1

    db = client.portfolio
    # 거래일인지 확인
    XKRX = ecals.get_calendar("XKRX") # 한국 코드
    date = datetime.today().strftime("%Y-%m-%d")
    if XKRX.is_session(date):
        # temp code
        date = "2023-02-06"

        # id, 계좌 확인 (이미 포트폴리오 관리 중인지 확인)
        for d in db['user'].find():
            if d['user_id'] == id:
                account_list = d['account_list']
                if code in account_list:
                    # 포트폴리오 관리 실행이 이미 되어있는 계좌인지 확인
                    if d[code]['isOperating'] == 0:
                        print(f"=== 계좌 {code} 자산 운용 시작 : {date} ===")
                        success = 1
                    else:
                        success = -1
                else:
                    success = -1
                break
    else:
        success = -1

    

    



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)