
import os
import sys, traceback
import logging
logging.basicConfig(level=logging.ERROR)
import math
import json
import sys
import imageio
import matplotlib.pyplot as plt
import numpy as np
from pandas_datareader import data
import argparse
import time
from datetime import timedelta
from datetime import datetime
import pandas as pd
from PIL import Image

def backtest( start, end, model_list, fore, topX,   sellProfit, kos, label_list):
    print(f"top : {topX}")
    
    result = {}
    result_profit = []
    result_winning = []
    result['market'] = kos
    result['count_model'] = len(model_list)
    
    model1 = pd.read_csv(model_list[0])
    st_date = datetime.strptime(start, "%Y-%m-%d")
    e_date = datetime.strptime(end,"%Y-%m-%d" )
    end_date = e_date.strftime("%Y%m%d")
    start_date = st_date.strftime("%Y%m%d")
    day_diff = e_date - st_date
    
    stock_data_label = None
    
    check_start = time.time()
    count=0
    # #/////////////////////
    
    # sd = datetime(int(start.split("-")[0]), int(start.split("-")[1]), int(start.split("-")[2]))
    # ed = datetime(int(end.split("-")[0]), int(end.split("-")[1]), int(end.split("-")[2]))
    # print(sd)
    # print(ed)
    # df = data.get_data_yahoo("^KS11", sd, ed)
    # stock_data_label = 'stcok'
    # if(kos=='Kosdaq'):
    #   df = data.get_data_yahoo("^KQ11", sd, ed)
    #   stock_data_label = 'kosdaq'
    # #print(df)


    # buy_price = df['Close'].iloc[0]
    # diff = df['Close'] - buy_price

    # rate = ( diff / buy_price ) * 100

    # df['Rate'] = rate

    # cumulative_rate = rate.copy()
    # for i in range(1, len(rate)):
    #     cumulative_rate[i] = rate[i] + cumulative_rate[i-1]

    # df['Cumulative rate'] = cumulative_rate


    
    # df.to_csv(f'/home/ubuntu/2022_VAIV_SeoHwan/make_graph/graph/KOSPI_profit.csv', mode="w")
    kospi_csv_data = pd.read_csv(f'/home/ubuntu/2022_VAIV_SeoHwan/make_graph/graph/KOSPI_profit.csv')
    check_end = time.time()
    print("time1 : ", check_end-check_start)
    color = []
    plt.figure(figsize=(20,10))
    trans_count = 0
    trans_list = []
    color_for_com = ['blue', 'red']
    
    kospi_check = False
    date_check= False
    kospi_date_list = []
    kospi_list = []
    d_list = []
    
    #prob_str = str(int(probability*100))

    Final_Efficient_Profit = 0
    Final_Vgg_Profit = 0


    
    win_list = []
    lose_list = []
    model_count = []
    final_profit_list=[]
    for i in range(day_diff.days+1):
      t_date = datetime.strptime(start, "%Y-%m-%d") + timedelta(days = i)
      t_date2 = t_date.strftime("%Y%m%d")
      t_date2 = t_date2[2:]
      d_list.append(t_date2)
    Final_win_list = []
    Final_lose_list = []
    for mod in range(len(model_list)):
      Final_win = 0
      Final_lose = 0
      check_profit = []
      year_buy_list = []
      date_list = []
      s_date = datetime.strptime(start, "%Y-%m-%d")
      e_date = datetime.strptime(end,"%Y-%m-%d" )
      d = []
      real_start = None
      start_data =0
      start_check=False
      
      no_list=[]
      cu_kospi = 0
      end_date = e_date.strftime("%Y%m%d")
      profit_list = []
      ac_profit =0
      ac_profit_no =0
      while s_date<=e_date:
        #/////////////////
        start_time = time.time()
        try : 
          if kospi_check == False:
            rate = kospi_csv_data[kospi_csv_data['Date']==s_date.strftime('%Y-%m-%d')].values[0][7]
            # cu_kospi  = cu_kospi + rate
            kospi_list.append(rate)
            temp_d = s_date.strftime("%Y%m%d")
            temp_d2 = temp_d[2:]
            kospi_date_list.append(temp_d2)
        except :
          ko = None
          if len(kospi_list)==0:
            ko = 0
          else : 
            ko=kospi_list[-1]
          kospi_list.append(ko)
          temp_d = s_date.strftime("%Y%m%d")
          temp_d2 = temp_d[2:]
          kospi_date_list.append(temp_d2)
        
      #//////////////////////////
        count = count+1
        check_start = time.time()
        print(count)
        try : 
          a=time.time()
          
          pred_csv = pd.read_csv(model_list[mod])
          temp_date = s_date.strftime('%Y-%m-%d')
          temp_year = temp_date.split('-')[0]
          pred_csv_data = pred_csv[pred_csv['Date']==temp_date].values
          

          ticker_data=[]
          if(len(pred_csv_data)<topX):
            for i in range(len(pred_csv_data)):
              ticker_data.append(pred_csv_data[i])
          else:
            for i in range(topX):
              ticker_data.append(pred_csv_data[i])
          print(ticker_data)
          # print(s_date)

            
          X=[]
          

          buy_list = []
          
          csv_date = s_date.strftime('%Y%m%d')
          buy_profit_no_list = []
          
          sum =0
          pred_date = None
          for t in ticker_data:

            try:
              day_close = float(t[3])
              predict_profit = None
              # first_profit=float(t[4])
              if(int(sellProfit)==0):
                if(pd.isna(t[4])):
                  predict_profit = 0
                # second_profit=float(t[5])
                elif(pd.isna(t[5])):
                  predict_profit = 0
                # third_profit=float(t[6])
                elif(pd.isna(t[6])):
                  predict_profit = 0
                # fourth_profit=float(t[7])
                elif(pd.isna(t[7])):
                  predict_profit = 0
                # fifth_profit=float(t[8])
                elif(pd.isna(t[8])):
                  predict_profit = 0
                else:
                  predict_profit = float(t[8])
              else:
                if(pd.isna(t[4])):
                  predict_profit = 0
                # second_profit=float(t[5])
                elif(pd.isna(t[5])):
                  predict_profit = float(t[4])
                # third_profit=float(t[6])
                elif(pd.isna(t[6])):
                  predict_profit = float(t[5])
                # fourth_profit=float(t[7])
                elif(pd.isna(t[7])):
                  predict_profit = float(t[6])
                # fifth_profit=float(t[8])
                elif(pd.isna(t[8])):
                  predict_profit = float(t[7])
                else:
                  predict_profit = float(t[8])
              
              
              
              
              

              
              if(float(sellProfit)<0):
                for i in range(int(fore)):
                  if(t[4+i]!=None):
                    temp_profit = float(t[4+i])
                    if(temp_profit < float(sellProfit)):
                      if i==0:
                        predict_profit=0
                      else :
                        predict_profit=float(t[4+i])
                      break
              
              if(predict_profit>0):
                Final_win = Final_win +1
              else:
                Final_lose = Final_lose +1
              buy_profit_no_list.append(predict_profit)
            
            except Exception as e:
              print(e)
          print(buy_profit_no_list)
          sum_profit_no=0
          for i in range(len(buy_profit_no_list)):
            sum_profit_no = sum_profit_no + buy_profit_no_list[i]

          avr_no = (sum_profit_no/len(buy_profit_no_list))
          ac_profit_no = ac_profit_no+avr_no
          no_list.append(ac_profit_no)
          if start_check==False:
            start_check = True
          
        

         
          
        except Exception as e:
          print(e)
          no_list.append(ac_profit_no)
        print("date : ", s_date)
        s_date = s_date + timedelta(days=1)

        end_time = time.time()
        print("!!!this is time!!!")
        print(f"{end_time - start_time}")
        print("!!!this is time!!!\n\n")

        



      

      
      print("no : ",no_list)

      temp_dict = {}
      temp_dict['date_list'] = d_list
      temp_dict['profit_list'] = no_list
      temp_dict['label'] = label_list[mod]
      result_profit.append(temp_dict)

      plt.plot(d_list, no_list, color_for_com[mod], label= label_list[mod], linewidth =4)
      
      kospi_check  = True
      date_check = True
      # plt.xticks(fontsize=15,rotation=-30)
      plt.text(d_list[-1],  no_list[-1]+ 0.4, '%.2f' %no_list[-1], ha='center', va='bottom', size = 30, color=color_for_com[mod])
      win_list.append(Final_win)
      lose_list.append(Final_lose)

      Final_win_list.append(Final_win)
      Final_lose_list.append(Final_lose)
      
      model_count.append(mod*(0.1))
      final_profit_list.append(no_list[-1])


    pltname = model_list[0].split('/')[-1]

    kospi_label = 'KOSPI'
    if(kos=='Kosdaq'):
      kospi_label = 'KOSDAQ'
    
    # temp_dict = {}
    # temp_dict['date_list'] = kospi_date_list
    # temp_dict['profit_list'] = kospi_list
    # temp_dict['label'] = kospi_label
    # result_profit.append(temp_dict)

    # plt.plot(kospi_date_list, kospi_list, 'g', label= kospi_label, linewidth =2)
    # plt.xlabel('Date')
    # plt.ylabel('Profit')
    plt.legend(loc='upper left', fontsize= 30)
    plt.xticks(np.arange(0, len(d_list), len(d_list)/5))
    #plt.yticks(np.arange(-50, 45, 5))
    plt.xticks(rotation=45)
    plt.xticks(fontsize=22)
    plt.yticks(fontsize=25)
    plt.title('Times New Roman',size=20)
    plt.grid(True)
    #plt.text(d_list[-35],  -48, string1, ha='center', va='bottom', size = 12)
    #####################################################################
    # plt.title(f'Profit')
    
    figName =f'/home/ubuntu/2022_VAIV_Dataset/flask/static/images/cumulative_profit.png'
    plt.savefig(figName)

    img = Image.open('/home/ubuntu/2022_VAIV_Dataset/flask/static/images/cumulative_profit.png')

    img_resize = img.resize((440, 350)) 
    img_resize.save('/home/ubuntu/2022_VAIV_Dataset/flask/static/images/cumulative_profit.png')
    plt.close()


    win_rate = int((Final_win/(Final_win+Final_lose))*100)
    lose_rate = 100-win_rate
    

    
    nothing = [0]
    
    color_for_win = [ 'crimson','red']
    color_for_lose = [ 'dodgerblue', 'blue']
    for i in range(len(model_count)):
      profit_rate = int((Final_win_list[i]/(Final_win_list[i]+Final_lose_list[i])) *100)
      lose_rate = 100 - profit_rate
      plt.barh(model_count[i], color = color_for_win[i], width = profit_rate, height=0.08, label=f"Profitable stocks ({Final_win_list[i]}_{label_list[i]})")
      plt.barh(model_count[i], color = color_for_lose[i], left=profit_rate,width = lose_rate,  height=0.08, label=f"Loss stocks ({Final_lose_list[i]}_{label_list[i]})")
      
      temp_dict = {}
      temp_dict['label'] = label_list[i]
      temp_dict['win_rate'] = profit_rate
      temp_dict['lose_rate'] = lose_rate
      temp_dict['final_win'] = Final_win_list[i]
      temp_dict['final_lose'] = Final_lose_list[i]

      result_winning.append(temp_dict)
      

      plt.legend(loc=(0, 0.75))
      
      win_str = f"{profit_rate}%"
      lose_str = f"{lose_rate}%"
      plt.text(-17,model_count[i]-0.01 ,label_list[i], color="black",fontsize=15)
      plt.text(10,model_count[i]-0.01,win_str, color="w", fontsize=15)
      plt.text(80,model_count[i]-0.01,lose_str, color="w",fontsize=15)
    plt.ylim([-0.15, 0.35])
    plt.gca().axes.yaxis.set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['left'].set_visible(False)
    # ax = plt.gca()
    # ax.axes.yaxis.set_visible(False)
    figName2 =f'/home/ubuntu/2022_VAIV_Dataset/flask/static/images/winning_rate.png'
    plt.savefig(figName2)
    plt.close()
    img = Image.open('/home/ubuntu/2022_VAIV_Dataset/flask/static/images/winning_rate.png')

    img_resize = img.resize((350, 350)) 
    img_resize.save('/home/ubuntu/2022_VAIV_Dataset/flask/static/images/winning_rate.png')
    for i in range(len(final_profit_list)):
      print(final_profit_list[i])
    #print("cuml profit : ", round(no_list[-1],3))
    final_profit_list.sort()

    result['result_profit'] = result_profit
    result['result_winning'] = result_winning

    #return round(final_profit_list[-1],2)
    result['profit'] = round(final_profit_list[-1], 2)
    print(result['profit'])
    return result

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    

    parser.add_argument('-min', '--minimum',
                        help='minimum profit when selling', type=str, required=True)
    parser.add_argument('-t', '--top',
                        help='top x of stocks', type=str, required=True)                  
    parser.add_argument('-m', '--model',
                        help='effi / vgg',nargs='+', required=True)
    parser.add_argument('-s', '--start',
                        help='start date', type=str, required=True)
    parser.add_argument('-e', '--end',
                        help='end date', type=str, required=True)
    parser.add_argument('-k', '--kos',
                        help='Kospi or Kosdaq', type=str, required=True)



    args = parser.parse_args()

    # minimum of profit
    mp = float(args.minimum)
    # top X of stock
    topX = int(args.top)
    # kospi / kosdaq
    kos = args.kos
    # model list
    m = args.model
    start_date = args.start
    end_date = args.end
    
    s_date = datetime.strptime(start_date, "%Y-%m-%d")
    e_date = datetime.strptime(end_date, "%Y-%m-%d")
    ticker_data = pd.read_csv('/home/ubuntu/2022_VAIV_Dataset/Stock_Data/Kosdaq.csv')
    if(kos == 'Kospi'):
      ticker_data = pd.read_csv('/home/ubuntu/2022_VAIV_Dataset/Stock_Data/Kospi.csv')
    
    
    ticker_list = ticker_data['Symbol'].values
    #for i in range(len(ticker_list)):
    # csv path of model
    model_list = []
    pr_list=[]
    label_list = []
    for i in range(len(m)):
      if(m[i]=='effi'):
        if(kos == 'Kospi'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSPI/new_efficient_4.csv')
          pr_list.append(0.625)
        elif(kos == 'Kosdaq'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSDAQ/new_efficient_kosdaq.csv')
          pr_list.append(0.55)
        label_list.append('EffiB7')
      elif(m[i]=='vgg'):
        if(kos == 'Kospi'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSPI/new_vgg16_4.csv')
          pr_list.append(0.625)
        elif(kos == 'Kosdaq'):
          model_list.append('/home/ubuntu/2022_VAIV_Dataset/try/predict_csv/KOSDAQ/new_vgg16_kosdaq.csv')
          pr_list.append(0.675)
        label_list.append('VGG16')

    size = 224
    fore = 5
    backtest(start_date, end_date ,model_list, fore,topX,  mp, kos,  label_list)
    
    

if __name__ == "__main__":
    main()