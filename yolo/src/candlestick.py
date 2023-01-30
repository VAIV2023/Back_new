# candlestick 차트를 만든다.
# market → ticker → pred
import matplotlib.pyplot as plt
import pandas as pd
from tqdm import tqdm
import numpy as np
from PIL import Image
from pathlib import Path
import sys
import multiprocessing as mp
import time

from manager import VAIV  # noqa: E402
from utils.mpf import candlestick_ochl, volume_overlay  # noqa: E402


def make_pixel(lines, patches, fig, stock, vaiv: VAIV):
    height = vaiv.kwargs.get('size')[1]
    xmin, xmax, ymin, ymax = [[] for i in range(4)]

    for i in range(len(stock)):
        bbox_x = patches[i].get_window_extent(fig.canvas.get_renderer())
        bbox_y = lines[i].get_window_extent(fig.canvas.get_renderer())
        xmin.append(bbox_x.x0)
        ymin.append(height-bbox_y.y1)
        xmax.append(bbox_x.x1)
        ymax.append(height-bbox_y.y0)

    dates = stock.index.tolist()

    df = pd.DataFrame({
        'Date': dates,
        'Xmin': xmin, 'Ymin': ymin,
        'Xmax': xmax, 'Ymax': ymax
    })
    df.set_index('Date', inplace=True)
    vaiv.set_df('pixel', df)
    vaiv.save_df('pixel')


def subplots(volume, MACD):
    tf = [volume, MACD]
    ax = []
    count = tf.count(True)
    if count == 0:
        ax = [111]
    elif count == 1:
        ax = [211, 212]
    else:
        ax = [211, 223, 224]
    return count, ax


def make_candlestick(vaiv: VAIV, stock, pred, pixel=True, save_dir=None):
    ticker = vaiv.kwargs.get('ticker')
    date = vaiv.kwargs.get('trade_date')
    feature = vaiv.kwargs.get('feature')
    Volume = feature.get('Volume')
    MACD = feature.get('MACD')
    MA = feature.get('MA')
    style = vaiv.kwargs.get('style')
    size = vaiv.kwargs.get('size')
    candle = vaiv.kwargs.get('candle')
    linespace = vaiv.kwargs.get('linespace')
    candlewidth = vaiv.kwargs.get('candlewidth')
    trade_date = pred['Date']

    vaiv.set_fname('png', ticker=ticker, date=date)
    if save_dir:
        vaiv.set_path(save_dir)
    else:
        vaiv.set_path(vaiv.common.image.get('images'))

    if vaiv.path.exists():
        print(vaiv.path)
        return

    dates = stock.index.tolist()
    trade_index = dates.index(trade_date)
    start_index = trade_index - 245
    end_index = trade_index - 1
    if start_index < 0:
        return
    start = dates[start_index]
    end = dates[end_index]

    try:
        c = stock.loc[start:end]
    except KeyError:
        print(ticker, pred)
        return
    plt.style.use(style)
    color = ['#0061cb', '#efbb00', '#ff4aad', '#882dff', '#2bbcff']
    num, ax = subplots(Volume, MACD)
    fig = plt.figure(figsize=(size[0]/100, size[1]/100))
    ax1 = fig.add_subplot(1, 1, 1)

    ax1.grid(False)
    ax1.set_xticklabels([])
    ax1.set_yticklabels([])
    ax1.xaxis.set_visible(False)
    ax1.yaxis.set_visible(False)
    ax1.axis('off')

    plt.tight_layout(pad=0)
    fig.set_constrained_layout_pads(w_pad=0, h_pad=0)

    t = np.arange(1, candle*linespace+1, linespace)
    quote = c[['Open', 'Close', 'High', 'Low']]
    quote.insert(0, 't', t)
    quote.reset_index(drop=True, inplace=True)

    lines, patches = candlestick_ochl(
        ax1, quote.values, width=candlewidth,
        colorup='#77d879', colordown='#db3f3f', alpha=None
    )

    if Volume:
        ax2 = fig.add_subplot(ax[1])
        bc = volume_overlay(
            ax2, c['Open'], c['Close'], c['Volume'], width=1,
            colorup='#77d879', colordown='#db3f3f', alpha=None,
        )
        ax2.add_collection(bc)
        ax2.grid(False)
        ax2.set_xticklabels([])
        ax2.set_yticklabels([])
        ax2.xaxis.set_visible(False)
        ax2.yaxis.set_visible(False)
        ax2.axis('off')

    if MACD:
        ax3 = fig.add_subplot(ax[num])
        ax3.plot(c['MACD'], linewidth=1, color='red', alpha=None)
        ax3.plot(c['MACD_Signal'], linewidth=1, color='white', alpha=None)
        ax3.grid(False)
        ax3.set_xticklabels([])
        ax3.set_yticklabels([])
        ax3.xaxis.set_visible(False)
        ax3.yaxis.set_visible(False)
        ax3.axis('off')

    if MA != [-1]:
        for m, i in zip(MA, range(len(MA))):
            ax1.plot(
                c[f'{MA}MA'], linewidth=size[1]/224,
                color=color[i], alpha=None
            )

    fig.savefig(vaiv.path)

    pil_image = Image.open(vaiv.path)
    rgb_image = pil_image.convert('RGB')
    rgb_image.save(vaiv.path)

    if pixel:
        vaiv.load_df('pixel')
        make_pixel(lines, patches, fig, c, vaiv)
    plt.close(fig)


