from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.contrib.cache import GAEMemcachedCache

from datetime import datetime, timedelta
import exchange_calendars as ecals 
import pandas as pd

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

cache = GAEMemcachedCache()

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
        
        if sucess == -1:
            # DB에 계정 새로 등록
            print("=== Resigter ===")
            print(f"id : {id}")
            user_info = {
                'user_id': id,
                'accounts': {}
            }
            db.user.insert_one(user_info)
        
    res_dict['success'] = success
    return res_dict
    

@app.route("/showtoppick", methods=['GET', 'POST'])
def toppick_show():
    #option = request.json
    #print(option)
    res_dict = cache.get('toppick')

    if res_dict == None:
        # 오늘 날짜 그대로 넣으면 안되는구나..
        # 오늘이 개장일이면 오늘 날짜 그대로 입력
        # 오늘이 폐장일이면 ?? 다음에 올 개장일로 입력해야 됨.
        XKRX = ecals.get_calendar("XKRX") # 한국 코드
        date = datetime.today().strftime("%Y-%m-%d")
        if not XKRX.is_session(date):
            next_date = XKRX.next_open(pd.Timestamp.today()) # 다음 개장일은 언제인지 확인
            date = next_date.strftime("%Y-%m-%d")
        
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

        cache.set('toppick', res_dict)
    else:
        res_dict = cache.get(toppick)

    print(res_dict)
    return jsonify(res_dict)


@app.route("/buytoppick", methods=['GET', 'POST'])
def toppick_buy():
    option = request.json
    id = option['id']


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)