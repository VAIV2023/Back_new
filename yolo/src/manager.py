'''
VAIV 폴더의 전반적인 Path를 관리하는 코드다
'''

import pandas as pd
from pathlib import Path


class FileManager:
    def set_fname(self, extension, **kwargs):
        values = '_'.join(kwargs.values())
        self.fname = f'{values}.{extension}'

    def set_path(self, dir):
        self.path = dir / self.fname

    def load_df(self, empty: dict, index=None, index_col=None):
        try:
            self.df = pd.read_csv(self.path, index_col=index_col)
        except FileNotFoundError:
            self.df = pd.DataFrame(empty)
        if index:
            self.df.set_index(index, inplace=True)

    def set_df(self, df):
        self.df = df

    def save_df(self):
        self.df.to_csv(self.path)


class CNN:  # CNN 폴더 관리
    def __init__(self, vaiv):
        '''
        CNN
          ㄴLabeling
          ㄴDataset
          ㄴCode
        '''
        self.root = vaiv / 'CNN'
        self.top = {
            'labeling': self.root / 'Labeling',
            'dataset': self.root / 'Dataset',
            'code': self.root / 'Code'
        }

    def set_labeling(self, offset, market):  # 레이블링 폴더 세팅
        '''
        labeling = str # labeling 이름 ex) '4%_01_2'
        forecast = int # 며칠 후를 예측할지 (= forecast interval)

        Labeling
          ㄴ{offset}
            ㄴ{market}
        '''
        self.offset = offset
        self.market = market

        self.labeling = self.top['labeling'] / str(offset) / market

    def set_dataset(self, name):  # 데이터셋 폴더 세팅
        '''
        Dataset
          ㄴ{name}
            ㄴ images
              ㄴtrain / valid / test
            ㄴ labels
        '''
        self.output = self.top['dataset'] / name
        images = self.output / 'images'
        labels = self.output / 'labels'

        self.dataset = {
            'images': {
                'train': images / 'train',
                'valid': images / 'valid',
                'test': images / 'test'
            },
            'labels': labels
        }

    # cnn폴더 내부에 폴더들 생성
    def make_cnn(self, labeling=None, dataset=None):
        for cnn in self.top.values():
            cnn.mkdir(parents=True, exist_ok=True)

        if labeling:
            self.labeling.mkdir(parents=True, exist_ok=True)
        if dataset:
            for image in self.dataset['images'].values():
                image.mkdir(parents=True, exist_ok=True)
            self.dataset['labels'].mkdir(parents=True, exist_ok=True)


class Yolo:  # Yolo 폴더 관리
    def __init__(self, vaiv):
        '''
        Yolo
          ㄴDataset
          ㄴLabeling
          ㄴCode
        '''
        self.root = vaiv / 'Yolo'
        self.top = {
            'dataset': self.root / 'Dataset',
            'labeling': self.root / 'Labeling',
            'code': self.root / 'Code'
        }

    # 데이터셋 폴더 세팅
    def set_dataset(self, name):
        '''
        Dataset
          ㄴ{name}
            ㄴimages
              ㄴtrain / valid / test
            ㄴlabels
              ㄴtrain / valid / test
        '''
        output = self.top['dataset'] / name
        train = output / 'train'
        valid = output / 'valid'
        test = output / 'test'

        self.dataset = {
            'train': {
                'labels': train / 'labels',
                'images': train / 'images',
                'dataframes': train / 'dataframes',
            },
            'valid': {
                'labels': valid / 'labels',
                'images': valid / 'images',
                'dataframes': valid / 'dataframes',
            },
            'test': {
                'labels': test / 'labels',
                'images': test / 'images',
                'dataframes': test / 'dataframes',
            },
        }


    def set_labeling(self, market, name):
        '''
        Labeling
          ㄴ{market}
            ㄴ{name}
              ㄴMinMax
              ㄴPattern
              ㄴMerge
        '''
        parent = self.top.get('labeling') / market / name
        self.labeling = {
            'pattern': parent / 'Pattern',
            'min_max': parent / 'MinMax',
            'merge': parent / 'Merge',
        }

    # Yolo폴더 내부에 폴더들 생성
    def make_yolo(
        self,
        dataset=None,
        labeling=None,
        signal=True,
    ):
        for yolo in self.top.values():
            yolo.mkdir(parents=True, exist_ok=True)

        if dataset:
            for k,v in self.dataset.items():
                for p in v.values():
                    p.mkdir(parents=True, exist_ok=True)

        if labeling:
            for label in self.labeling.values():
                label.mkdir(parents=True, exist_ok=True)


