import os
import sys
import shutil
from os import path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from predict_newDemo import discover
from backtesting import backtest
from find_sell import detect_list
from temp import find_sell_date
from pykrx import stock
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import multiprocessing as mp
import torch
import time
import requests
import exchange_calendars as xcals
from datetime import datetime, timedelta
import json
import random
from pymongo import MongoClient

# auto trading - buy
def auto_buy():
  result_dict = {}
  selectedDate = datetime.today().strftime("%Y-%m-%d")

  t_buy_date = datetime.strptime(selectedDate, "%Y-%m-%d")
  t_prev_date = t_buy_date - timedelta(days=10)
  s_prev_date = t_prev_date.strftime("%Y-%m-%d")

  XKRX = xcals.get_calendar("XKRX") 
  pred_dates = XKRX.sessions_in_range(s_prev_date, selectedDate)
  open_dates = pred_dates.strftime("%Y-%m-%d").tolist()

  date = None
  temp = XKRX.sessions_in_range(selectedDate, selectedDate).tolist()
  print(date)

  stockMarket = "KOSPI"
  numOfStock = "20"


  filename = f'/home/ubuntu/2022_VAIV_Dataset/flask/static/today_results/{date}_{stockMarket}_{numOfStock}.json'
  with open(filename, 'r') as json_file:
    result_dict = json.load(json_file)
  loadStocklist = result_dict['results']
  tickerlist = [result[0][0:] for result in loadStocklist]

  client = MongoClient("mongodb://localhost:27017/")
  db = client.user_asset


  for i in range(len(loadStocklist)):
    vgg_value = loadStocklist[i][3][0][1]
    effi_value = loadStocklist[i][3][1][1]
    if vgg_value==1.0 and effi_value==1.0:
      
      result = {}
      data = request.form.to_dict()
      print(f"\n\ndata : {data}\n\n")
      user_id = "vggeffi"

      ticker = loadStocklist[i][0]
      name = loadStocklist[i][1]
      buy_close = loadStocklist[i][2]
      buy_date = date
      buy_count = 1
      buy_total = int(buy_close) * int(buy_count)
      market = "KOSPI"

      stock_info = {
          "market" : market,
          "ticker" : ticker,   #fixed
          "name" : name,   #fixed
          "buy date" : buy_date,   #fixed
          "buy count" : int(buy_count),   #fixed
          "buy close" : int(buy_close),   #fixed
          "buy total" : int(buy_total),   #fixed
      }
      try:
        for d in db['asset'].find():
          if d['id'] == user_id:
              # modify 'asset_list'
              asset_list = d['asset_list']
              print(f"\nbefore add : {asset_list}\n")
              asset_list.append(stock_info)
              print(f"\nafter add : {asset_list}\n")
              db.asset.update_one(
                  {"id":user_id},
                  {
                      "$set": {
                          "asset_list" : asset_list
                      }
                  }
              )

              # modify 'total buy'
              total_buy = d['total buy']  # 총 매입
              
              total_buy += int(buy_total)

              print(f"\ntotal buy : {total_buy}")

              db.asset.update_one(
                  {"id":user_id},
                  {
                      "$set": {
                          "total buy" : total_buy,
                      }
                  }
              )
              break
      except Exception as e:
          print(e)

    if vgg_value==0.0 and effi_value==1.0:
      
      result = {}
      data = request.form.to_dict()
      print(f"\n\ndata : {data}\n\n")
      user_id = "effi"

      ticker = loadStocklist[i][0]
      name = loadStocklist[i][1]
      buy_close = loadStocklist[i][2]
      buy_date = date
      buy_count = 1
      buy_total = int(buy_close) * int(buy_count)
      market = "KOSPI"

      stock_info = {
          "market" : market,
          "ticker" : ticker,   #fixed
          "name" : name,   #fixed
          "buy date" : buy_date,   #fixed
          "buy count" : int(buy_count),   #fixed
          "buy close" : int(buy_close),   #fixed
          "buy total" : int(buy_total),   #fixed
      }
      try:
        for d in db['asset'].find():
          if d['id'] == user_id:
              # modify 'asset_list'
              asset_list = d['asset_list']
              print(f"\nbefore add : {asset_list}\n")
              asset_list.append(stock_info)
              print(f"\nafter add : {asset_list}\n")
              db.asset.update_one(
                  {"id":user_id},
                  {
                      "$set": {
                          "asset_list" : asset_list
                      }
                  }
              )

              # modify 'total buy'
              total_buy = d['total buy']  # 총 매입
              
              total_buy += int(buy_total)

              print(f"\ntotal buy : {total_buy}")

              db.asset.update_one(
                  {"id":user_id},
                  {
                      "$set": {
                          "total buy" : total_buy,
                      }
                  }
              )
              break
      except Exception as e:
          print(e)
def current_close_by_ticker(ticker):
    currentClose = None
    try:
        s = requests.Session()
        url = "https://finance.naver.com/item/main.nhn?code=" + ticker[1:]
        resp = s.get(url)
        currentClose = resp.text.split("<dd>현재가 ")[1].split(' ')[0].replace(",","")
    except:
        currentClose = 0
    return currentClose
# auto trading - sell
def auto_sell():
  client = MongoClient("mongodb://localhost:27017/")
  db = client.user_asset

  sell =[]
  for d in db['asset'].find():
    if d['id'] == 'vggeffi':
      print(d)
      sell_list = d['sell_list']
      asset_list = d['asset_list']
      for data in asset_list:
        temp = []
        if data['dayprofit'][4][0] != -1:
          temp.append(data['ticker'])
          temp.append(data['buy_date'])
          sell.append(temp)


  total_remove_buy=0
  total_real_gain =0
  sell_count=1
  for d in db['asset'].find():
    if d['id'] == 'vggeffi':
      print(d)
      
      
      # length = len(asset_list)
      for k in range(len(sell)):
        asset_list = d['asset_list']
        sell_list = d['sell_list']
        for data in asset_list
          try: 
              if data['ticker']==sell[k][0] and data['buy date']==sell[k][1]:
                remove_buy = data['buy total']
                total_remove_buy +=remove_buy
                stock = data
                stock['sell date'] = datetime.today().strftime("%Y%m%d")
                stock['sell close'] = current_close_by_ticker(data['ticker'])
                stock['sell count'] = sell_count
                sell_list.append(stock)
                del data

                db.asset.update_one(
                    {"id":user_id},
                    {
                        "$set": {
                            "asset_list" : asset_list,
                            "sell list" : sell_list
                        }
                    }
                )
                real_gain = int((float(current_close_by_ticker(data['ticker'])) * float(sell_count) * 0.9975 - float(remove_buy)))
                total_real_gain+=real_gain

      # modify 'total buy'
      total_buy = d['total buy']  # 총 매입
      
      total_buy -= int(total_remove_buy)

      print(f"\ntotal buy : {total_buy}")

      # modify 'real gain'
      new_real_gain = d['real gain']  # 실현 손익
      new_real_gain += total_real_gain
      db.asset.update_one(
          {"id":user_id},
          {
              "$set": {
                  "total buy" : total_buy,
                  "real gain" : new_real_gain,
              }
          }
      )
      break


if __name__ == '__main__':
  # 실행 주기 설정
  # Updating Stock Data
  schedule.every().day.at("15:30").do(update_stock)   # 매일 오후 3시 30분에 update_stock 함수 실행
  #update_stock()

  # 실행 시작
  while True:
      schedule.run_pending()