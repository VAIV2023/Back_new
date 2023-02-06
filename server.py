from flask import Flask, request, jsonify
from flask_cors import CORS
from toppick import toppick_detect

from datetime import datetime, timedelta
import exchange_calendars as ecals 
import pandas as pd

app = Flask(__name__)
app.config['DEBUG'] = True
CORS(app)

@app.route("/example", methods=['GET', 'POST'])
def example():
    option = request.json
    print(option)
    result = { 'stocks' : 'samsung'}
    
    return jsonify(result)

@app.route("/showtoppick", methods=['GET', 'POST'])
def toppick_show():
    option = request.json
    print(option)

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
    
    print(res_dict)
    return jsonify(res_dict)

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)