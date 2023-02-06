from demo import yolo_buy
import pandas as pd
from find_sell import detect_all
from datetime import datetime, timedelta
import exchange_calendars as ecals
import time

"""
전날에 미리 detection 결과 저장해놓는 코드
nohup python3 toppick.py & 로 실행하기
"""

def list_chunk(lst, n):     # n : 몇 개씩 분할할 것인지
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def toppick_detect():
    XKRX = ecals.get_calendar("XKRX") # 한국 코드
    # 내일 날짜 불러오기 (아아악 헷갈려 담날이 폐장일이면? -> 그냥 오늘 기준으로 다음 개장일 날짜 불러오기)
    """
    date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    if not XKRX.is_session(date):
        next_date = XKRX.next_open(pd.Timestamp.today()) # 다음 개장일은 언제인지 확인
        date = next_date.strftime("%Y-%m-%d")
    """

    date = '2023-02-06'
    # 오늘이 장 열린 날짜인지 확인
    date_time = datetime.strptime(date, "%Y-%m-%d")     # temp
    #if not XKRX.is_session(datetime.today()):
    #    return
    if not XKRX.is_session(date_time):  # temp
        return

    # 전종목 티커 가져오기
    stock_df = pd.read_csv("/home/ubuntu/Back_new/static/Stock.csv", index_col=0)
    KOSPI_df = stock_df.loc[stock_df['Market'] == 'STK']
    KOSDAQ_df = stock_df.loc[stock_df['Market'] == 'KSQ']

    kospi_list = KOSPI_df.index.to_list()[:100]
    kosdaq_list = KOSDAQ_df.index.to_list()[:100]

    # Detection 시작 (yolo_buy 사용)
    print(f"\n---Detection start : {date}---")

    stock_dict = {'KOSPI' : kospi_list, 'KOSDAQ' : kosdaq_list}
    res_dict = {'KOSPI' : [], 'KOSDAQ' : []}
    split_opt = 50     # 과부하 방지 위해 분할해서 프로세스 진행

    for market in stock_dict:
        stock_list = stock_dict[market]
        split_list = list_chunk(stock_list, split_opt)
        count = 0
        for ticker_list in split_list:
            count += 1
            print(f"{market} : {count}")
            res_detect = yolo_buy(ticker_list, date, market)[1]

            # Buy Signal 뜬 종목 코드만 뽑아서 result list에 저장
            for ticker in res_detect:
                signal = res_detect[ticker][0]
                if signal == 'buy':
                    res_dict[market].append(ticker)
            time.sleep(5)

        print(res_dict[market])
    
    print(f"\n---Detection successed : {date}---")
    print(f"buy ticker list : {res_dict}")

    # res_dict를 static/toppick_csv/{market}/날짜.txt에 저장
    # KOSPI 저장 (date : 내일 날짜)
    f = open(f'/home/ubuntu/Back_new/static/toppick/KOSPI/{date}.txt', 'w')
    for ticker in res_dict['KOSPI']:
        f.write(ticker)
        f.write("\n")
    f.close()
    # KOSDAQ 저장
    f = open(f'/home/ubuntu/Back_new/static/toppick/KOSDAQ/{date}.txt', 'w')
    for ticker in res_dict['KOSDAQ']:
        f.write(ticker)
        f.write("\n")
    f.close()

    return res_dict

if __name__ == '__main__':
    # 실행 주기 설정
    # Updating Prediction Data
    #schedule.every().day.at("17:00").do(toppick_detect)   # 매일 오후 5시에 update_stock 함수 실행
    toppick_detect()
    
    # 실행 시작
    #while True:
    #    schedule.run_pending()