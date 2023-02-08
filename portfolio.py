import schedule
import time
from pymongo import MongoClient
import pandas as pd
from time import time
from datetime import datetime, timedelta
import exchange_calendars as ecals 

global client
client = MongoClient('mongodb://vaivwinter:vaivwinter2023!@3.37.180.191', 27017)

global availableBuyNum
availableBuyNum = 10

stock_df = pd.read_csv("/home/ubuntu/Back_new/static/Stock.csv", index_col=0)
global KOSPI_df
global KOSDAQ_df
KOSPI_df = stock_df.loc[stock_df['Market'] == 'STK']
KOSDAQ_df = stock_df.loc[stock_df['Market'] == 'KSQ']


def selectToppick(id, code):
    global availableBuyNum
    if availableBuyNum == 0:
        return

    date = '2023-02-08' #datetime.today().strftime("%Y-%m-%d")
    last_date = '20230207'  # temp code

    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            if code in account_list:
                account = d[code]
                holdingStock = account['holdingStock']
                buyStockNum = int(account['buyStockNum'])
                balance = float(account['balance'])
                
                # Toppick 종목 불러오기 (일단 KOSPI만)
                df = pd.read_csv(f'/home/ubuntu/Back_new/static/toppick/KOSPI/{date}.csv', index_col=False)
                buyPick = df.loc[df['Signal'] == 'buy']
                todayPick = buyPick.loc[df['End'] == int(last_date)]

                # confidence score 순으로 정렬
                sortedPick = todayPick.sort_values('Probability', ascending=False)

                # availableBuyNum만큼 자르기
                if len(sortedPick) > availableBuyNum:
                    sortedPick = sortedPick.iloc[:availableBuyNum]
                    buyStockNum += availableBuyNum
                    availableBuyNum = 0
                else:
                    buyStockNum += len(sortedPick)
                    availableBuyNum -= len(sortedPick)
                
                exit()

                for row in sortedPick.values:
                    ticker = row[1]
                    buyPrice = row[3]
                    seed = 2000000
                    quantity = "%0.1f" % float(float(seed) / float(buyPrice))
                    balance = float(balance) - float(quantity * float(buyPrice))

                    # KOSPI_df에서 종목명 찾기
                    stockName = KOSPI_df.loc[ticker]['Symbol']

                    stock = {
                        'ticker': ticker,
                        'stockName': stockName,
                        'quantity': quantity,
                        'buyDate': date,
                        'buyPrice': buyPrice,
                    }
                    holdingStock.append(stock)
                
                # 변경된 holdingStock, balance, buyStockNum를 account에 업데이트
                account['holdingStock'] = holdingStock
                account['balance'] = balance
                account['buyStockNum'] = buyStockNum

                # 해당 account 업데이트 (DB)
                db.user.update_one(
                    {"user_id": id},
                    {
                        "$set": {
                            code: account,
                        }
                    }
                )
            break

selectToppick('temp', 'ejf5wow1')
"""
if __name__ == "__main__":
    schedule.every(1).second.do(selectToppick)

    while True:
        schedule.run_pending()
        time.sleep(10)
"""