class Common:  # Common 폴더 관리
    def __init__(self, vaiv):
        '''
        Common
          ㄴStock
          ㄴPrediction
          ㄴImage
          ㄴServer
          ㄴModel
          ㄴCode
        '''
        self.root = vaiv / 'Common'
        self.top = {
            'stock': self.root / 'Stock',
            'predict': self.root / 'Prediction',
            'image': self.root / 'Image',
            'server': self.root / 'Server',
            'model': self.root / 'Model',
            'code': self.root / 'Code'
        }

        self.candidate = ['Candle', 'Vol', 'MA', 'Vol_MA',
                          'MACD', 'Vol_MACD', 'MA_MACD', 'Vol_MA_MACD']

    def set_stock(self, market):
        '''
        Stock
          ㄴ{market}
        '''
        self.market = market
        self.stock = self.top['stock'] / self.market

    # Prediction 폴더 세팅 -> 예측일 기준으로 필요한 정보 담김
    def set_prediction(self, candle, market):
        '''
        Prediction
          ㄴ{candle}
            ㄴ{market}
        '''
        self.pred = self.top['predict'] / str(candle) / market

    # 차트 이미지 폴더 세팅
    def set_image(
        self,
        feature: dict,  # {'Volume': bool, 'MA': [int], 'MACD': bool}
        offset: int,  # 거래일 간격
        market: str,  # 주식 시장
        style: str,  # background 색깔
        size: list,  # [width, height]
        candle: int,  # 캔들 개수
        linespace: float,  # 캔들 간격
        candlewidth: float  # 캔들 두께
    ):
        '''
        Image
          ㄴ {feature}
            ㄴ {style}
              ㄴ {width}x{height}_{candle}_{linespace}_{candlewidth}
                ㄴ {offset}
                  ㄴ{market}
                    ㄴimages
                    ㄴpixels
        '''
        f = 0
        if feature['Volume']:  # volume 있을 때
            f += 1
        if feature['MA'] != [-1]:  # ma 있을 때
            f += 2
        if feature['MACD']:  # macd 있을 때
            f += 4
        f = self.candidate[f]

        root = self.top['image']
        set = f'{size[0]}x{size[1]}_{candle}_{linespace}_{candlewidth}'
        folder = root / f / style / str(offset) / set / market

        self.image = {
            'images': folder / 'images',
            'pixels': folder / 'pixels'
        }

    def set_server(self, server):
        '''
        Server
          ㄴ{app} # MakeDataset, Simulator
            ㄴtemplates
            ㄴstatic
        '''
        self.seroot = self.top['server'] / server
        self.server = {
            'templates': self.seroot / 'templates',
            'static': self.seroot / 'static'
        }

    # Common폴더 내부에 폴더들 생성
    def make_common(
        self,
        stock=None,
        prediction=None,
        image=None,
        server=None
    ):
        for common in self.top.values():
            common.mkdir(parents=True, exist_ok=True)

        for ft in self.candidate:
            (self.top['image'] / ft).mkdir(parents=True, exist_ok=True)

        if prediction:
            self.pred.mkdir(parents=True, exist_ok=True)

        if image:
            self.image['images'].mkdir(parents=True, exist_ok=True)
            self.image['pixels'].mkdir(parents=True, exist_ok=True)

        if server:
            self.server['templates'].mkdir(parents=True, exist_ok=True)
            self.server['static'].mkdir(parents=True, exist_ok=True)

        if stock:
            self.stock.mkdir(parents=True, exist_ok=True)


