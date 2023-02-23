import schedule
import time
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, timedelta
import exchange_calendars as ecals 
import argparse

global client
client = MongoClient('mongodb://vaivwinter:vaivwinter2023!@3.37.180.191', 27017)

global availableBuyNum
availableBuyNum = 10

stock_df = pd.read_csv("/home/ubuntu/Back_new/static/Stock.csv", index_col=0)
global KOSPI_df
global KOSDAQ_df
KOSPI_df = stock_df.loc[stock_df['Market'] == 'STK']
KOSDAQ_df = stock_df.loc[stock_df['Market'] == 'KSQ']

"""
오늘이 매매 가능일인지 확인
"""
def checkOpeningDay():
    isOpen = True
    XKRX = ecals.get_calendar("XKRX") # 한국 코드
    date = datetime.today().strftime("%Y-%m-%d")
    last_date = None
    last_date_format = None
    if not XKRX.is_session(date):
        isOpen = False
    else:
        past = (datetime.today() - timedelta(days=20)).strftime("%Y-%m-%d")
        pred_dates = XKRX.sessions_in_range(past, date)
        open_dates = pred_dates.strftime("%Y%m%d").tolist()
        last_date = open_dates[-2]
        date = open_dates[-1]
        date_t = datetime.strptime(date, "%Y%m%d")
        date = date_t.strftime("%Y-%m-%d")  
        last_date_t = datetime.strptime(last_date, "%Y%m%d")
        last_date_format = date_t.strftime("%Y-%m-%d") 
    return isOpen, date, last_date, last_date_format
# 다음 개장일 보려면 걍 이거 쓰면 됨 : trade_date = XKRX.next_session(s_date).strftime('%Y-%m-%d')

"""
Toppick 종목 불러와서 confidence score가 높은 순으로 최대 10종목 선정 (매수)
"""
def selectToppick(id, code):
    global availableBuyNum
    if availableBuyNum == 0:
        return
    
    isOpen, date, last_date, last_date_format = checkOpeningDay()
    if not isOpen:
        print(f"개장일이 아님 : {date}")
        return

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
                df = pd.read_csv(f'/home/ubuntu/Back_new/static/toppick/KOSPI/{last_date_format}.csv', index_col=False)
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

"""
보유중인 주식만 detect (today's pick에서 결과만 불러오기)
판매할 주식 결정 (매도)

"""
def detectHoldingStock(id, code):
    global availableBuyNum
    if availableBuyNum == 0 or availableBuyNum == 10:
        return

    isOpen, date, last_date, last_date_format = checkOpeningDay
    if not isOpen:
        print(f"개장일이 아님 : {date}")
        return
    
    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            if code in account_list:
                account = d[code]
                holdingStock = account['holdingStock']
                sellStock = account['sellStock']
                balance = account['balance']
                todaySell = 0
                buyTotal = 0

                # Toppick 종목 불러오기 (일단 KOSPI만)
                df = pd.read_csv(f'/home/ubuntu/Back_new/static/toppick/KOSPI/{last_date_format}.csv', index_col=False)
                sellPick = df.loc[df['Signal'] == 'sell']
                todayPick = sellPick.loc[df['End'] == int(last_date)]
                tickerObj = todayPick['ticker']
                tickerList = tickerObj.values.tolist()

                # holdingStock 종목들 매도 검토
                for stock in holdingStock:
                    ticker = stock['ticker']
                    sellPrice = None
                    buyPrice = None
                    rate = None
                    try:
                        df = stock.get_market_ohlcv_by_date(last_date, last_date, ticker)
                        sellPrice = float(df.iloc[0]['종가'])
                        buyPrice = stock['buyPrice']
                        rate = (float(sellPrice)*0.9975 - float(buyPrice))/float(buyPrice) * 100
                    except Exception as e:
                        print("전날 종가 조회 오류?")
                        print(e)
                        continue
                    
                    # -20% 손실인 경우 손절 / 추천 매도 종목인지 확인
                    if (rate <= -20) or (ticker in tickerList):
                        # 보유 주식 리스트에서 삭제
                        holdingStock.remove(stock)

                        # stock에 매도 정보 추가
                        # “sell date”: <매도일: string>,
                        # “sell price”: <매도가: number>, 
                        # "rate": <수익률: number>
                        stock['sellDate'] = date
                        stock['sellPrice'] = sellPrice
                        stock['rate'] = rate
                        sellStock.append(stock)

                        # balance에 매도한 금액만큼 추가
                        balance = balance + float(sellPrice)*float(stock['quantity'])*0.9975

                        # realGain에 추가
                        todaySell = todaySell + float(sellPrice)*float(stock['quantity'])*0.9975
                        buyTotal = buyTotal + float(buyPrice)*float(stock['quantity'])
                    else:
                        continue
                
                # 변경된 holdingStock, balance, sellStock, dailyRealProfit을 account에 업데이트
                account['holdingStock'] = holdingStock
                account['balance'] = balance
                account['sellStock'] = sellStock
                todayRealProfit = (todaySell - buyTotal)/buyTotal*100
                account['dailyRealProfit'][date] = todayRealProfit
                

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

    

def dailyCalculate(id, code):
    global availableBuyNum
    if availableBuyNum == 10:
        return

    isOpen, date, last_date, last_date_format = checkOpeningDay
    if not isOpen:
        print(f"개장일이 아님 : {date}")
        return

    db = client.portfolio
    for d in db['user'].find():
        if d['user_id'] == id:
            account_list = d['account_list']
            if code in account_list:
                account = d[code]
                holdingStock = account['holdingStock']
                dailyMarketValue = account['dailyMarketValue']
                todayMarketValue = 0

                # 오늘의 총 평가 금액 (holdingStock 조회) (지난 개장일 종가 기준으로 계산)
                for stock in holdingStock:
                    ticker = stock['ticker']
                    quantity = stock['quantity']
                    last_price = None
                    try:
                        df = stock.get_market_ohlcv_by_date(last_date, last_date, ticker)
                        last_price = float(df.iloc[0]['종가'])
                    except Exception as e:
                        print(f"전날 종가 조회 오류 : {ticker}")
                        print(e)
                        continue
                    
                    todayMarketValue = todayMarketValue + int(last_price)*int(quantity)
                
                dailyMarketValue[last_date_format] = todayMarketValue
                
                # 변경된 dailyMarketValue를 account에 업데이트
                account['dailyMarketValue'] = dailyMarketValue

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
                

                    



#selectToppick('temp', 'ejf5wow1')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--id',
                        help='minimum profit when selling', type=str, required=True)
    parser.add_argument('-c', '--code',
                        help='top x of stocks', type=str, required=True)                  
    args = parser.parse_args()
    id = args.id
    code = args.code

    schedule.every().day.at("8:00").do(selectToppick, id, code)
    schedule.every().day.at("8:00").do(detectHoldingStock, id, code)
    schedule.every().day.at("2:00").do(dailyCalculate, id, code)

    while True:
        schedule.run_pending()
        time.sleep(10)
