from demo import yolo_buy
import pandas as pd
from find_sell import detect_all

# 전종목 티커 가져오기
stock_df = pd.read_csv("/home/ubuntu/Back_new/static/Stock.csv", index_col=0)
KOSPI_df = stock_df.loc[stock_df['Market'] == 'STK']
KOSDAQ_df = stock_df.loc[stock_df['Market'] == 'KSQ']

kospi_list = KOSPI_df.index.to_list()
kosdaq_list = KOSDAQ_df.index.to_list()

print(f"ticker list : {kospi_list}")
#detect_all("2022-12-01")
print("\n---Detection start---")
print(yolo_buy(['095570', '027410', '282330'], '2022-11-25', 'KOSPI'))