def make_ticker_candlesticks(vaiv: VAIV, start_date, end_date):
    vaiv.load_df('stock')
    vaiv.load_df('predict')
    stock = vaiv.modedf.get('stock')
    predict = vaiv.modedf.get('predict')
    offset = vaiv.kwargs.get('offset')

    if not predict.empty:
        condition = (predict.index >= start_date) & (predict.index <= end_date)
        predict = predict.loc[condition]
        dates = predict.index.tolist()
        for i in range(0, len(dates), offset):
            trade_date = dates[i]
            pred = predict.loc[trade_date]
            vaiv.set_kwargs(trade_date=trade_date)
            make_candlestick(vaiv, stock, pred)


def make_all_candlesticks(
            vaiv: VAIV,
            start_date='2006',
            end_date='a',
            num = 968,
        ):
    market = vaiv.kwargs.get('market')
    vaiv.load_df(market)
    df = vaiv.modedf.get(market).reset_index()
    pbar = tqdm(total=len(df.Ticker.tolist()[:num]))
    for ticker in df.Ticker.tolist()[:num]:
        vaiv.set_kwargs(ticker=ticker)
        make_ticker_candlesticks(vaiv, start_date, end_date)
        pbar.update()
    pbar.close()


def update_candlestick(vaiv: VAIV):
    date = vaiv.kwargs.get('trade_date')
    vaiv.load_df('stock')
    vaiv.load_df('predict')
    stock = vaiv.modedf.get('stock')
    predict = vaiv.modedf.get('predict')

    if date in predict.index.tolist():
        pred = predict.loc[date]
        make_candlestick(vaiv, stock, pred)


def update_all_candlesticks(vaiv: VAIV, today):
    vaiv.set_kwargs(trade_date=today)
    market = vaiv.kwargs.get('market')
    vaiv.load_df(market)
    df = vaiv.modedf.get(market).reset_index()

    pbar = tqdm(total=len(df.Ticker))
    for ticker in df.Ticker:
        vaiv.set_kwargs(ticker=ticker)
        update_candlestick(vaiv)
        pbar.update()
    pbar.close()


if __name__ == '__main__':
    vaiv = VAIV(ROOT)
    kwargs = {
        'market': 'Kospi',
        'feature': {'Volume': False, 'MA': [-1], 'MACD': False},
        'offset': 10,
        'size': [1800, 650],
        'candle': 245,
        'linespace': 1,
        'candlewidth': 0.8,
        'style': 'default',
    }
    vaiv.set_kwargs(**kwargs)
    vaiv.set_stock()
    vaiv.set_prediction()
    vaiv.set_image()
    vaiv.make_dir(common=True, image=True)

    years = ['2006-', '2007-', '2008-', '2022-']
    start_mds = ['01-01', '04-01', '07-01', '10-01']
    end_mds = ['03-31', '06-30', '09-30', '12-31']
    num = 942
    jobs = []
    start = time.time()
    for year in range(2006, 2023):
        year = str(year) + '-'
        for start_md, end_md in zip(start_mds, end_mds):
            start_date = year + start_md
            end_date = year + end_md
            p = mp.Process(target=make_all_candlesticks, args=(vaiv, start_date, end_date, num, ))
            p.start()
            jobs.append(p)

    for proc in jobs:
        proc.join()

    end = time.time()
    print('Time: {0:.2f}'.format(end-start))
