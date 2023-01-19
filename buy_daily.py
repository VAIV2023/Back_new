import json
from pymongo import MongoClient
from datetime import datetime, timedelta
from predict_newDemo import discover
import exchange_calendars as xcals
import requests

# condition 0 : only vgg
# condition 1 : only effi
# condition 2 : vgg and effi (교집합)
# condition 3 : vgg or effi (합집합)
# date format ; 2022-11-28
def buy_stocks(user_id, condition, start_date, end_date):
    stockMarket = 'KOSPI'
    XKRX = xcals.get_calendar("XKRX") #개장일 가져오기
    pred_dates = XKRX.sessions_in_range(start_date, end_date)
    open_dates = pred_dates.strftime("%Y-%m-%d").tolist()
    numOfStock = 20

    client = MongoClient("mongodb://localhost:27017/")
    db = client.user_asset

    for d in db['asset'].find():
        try:
            if d['id'] == user_id:
                asset_list = d['asset_list']

        except Exception as e:
            print(e)        

    # ['A377300', '카카오페이', 56400, [['VGG16', 1.0, 65.8], ['EfficientNet', 1.0, 64.5]], 501.30303657]
    for date in open_dates:
        stocklist = discover(stockMarket, date, numOfStock)
        
        for stock in stocklist:
            vgg_res = stock[3][0][1]
            effi_res = stock[3][1][1]
            res = False
            # condition 0 : only vgg
            if condition == 0:
                if vgg_res == 1.0:
                    res = True
            # condition 1 : only effi
            elif condition == 1:
                if effi_res == 1.0:
                    res = True
            # condition 2 : vgg and effi (교집합)
            elif condition == 2:
                if vgg_res == 1.0 and effi_res == 1.0:
                    res = True
            # condition 3 : vgg or effi (합집합)
            elif condition == 3:
                if vgg_res == 1.0 or effi_res == 1.0:
                    res = True
            else:
                print("invalid condition")
                exit()
            if not res:
                continue
            market = 'KOSPI'
            ticker = stock[0]
            name= stock[1]
            buy_date = date
            buy_count = 1
            buy_close = stock[2]
            buy_total = buy_count * buy_close

            stock_info = {
                    "market" : market,
                    "ticker" : ticker,   #fixed
                    "name" : name,   #fixed
                    "buy date" : buy_date,   #fixed
                    "buy count" : int(buy_count),   #fixed
                    "buy close" : int(buy_close),   #fixed
                    "buy total" : int(buy_total),   #fixed
            }
            asset_list.append(stock_info)




    db.asset.update_one(
        {"id":user_id},
        {
            "$set": {
                "asset_list" : asset_list
            }
        }
    )

buy_stocks("vgg16_kospi_2", 0, '2022-11-22', '2022-11-24')