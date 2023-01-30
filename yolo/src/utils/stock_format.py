'''
stock csv 파일 column 및 날짜 형식 변경
'''

from datetime import datetime
import numpy as np

column = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']


def correction(df, MAs, date_format):
    # column 맨 앞글자 대문자로
    df.columns = map(lambda x: str(x)[0].upper() + str(x)[1:], df.columns)
    # 안 쓰는 column set
    delete_col = set(df.columns) - set(column)
    for i in delete_col:  # 안 쓰는 column 삭제
        del df[i]

    if df.empty:
        return df

    # 날짜 형식 변경 %Y-%m-%d
    df.Date = df.Date.map(lambda x: correct_date(x, date_format))

    # MA, MACD, MACD Signal 추가
    if MAs != [-1]:
        df = add_MA(df, MAs)

    # df 0인 부분 제거, index 숫자 리셋
    df.replace(0, np.NaN, inplace=True)
    df.dropna(inplace=True)
    df.set_index('Date', inplace=True)

    return df


def correct_date(date, date_format):
    date = str(date)
    date_time = datetime.strptime(date, date_format)
    date = date_time.strftime("%Y-%m-%d")
    return date


def add_MA(df, MAs):
    # MA column 추가 (단순 이동 평균)
    for ma in MAs:
        df[f'{ma}MA'] = df['Close'].rolling(ma).mean()

    # MACD, MACD Signal 추가 (지수 이동 평균)
    ema_12 = df['Close'].ewm(span=12).mean()
    ema_26 = df['Close'].ewm(span=26).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()

    return df
