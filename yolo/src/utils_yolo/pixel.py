from pathlib import Path
import pandas as pd
import sys
p = Path('/home/ubuntu/Back_new/yolo/src')
from stock_2 import Stock  # Modify Path


class StockImage:
    def __init__(self, path):
        p = Path(path)
        print(p)
        file_name = p.stem
        ticker, last_date = file_name.split('_')[:2]
        self.ticker = ticker
        self.date = last_date
        
        try:
            i = p.parts.index('images')
            parts = list(p.parts)
            parts[i] = 'dataframes'
            lpath = Path(*parts).with_suffix('.csv')
            labeling = pd.read_csv(lpath)
            self.labeling = labeling
        except FileNotFoundError:
            pass
        try:
            i = p.parts.index('images')
            parts = list(p.parts)
            parts[i] = 'pixels'
            pixelPath = Path(*parts).with_suffix('.csv')
            pixel = pd.read_csv(pixelPath, index_col=0)
            self.pixel = pixel
        except FileNotFoundError:
            print("fileNotFoundError in pixel!!!!")
            pass
        
        self.stock = Stock(ticker, root=(Path.cwd().parent / 'Data')).load_data()
        self.ticker = ticker
        self.last_date = last_date


    def get_box_date(self, xmin, xmax):
        pixels = self.pixel.to_dict('index')
        dates = []
        for date, pixel in pixels.items():
            pix_min = pixel['Xmin']
            pix_max = pixel['Xmax']
            i = min(pix_max, xmax) - max(pix_min, xmin)
            w = pix_max - pix_min
            if i / w > 0.2:
                dates.append(date)
        return dates

    def get_last_date(self, dates):
        try:
            end = dates[-1]
        except IndexError:
            print(self.ticker, self.last_date, dates)
            return None
        after = self.pixel.index[self.pixel.index > end].tolist()
        if len(after) == 0:
            return self.last_date
        else:
            return after[0]

    def get_trade_close(self, date):
        try:
            close = self.stock.loc[date, 'Close']
        except KeyError:
            close = 0
        return close

    def get_pixel(self, i):
        try:
            pix_min = self.pixel.Xmin.iloc[i]
            pix_max = self.pixel.Xmax.iloc[i]
        except IndexError:
            print(i)
            print(self.pixel)
            print(self.ticker)
            print(self.last_date)
            exit()
        return pix_min, pix_max

    def last_signal(self, xmin, xmax, date_thres):
        index = [-i for i in range(1, date_thres+1)]
        for i in index:
            pix_min, pix_max = self.get_pixel(i)
            i = min(pix_max, xmax) - max(pix_min, xmin)
            w = pix_max - pix_min
            if i / w > 0.2:
                return True
        return False

    def minmaxTrue(self, drange, LRange, label):
        Ltrade = self.stock.loc[LRange]
        trade = self.stock.loc[drange]
        if label == 1:
            Ldate = Ltrade.Close.idxmin()
            date = trade.Close.idxmin()
        else:
            Ldate = Ltrade.Close.idxmax()
            date = trade.Close.idxmax()
        return int(Ldate == date)

    def patternTrue(self, drange, Ldrange):
        intersection = list(set(drange).intersection(Ldrange))
        return len(intersection) == len(Ldrange)

    def rowTrue(self, drange, LRange, label, row):
        if 'Priority' in row.keys():
            return self.minmaxTrue(drange, LRange, label)
        else:
            return self.patternTrue(drange, LRange)

    def TFPN(self, drange, label):
        labeling = self.labeling[self.labeling.Label == label.item()]

        dates = self.stock.index.tolist()
        MaxRange = []
        Maxrow = {}
        for row in labeling.to_dict('records'):
            Ldrange = row['Range'].split('/')
            # print(Ldrange)
            if IoU(drange, MaxRange) <= IoU(drange, Ldrange):
                MaxRange = Ldrange
                Maxrow = row
        iou = IoU(drange, MaxRange)

        if iou > 0:
            Ltrade = max(MaxRange)
            trade = max(drange)
            Ltrade_close = self.stock.loc[Ltrade]['Close']
            trade_close = self.stock.loc[trade]['Close']
            date_diff = dates.index(trade) - dates.index(Ltrade)
            close_diff = round(((trade_close - Ltrade_close) / Ltrade_close) * 100, 2)
        else:
            date_diff = 0
            close_diff = 0
            # print('Trade: ', date_diff, close_diff)
        T = self.rowTrue(drange, MaxRange, label, Maxrow)
        return iou, date_diff, close_diff, T


def IoU(drange, Ldrange):
    intersection = list(set(drange).intersection(Ldrange))
    union = list(set().union(drange, Ldrange))
    IoU = len(intersection) / len(union)
    return round(IoU, 2)