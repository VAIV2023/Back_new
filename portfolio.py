import schedule
import time
from pymongo import MongoClient
import pandas as pd
from time import time
from datetime import datetime, timedelta
import exchange_calendars as ecals 

global client
client = MongoClient('mongodb://vaivwinter:vaivwinter2023!@43.201.8.26', 27017)

global availableBuyNum
availableBuyNum = 10

def selectToppick(id, code):
    global availableBuyNum
    if availableBuyNum == 0:
        return

    date = datetime.today().strftime("%Y-%m-%d")
    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            if code in account_list:
                holdingStock = d[code]['holdingStock']
                buyStockNum = d[code]['buyStockNum']
                balance = d[code]['balance']
                
                # Toppick 종목 불러오기 (일단 KOSPI만)
                df = pd.read_csv(f'/home/ubuntu/Back_new/static/toppick/KOSPI/{date}.csv', index_col=False)
                buyPick = df.loc[df['Signal'] == 'buy']

                # confidence score 순으로 정렬
                sortedPick = buyPick.sort_values('Probability', ascending=False)

                # availableBuyNum만큼 자르기
                if len(sortedPick) > availableBuyNum:
                    sortedPick = sortedPick.iloc[:availableBuyNum]
                    buyStockNum += availableBuyNum
                    availableBuyNum = 0
                else:
                    buyStockNum += len(sortedPick)
                    availableBuyNum -= len(sortedPick)

                for row in sortedPick.values:
                    ticker = row[1]
                    buyPrice = row[3]
                    seed = 2000000

                    stock = {
                        'ticker': ticker,
                        'stockName': ,
                        'quantity': ,
                        'buyDate': ,
                        'buyPrice': buyPrice,
                    }

            break

selectToppick('temp', 'ejf5wow1')
"""
if __name__ == "__main__":
    schedule.every(1).second.do(selectToppick)

    while True:
        schedule.run_pending()
        time.sleep(10)
"""