class VAIV(FileManager):
    def __init__(self, vaiv):
        self.vaiv = Path(vaiv)

        self.cnn = CNN(self.vaiv)
        self.yolo = Yolo(self.vaiv)
        self.common = Common(self.vaiv)
        self.kwargs = {}

        # DataFrame들
        self.modedf = {
            'label': None,
            'train': None, 'valid': None, 'test': None,
            'pixel': None,
            'predict': None,
            'signal': None, 'total': None,
            'info': None,
            'stock': None,
            'Kospi': None, 'Kosdaq': None,
        }

        # Load한 DataFrame Path들
        self.load = {
            'label': None,
            'train': None, 'valid': None, 'test': None,
            'pixel': None,
            'predict': None,
            'signal': None, 'total': None,
            'info': None,
            'stock': None,
            'Kospi': None, 'Kosdaq': None,
        }

    def set_kwargs(self, **kwargs):
        for k, v in kwargs.items():
            self.kwargs[k] = v

    def load_df(self, mode):
        '''
        [kwargs]
        label: 'ticker', 'trade_date'
        train / valid / test: None
        info: 'folder'
        pixel: 'ticker', 'trade_date'
        signal: 'ticker'
        total: None
        predict: 'ticker'
        stock: 'ticker'
        Kospi / Kosdaq: None
        '''
        index = None
        index_col = None
        if mode == 'label':
            empty = {'Date': [], 'Ticker': [], 'Label': []}
            ticker = self.kwargs['ticker']
            trade_date = self.kwargs['trade_date']
            self.set_fname('csv', ticker=ticker, trade_date=trade_date)
            self.set_path(self.cnn.labeling)

        elif (mode == 'train') or (mode == 'valid') or (mode == 'test'):
            empty = {'Date': [], 'Ticker': [], 'Label': []}
            self.set_fname('csv', mode=mode)
            self.set_path(self.cnn.dataset['labels'])

        elif mode == 'info':
            folder = self.kwargs['folder']
            self.set_fname('csv', mode=mode)
            if folder == 'cnn':
                empty = {'Name': [], 'Image': [], 'Labeling': [],
                         'Market': [], 'Train': [], 'Valid': [], 'Test': []}
                self.set_path(self.cnn.top['dataset'])
            elif folder == 'yolo':
                empty = {'Name': [], 'Image': [], 'Market': [],
                         'Train': [], 'Valid': [], 'Test': []}
                self.set_path(self.yolo.top['dataset'])

        elif mode == 'pixel':
            empty = {
                'Date': [],
                'Xmin': [], 'Xmax': [],
                'Ymin': [], 'Ymax': [],
            }
            ticker = self.kwargs['ticker']
            trade_date = self.kwargs['trade_date']
            self.set_fname('csv', ticker=ticker, trade_date=trade_date)
            self.set_path(self.common.image['pixels'])
            index = 'Date'

        elif mode == 'signal':
            empty = {'Date': [], 'Ticker': [], 'Label': [],
                     'Probability': [], 'Range': [], 'Detect': []}
            ticker = self.kwargs['ticker']
            self.set_fname('csv', ticker=ticker)
            self.set_path(self.yolo.signals)

        elif mode == 'total':
            empty = {'Date': [], 'Ticker': [], 'Label': [],
                     'Probability': [], 'Range': [], 'Detect': []}
            self.set_fname('csv', mode=mode)
            self.set_path(self.yolo.signals)

        elif mode == 'predict':
            empty = {'Date': [], 'Start': [], 'End': []}
            ticker = self.kwargs['ticker']
            self.set_fname('csv', ticker=ticker)
            self.set_path(self.common.pred)
            index = 'Date'

        elif mode == 'stock':
            empty = {
                'Date': [],
                'Open': [], 'Close': [],
                'High': [], 'Low': [],
                'Volume': []
            }
            ticker = self.kwargs['ticker']
            self.set_fname('csv', ticker=ticker)
            self.set_path(self.common.stock)
            index = 'Date'

        elif (mode == 'Kospi') or (mode == 'Kosdaq'):
            empty = {'Ticker': [], 'Name': []}
            self.set_fname('csv', market=mode)
            self.set_path(self.common.top['stock'])
            index_col = 0

        elif mode=='pattern':
            ticker = self.kwargs.get('ticker')
            trade_date = self.kwargs.get('trade_date')
            empty = {'Label': [], 'Range': [], 'Pattern': []}
            self.set_fname('csv', ticker=ticker, trade_date=trade_date)
            self.set_path(self.yolo.labeling.get(mode))
            index = 'Label'

        elif mode=='min_max':
            ticker = self.kwargs.get('ticker')
            trade_date = self.kwargs.get('trade_date')
            empty = {'Label': [], 'Date': [], 'Priority': []}
            self.set_fname('csv', ticker=ticker, trade_date=trade_date)
            self.set_path(self.yolo.labeling.get(mode))
            index = 'Label'

        elif mode=='merge':
            ticker = self.kwargs.get('ticker')
            trade_date = self.kwargs.get('trade_date')
            empty = {'Label': [], 'CenterX': [], 'CenterY': [], 'Width': [], 'Height': [], 'Pattern': [], 'Priority': []}
            self.set_fname('csv', ticker=ticker, trade_date=trade_date)
            self.set_path(self.yolo.labeling.get(mode))

        else:
            return

        self.load[mode] = self.path
        super().load_df(empty, index=index, index_col=index_col)
        self.modedf[mode] = self.df

    def set_df(self, mode, df):
        super().set_df(df)
        self.modedf[mode] = self.df

    def save_df(self, mode):
        self.path = self.load[mode]
        self.df = self.modedf.get(mode)
        super().save_df()

    def set_image(self, p=None):
        style = self.kwargs.get('style')
        offset = self.kwargs.get('offset')
        market = self.kwargs.get('market')
        size = self.kwargs.get('size')
        candle = self.kwargs.get('candle')
        feature = self.kwargs.get('feature')
        linespace = self.kwargs.get('linespace')
        candlewidth = self.kwargs.get('candlewidth')

        if p:
            self.common.top['image'] = p
        self.common.set_image(
            feature, offset,
            market, style,
            size, candle,
            linespace, candlewidth,
        )

    def set_labeling(self):
        folder = self.kwargs.get('folder')
        market = self.kwargs.get('market')

        if folder == 'cnn':
            offset = self.kwargs.get('offset')
            self.cnn.set_labeling(offset, market)
        elif folder == 'yolo':
            name = self.kwargs.get('name')
            self.yolo.set_labeling(market, name)

    def set_dataset(self):
        '''
        folder: 'cnn' 또는 'Yolo' 폴더
        '''
        name = self.kwargs.get('name')
        folder = self.kwargs.get('folder')

        if folder == 'cnn':
            self.cnn.set_dataset(name)
        elif folder == 'yolo':
            self.yolo.set_dataset(name)
        else:
            print('There is no such folder')

    def set_prediction(self):
        candle = self.kwargs.get('candle')
        market = self.kwargs.get('market')
        self.common.set_prediction(candle, market)

    def set_stock(self):
        market = self.kwargs.get('market')
        self.common.set_stock(market)

    def set_server(self):
        server = self.kwargs.get('server')
        self.common.set_server(server)

    def make_dir(
        self,
        cnn=None, labeling=None, dataset=None,
        yolo=None, signal=True,
        common=None, stock=None, prediction=None, image=None, server=None
    ):
        if cnn:
            self.cnn.make_cnn(
                labeling=labeling,
                dataset=dataset
            )
        if yolo:
            self.yolo.make_yolo(dataset=dataset, labeling=labeling, signal=signal)
        if common:
            self.common.make_common(
                stock=stock,
                prediction=prediction,
                image=image,
                server=server
            )


if __name__ == '__main__':
    ROOT = Path('/home/ubuntu/2022_VAIV_Cho/VAIV')
    vaiv = VAIV(ROOT)
    vaiv.make_dir(cnn=True, yolo=True, common=True)
