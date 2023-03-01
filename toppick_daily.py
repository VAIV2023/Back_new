from demo import yolo_buy, yolo_buy_new
import pandas as pd
from datetime import datetime, timedelta
import exchange_calendars as ecals
import time
import os
from csv import writer
import argparse
import schedule

"""
전날에 미리 detection 결과 저장해놓는 코드
nohup python3 toppick.py & 로 실행하기
"""

def list_chunk(lst, n):     # n : 몇 개씩 분할할 것인지
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def toppick_detect(version, mar):
    XKRX = ecals.get_calendar("XKRX") # 한국 코드

    # 오늘이 개장일이었는지 확인
    # 개장일이면 다음 개장일 날짜 불러와서 input으로 넣기
    # 개장일 아니면 pass
    date = datetime.today().strftime("%Y-%m-%d")
    if not XKRX.is_session(date):  # temp
       return
    
    #date = "2023-02-27"     # temp

    # 전종목 티커 가져오기
    stock_df = pd.read_csv("/home/ubuntu/Back_new/static/Stock.csv", index_col=0)
    KOSPI_df = stock_df.loc[stock_df['Market'] == 'STK']
    KOSDAQ_df = stock_df.loc[stock_df['Market'] == 'KSQ']

    kospi_list = KOSPI_df.index.to_list()
    kosdaq_list = KOSDAQ_df.index.to_list()

    # Detection 시작 (yolo_buy 사용)
    print(f"\n---Detection start : {date}---")

    # temp code
    if mar == 'kospi':
        kosdaq_list = []
    else:
        kospi_list = []
    
    print("!!! number of KOSPI Tickers !!!")
    print(len(kospi_list))
    print("!!! number of KOSDAQ Tickers !!!")
    print(len(kosdaq_list))
    stock_dict = {}
    stock_dict = {'KOSPI' : kospi_list, 'KOSDAQ' : kosdaq_list}
    res_dict = {'KOSPI' : [], 'KOSDAQ' : []}
    split_opt = 100     # 과부하 방지 위해 분할해서 프로세스 진행

    for market in stock_dict:
        stock_list = stock_dict[market]
        split_list = list_chunk(stock_list, split_opt)
        count = 0
        ticker_ = []
        signal_ = []
        prob_ = []
        close_ = []
        start_ = []
        end_ = []


        for ticker_list in split_list:
            count += 1
            print(f"{market} : {count}")
            res_detect = None
            if version == 'old':
                res_detect = yolo_buy(ticker_list, date, market)[1]
            else:
                res_detect = yolo_buy_new(ticker_list, date, market)[1]
            # print(ticker_list)
            # print(len(ticker_list))
            # time.sleep(60)
            # continue

            print(f"res_detect: {res_detect}")
            # Sell, Buy Signal 뜬 종목 코드만 뽑아서 result list에 저장
            for ticker in res_detect:
                info = res_detect[ticker]
                signal = info[0]
                if signal == 'buy' or signal == 'sell':
                    end = info[4]
                    end_t = datetime.strptime(end, "%Y-%m-%d")
                    end = end_t.strftime("%Y%m%d")
                    #if end != datetime.today().strftime("%Y%m%d"):
                    #    print(f"???? end : {end}")
                    #    continue
                    ticker_.append(str(ticker))
                    signal_.append(signal)
                    prob_.append(info[1])
                    close_.append(float(info[2]))
                    start = info[3]
                    start_t = datetime.strptime(start, "%Y-%m-%d")
                    start = start_t.strftime("%Y%m%d")
                    start_.append(str(start))
                    end_.append(str(end))

        file_name = f'/home/ubuntu/Back_new/static/toppick/{market}/{date}.csv'
        if version == 'new':
            file_name = f'/home/ubuntu/Back_new/static/toppick/{market}/{date}_new.csv'
            
        # static/toppick_csv/{market}/날짜.csv에 저장
        if os.path.isfile(file_name):
            # add
            with open(file_name, 'a', newline='') as f_object:
                writer_object = writer(f_object)
                for i in range(len(ticker_)):
                    lst = [signal_[i], ticker_[i], prob_[i], close_[i], start_[i], end_[i]]
                    writer_object.writerow(lst)       
                f_object.close()

        else:
            # create
            data = {
                'Signal': signal_,
                'Ticker': ticker_,
                'Probability': prob_,
                'Close': close_,
                'Start': start_,
                'End': end_,
            }
            df = pd.DataFrame(data)
            if version == 'old':
                df.to_csv(file_name, index=False)
            else:
                df.to_csv(file_name, index=False)
    
    print(f"\n---Detection successed : {date}---")
    #print(f"buy/sell ticker list : {res_dict}")
    

    return res_dict

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(
    #     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # parser.add_argument('-s', '--start',
    #                     help='number of stocks', type=str, default=0)
    # parser.add_argument('-e', '--end',
    #                     help='number of stocks', type=str, default=1600)                  
    # args = parser.parse_args()
    # start = args.start
    # end = args.end

    # 실행 주기 설정
    # Updating Prediction Data
    schedule.every().day.at("17:00").do(toppick_detect, 'old', 'kospi')   # 매일 오후 5시에 update_stock 함수 실행
    schedule.every().day.at("17:30").do(toppick_detect, 'old', 'kosdaq')   # 매일 오후 5시에 update_stock 함수 실행
    schedule.every().day.at("18:00").do(toppick_detect, 'new', 'kospi')   # 매일 오후 5시에 update_stock 함수 실행
    schedule.every().day.at("18:30").do(toppick_detect, 'new', 'kosdaq')
    #toppick_detect('old')
    #toppick_detect('new')
    
    # 실행 시작
    while True:
        schedule.run_pending()