import argparse
import time
from pathlib import Path

import cv2
import torch
from tqdm import tqdm
import pandas as pd
import sys

import random
from datetime import datetime
from datetime import timedelta
# from datetime import date

from models.experimental import attempt_load
from utils_yolo.datasets import LoadImages, LoadFilesImages
from utils_yolo.general import check_img_size, non_max_suppression, \
    apply_classifier, scale_coords, xyxy2xywh, \
    set_logging, increment_path
from utils_yolo.plots import plot_one_box
from utils_yolo.pixel import StockImage
from utils_yolo.torch_utils import select_device, load_classifier, \
    TracedModel

ROOT = Path('/home/ubuntu/Back_new/yolo')

from manager import VAIV  # noqa: E402

def detect_only_cpu(
            weights='../weights_KOSPI50/best.pt',
            source='inference/images',
            files=None,     # detect 할 이미지
            imgsz=640,
            conf_thres=0,
            iou_thres=0.45,
            device='',
            trace=False,
            model=None,
            vaiv=VAIV(ROOT),
            save_dir=Path('/home/ubuntu/Back_new/static/predict')
        ):
        
    # Initialize
    #device = select_device(device)
    #half = device.type != 'cpu'  # half precision only supported on CUDA
    device = torch.device('cpu')

    (save_dir).mkdir(parents=True, exist_ok=True)

    # Load model
    if not model:
        model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size
    if trace:
        print("trace???")
        model = TracedModel(model, device, imgsz)

    # if half:
    #     model.half()  # to FP16

    # Set Dataloader
    # source = source.strip()
    if not files:
        dataset = LoadImages(source, img_size=imgsz, stride=stride)
    else:
        dataset = LoadFilesImages(files, img_size=imgsz, stride=stride)
    # Get names and colors
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[121, 216, 119], [63, 63, 219], [128, 128, 128]]

    # Run inference
    print(f"device type : {device.type}")
    if device.type != 'cpu':
        model(
            torch.zeros(
                1, 3, imgsz, imgsz
            ).to(device).type_as(next(model.parameters()))
        )  # run once
    # t0 = time.time()

    df_list = []
    for path, img, im0s in (dataset):
        # 각 이미지마다 진행
        stockimg = StockImage(path, vaiv)
        # box = {}  # trade_date: df
        probability = 0
        # is_signal = False

        new_df = pd.DataFrame({
            'Ticker': [stockimg.ticker],
            'Signal': ['hold'],
            'Probability': [0],
            'Start': [''],
            'End': [''],
        })

        img = torch.from_numpy(img).to(device)
        #img = img.half() if half else img.float()  # uint8 to fp16/32
        img = img.float()
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = model(img)[0]
        print({f"length of pred : {len(pred)}"})

        # Apply NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres)
        
        # Process detections
        for i, det in enumerate(pred):  # detections per image
            p, s, im0 = path, '', im0s

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)
            s += '%gx%g ' % img.shape[2:]  # print string
            # normalization gain whwh
            # gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]

            if len(det):
                print(det)
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(
                    img.shape[2:], det[:, :4], im0.shape
                ).round()
                print(det)

                # Write results

                for *xyxy, conf, cls in reversed(det):
                    # 각 박스마다 기록
                    pixel_col = torch.tensor(xyxy).cpu().detach().numpy()
                    xmin, xmax = pixel_col[0], pixel_col[2]
                    signal = names[int(cls)]

                    probability = round(float(conf), 3)
                    if stockimg.last_signal(xmin, xmax, 1):
                        dates = stockimg.get_box_date(xmin, xmax)
                        # print('Last: ', dates)
                        new_df = pd.DataFrame({
                            'Ticker': [stockimg.ticker],
                            'Signal': [signal],
                            'Probability': [probability],
                            'Start': [dates[0]],
                            'End': [dates[-1]],
                        })

                        label = f'{names[int(cls)]} {conf:.2f}'
                        plot_one_box(
                            xyxy, im0, label=label,
                            color=colors[int(cls)],
                            line_thickness=2
                        )
                        break

        df_list.append(new_df)
        cv2.imwrite(save_path, im0)

    df = pd.concat(df_list)
    return df



def detect_light(
            weights='../weights_KOSPI50/best.pt',
            source='inference/images',
            files=None,     # detect 할 이미지
            imgsz=640,
            conf_thres=0,
            iou_thres=0.45,
            device='',
            trace=False,
            model=None,
            vaiv=VAIV(ROOT),
            save_dir=Path('/home/ubuntu/Back_new/static/predict')
        ):
        
    # Initialize
    device = select_device(device)
    half = device.type != 'cpu'  # half precision only supported on CUDA

    (save_dir).mkdir(parents=True, exist_ok=True)

    # Load model
    if not model:
        model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size
    if trace:
        model = TracedModel(model, device, imgsz)

    if half:
        model.half()  # to FP16

    # Set Dataloader
    # source = source.strip()
    if not files:
        dataset = LoadImages(source, img_size=imgsz, stride=stride)
    else:
        dataset = LoadFilesImages(files, img_size=imgsz, stride=stride)
    # Get names and colors
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[121, 216, 119], [63, 63, 219], [128, 128, 128]]

    # Run inference
    if device.type != 'cpu':
        model(
            torch.zeros(
                1, 3, imgsz, imgsz
            ).to(device).type_as(next(model.parameters()))
        )  # run once
    # t0 = time.time()

    df_list = []
    for path, img, im0s in (dataset):
        # 각 이미지마다 진행
        stockimg = StockImage(path, vaiv)
        # box = {}  # trade_date: df
        probability = 0
        # is_signal = False

        new_df = pd.DataFrame({
            'Ticker': [stockimg.ticker],
            'Signal': ['hold'],
            'Probability': [0],
            'Start': [''],
            'End': [''],
        })

        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = model(img)[0]
        print({f"length of pred : {len(pred)}"})

        # Apply NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres)
        
        # Process detections
        for i, det in enumerate(pred):  # detections per image
            p, s, im0 = path, '', im0s

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)
            s += '%gx%g ' % img.shape[2:]  # print string
            # normalization gain whwh
            # gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
            print("!!")
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(
                    img.shape[2:], det[:, :4], im0.shape
                ).round()
                print(det)

                # Write results

                for *xyxy, conf, cls in reversed(det):
                    # 각 박스마다 기록
                    pixel_col = torch.tensor(xyxy).cpu().detach().numpy()
                    xmin, xmax = pixel_col[0], pixel_col[2]
                    signal = names[int(cls)]

                    probability = round(float(conf), 3)
                    if stockimg.last_signal(xmin, xmax, 1):
                        dates = stockimg.get_box_date(xmin, xmax)
                        # print('Last: ', dates)
                        new_df = pd.DataFrame({
                            'Ticker': [stockimg.ticker],
                            'Signal': [signal],
                            'Probability': [probability],
                            'Start': [dates[0]],
                            'End': [dates[-1]],
                        })

                        label = f'{names[int(cls)]} {conf:.2f}'
                        plot_one_box(
                            xyxy, im0, label=label,
                            color=colors[int(cls)],
                            line_thickness=2
                        )
                        break

        df_list.append(new_df)
        cv2.imwrite(save_path, im0)

    df = pd.concat(df_list)
    return df


def detect(
            pair=0,
            save_img=True,
            weights='yolov7.pt',
            source='inference/images',
            imgsz=640,
            conf_thres=0,
            iou_thres=0.45,
            device='',
            save_txt=False,
            project='runs/detect',
            name='exp',
            exist_ok=False,
            trace=True,
            vaiv=VAIV(ROOT)
        ):

    # Directories
    save_dir = Path(increment_path(Path(project) / name, exist_ok=exist_ok))
    (save_dir / 'labels' if save_txt else save_dir).mkdir(
        parents=True, exist_ok=True
    )  # make dir
    (save_dir / 'signals').mkdir(parents=True, exist_ok=True)
    (save_dir / 'images').mkdir(parents=True, exist_ok=True)

    # Initialize
    set_logging()
    device = select_device(device)
    half = device.type != 'cpu'  # half precision only supported on CUDA

    # Load model
    model = attempt_load(weights, map_location=device)  # load FP32 model
    stride = int(model.stride.max())  # model stride
    imgsz = check_img_size(imgsz, s=stride)  # check img_size

    if trace:
        model = TracedModel(model, device, imgsz)

    if half:
        model.half()  # to FP16

    # Second-stage classifier
    classify = False
    if classify:
        modelc = load_classifier(name='resnet101', n=2)  # initialize
        modelc.load_state_dict(
            torch.load('weights/resnet101.pt', map_location=device)['model']
        ).to(device).eval()

    # Set Dataloader
    source = source.strip()
    dataset = LoadImages(source, img_size=imgsz, stride=stride)

    # Get names and colors
    names = model.module.names if hasattr(model, 'module') else model.names
    colors = [[random.randint(0, 255) for _ in range(3)] for _ in names]

    # Run inference
    if device.type != 'cpu':
        model(
            torch.zeros(
                1, 3, imgsz, imgsz
            ).to(device).type_as(next(model.parameters()))
        )  # run once
    t0 = time.time()

    signals = {}  # ticker: box
    pbar = tqdm(total=len(dataset))
    for path, img, im0s in dataset:
        # 각 이미지마다 진행
        stockimg = StockImage(path, vaiv)
        if stockimg.get_trade_close(stockimg.trade_date) == 0:
            continue
        box = {}  # trade_date: df
        if stockimg.ticker not in signals:
            signals[stockimg.ticker] = box
        probability = 0
        is_signal = False

        img = torch.from_numpy(img).to(device)
        img = img.half() if half else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # Inference
        pred = model(img)[0]

        # Apply NMS
        pred = non_max_suppression(pred, conf_thres, iou_thres)

        # Apply Classifier
        if classify:
            pred = apply_classifier(pred, modelc, img, im0s)

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            check = 0

            p, s, im0 = path, '', im0s

            p = Path(p)  # to Path
            save_path = str(save_dir / 'images' / p.name)  # img.jpg
            txt_path = str(save_dir / 'labels' / p.stem)  # img.txt
            s += '%gx%g ' % img.shape[2:]  # print string
            # normalization gain whwh
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_coords(
                    img.shape[2:], det[:, :4], im0.shape
                ).round()

                # Print results
                for c in det[:, -1].unique():
                    n = (det[:, -1] == c).sum()  # detections per class
                    # add to string
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "
                # Write results

                for *xyxy, conf, cls in reversed(det):
                    # 각 박스마다 기록
                    pixel_col = torch.tensor(xyxy).cpu().detach().numpy()
                    xmin, xmax = pixel_col[0], pixel_col[2]
                    dates = stockimg.get_box_date(xmin, xmax)
                    if len(dates) == 0:
                        print(stockimg.ticker, stockimg.trade_date, pixel_col)
                        continue
                    signal = names[int(cls)]

                    # Here the conditions change based on the 'pairs' input

                    if pair == 0:
                        probability = round(float(conf), 3)
                        trade_date = stockimg.get_trade_date(dates)
                        close = stockimg.get_trade_close(trade_date)
                        df = signals[stockimg.ticker].get(trade_date)

                        if df is None:
                            signals[stockimg.ticker][trade_date] = pd.DataFrame({
                                'Ticker': [stockimg.ticker],
                                'Date': [trade_date],
                                'Label': [signal],
                                'Close': [close],
                                'Probability': [probability],
                                'Range': ['/'.join(dates)],
                                'Detect': [stockimg.trade_date]
                            })
                            if stockimg.last_signal(xmin, xmax, 3):
                                is_signal = True
                        else:
                            if df.Label[0] != signal:
                                signals[stockimg.ticker].pop(trade_date)
                                is_signal = False

                        if save_txt and is_signal:  # Write to file
                            xywh = (
                                xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn
                            ).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf)
                            with open(txt_path + '.txt', 'a') as f:
                                f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        if save_img:  # Add bbox to image
                            label = f'{names[int(cls)]} {conf:.2f}'
                            plot_one_box(
                                xyxy, im0, label=label,
                                color=colors[int(cls)],
                                line_thickness=2
                            )

                    if pair == 1 and signal == "buy":
                        probability = round(float(conf), 3)
                        trade_date = stockimg.get_trade_date(dates)
                        close = stockimg.get_trade_close(trade_date)
                        df = signals[stockimg.ticker].get(trade_date)

                        # This is where we get the close price of five days later
                        begin_date = datetime.strptime(trade_date, "%Y-%m-%d")
                        five_days_later = begin_date + timedelta(days=5)

                    #    five_days_later = stockimg.stock[begin_date + timedelta(days=5)]

                    #    date_list = stockimg.stock[date]

                        five_days_later_price = stockimg.get_trade_close(five_days_later.strftime('%Y-%m-%d'))

                        end_date = five_days_later.strftime('%Y-%m-%d')

                        if five_days_later_price == 0:
                            five_days_later_price = stockimg.get_trade_close((begin_date + timedelta(days=6)).strftime('%Y-%m-%d'))
                            end_date = (begin_date + timedelta(days=6)).strftime('%Y-%m-%d')
                            if five_days_later_price == 0:
                                five_days_later_price = stockimg.get_trade_close((begin_date + timedelta(days=7)).strftime('%Y-%m-%d'))
                                end_date = (begin_date + timedelta(days=7)).strftime('%Y-%m-%d')
                                if five_days_later_price == 0:
                                    five_days_later_price = stockimg.get_trade_close((begin_date + timedelta(days=8)).strftime('%Y-%m-%d'))
                                    end_date = (begin_date + timedelta(days=8)).strftime('%Y-%m-%d')
                                    if five_days_later_price == 0:
                                        end_date = (begin_date + timedelta(days=8)).strftime('%Y-%m-%d')
                                        five_days_later_price = stockimg.get_trade_close((begin_date + timedelta(days=9)).strftime('%Y-%m-%d'))
                                        if five_days_later_price == 0:
                                            end_date = (begin_date + timedelta(days=10)).strftime('%Y-%m-%d')
                                            five_days_later_price = stockimg.get_trade_close((begin_date + timedelta(days=10)).strftime('%Y-%m-%d'))

                        # End

                        if df is None:
                            signals[stockimg.ticker][trade_date] = pd.DataFrame({
                                'Ticker': [stockimg.ticker],
                                'Date': [trade_date],
                                'Label': [signal],
                                'Close': [close],
                                'Probability': [probability],
                                'Range': ['/'.join(dates)],
                                'Detect': [stockimg.trade_date],
                                'Five': [five_days_later_price],
                                'End': [end_date]
                            })
                            if stockimg.last_signal(xmin, xmax, 3):
                                is_signal = True
                        else:
                            if df.Label[0] != signal:
                                signals[stockimg.ticker].pop(trade_date)
                                is_signal = False

                        if save_txt and is_signal:  # Write to file
                            xywh = (
                                xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn
                            ).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf)
                            with open(txt_path + '.txt', 'a') as f:
                                f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        if save_img:  # Add bbox to image
                            label = f'{names[int(cls)]} {conf:.2f}'
                            plot_one_box(
                                xyxy, im0, label=label,
                                color=colors[int(cls)],
                                line_thickness=2
                            )
                    elif pair == 2 and signal == "sell":
                        probability = round(float(conf), 3)
                        trade_date = stockimg.get_trade_date(dates)
                        close = stockimg.get_trade_close(trade_date)
                        df = signals[stockimg.ticker].get(trade_date)

                        if df is None:
                            signals[stockimg.ticker][trade_date] = pd.DataFrame({
                                'Ticker': [stockimg.ticker],
                                'Date': [trade_date],
                                'Label': [signal],
                                'Close': [close],
                                'Probability': [probability],
                                'Range': ['/'.join(dates)],
                                'Detect': [stockimg.trade_date]
                            })
                            if stockimg.last_signal(xmin, xmax, 3):
                                is_signal = True
                        else:
                            if df.Label[0] != signal:
                                signals[stockimg.ticker].pop(trade_date)
                                is_signal = False

                        if save_txt and is_signal:  # Write to file
                            xywh = (
                                xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn
                            ).view(-1).tolist()  # normalized xywh
                            line = (cls, *xywh, conf)
                            with open(txt_path + '.txt', 'a') as f:
                                f.write(('%g ' * len(line)).rstrip() % line + '\n')

                        if save_img:  # Add bbox to image
                            label = f'{names[int(cls)]} {conf:.2f}'
                            plot_one_box(
                                xyxy, im0, label=label,
                                color=colors[int(cls)],
                                line_thickness=2
                            )
                    elif pair == 3:
                        if signal == "buy":
                            if check == 1:
                                print("skip buy")
                                continue

                            elif check == 0:
                                check = 1

                                probability = round(float(conf), 3)
                                trade_date = stockimg.get_trade_date(dates)
                                close = stockimg.get_trade_close(trade_date)
                                df = signals[stockimg.ticker].get(trade_date)

                                if df is None:
                                    signals[stockimg.ticker][trade_date] = pd.DataFrame({
                                        'Ticker': [stockimg.ticker],
                                        'Date': [trade_date],
                                        'Label': [signal],
                                        'Close': [close],
                                        'Probability': [probability],
                                        'Range': ['/'.join(dates)],
                                        'Detect': [stockimg.trade_date]
                                    })
                                    if stockimg.last_signal(xmin, xmax, 3):
                                        is_signal = True
                                else:
                                    if df.Label[0] != signal:
                                        signals[stockimg.ticker].pop(trade_date)
                                        is_signal = False

                                if save_txt and is_signal:  # Write to file
                                    xywh = (
                                        xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn
                                    ).view(-1).tolist()  # normalized xywh
                                    line = (cls, *xywh, conf)
                                    with open(txt_path + '.txt', 'a') as f:
                                        f.write(('%g ' * len(line)).rstrip() % line + '\n')

                                if save_img:  # Add bbox to image
                                    label = f'{names[int(cls)]} {conf:.2f}'
                                    plot_one_box(
                                        xyxy, im0, label=label,
                                        color=colors[int(cls)],
                                        line_thickness=2
                                    )
                        if signal == "sell":

                            if check == 0:
                                print("skip sell")
                                continue

                            elif check == 1:

                                check = 0
                                probability = round(float(conf), 3)
                                trade_date = stockimg.get_trade_date(dates)
                                close = stockimg.get_trade_close(trade_date)
                                df = signals[stockimg.ticker].get(trade_date)

                                if df is None:
                                    signals[stockimg.ticker][trade_date] = pd.DataFrame({
                                        'Ticker': [stockimg.ticker],
                                        'Date': [trade_date],
                                        'Label': [signal],
                                        'Close': [close],
                                        'Probability': [probability],
                                        'Range': ['/'.join(dates)],
                                        'Detect': [stockimg.trade_date]
                                    })
                                    if stockimg.last_signal(xmin, xmax, 3):
                                        is_signal = True
                                else:
                                    if df.Label[0] != signal:
                                        signals[stockimg.ticker].pop(trade_date)
                                        is_signal = False

                                if save_txt and is_signal:  # Write to file
                                    xywh = (
                                        xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn
                                    ).view(-1).tolist()  # normalized xywh
                                    line = (cls, *xywh, conf)
                                    with open(txt_path + '.txt', 'a') as f:
                                        f.write(('%g ' * len(line)).rstrip() % line + '\n')

                                if save_img:  # Add bbox to image
                                    label = f'{names[int(cls)]} {conf:.2f}'
                                    plot_one_box(
                                        xyxy, im0, label=label,
                                        color=colors[int(cls)],
                                        line_thickness=2
                                    )

            # Save results (image with detections)
            if save_img and is_signal:
                cv2.imwrite(save_path, im0)
        pbar.update()
    pbar.close()

    for ticker, box in signals.items():
        df_list = []
        save_path = str(save_dir / 'signals' / f'{ticker}.csv')
        for trade_date, df in box.items():
            df_list.append(df)
        try:
            signal_df = pd.concat(df_list, ignore_index=True)
            signal_df.sort_values('Date', inplace=True)
            signal_df.astype({'Ticker': str})
            signal_df.to_csv(save_path, index=False)
        except ValueError:
            print(f'{ticker} not detected')

    print(f'Done. ({time.time() - t0:.3f}s)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    # This is the new argument
    parser.add_argument(
        '--pair', type=int, default=0,
        help='Option for deciding pairs'
    )
    parser.add_argument(
        '--weights', nargs='+', type=str, default='yolov7.pt',
        help='model.pt path(s)'
    )
    parser.add_argument(
        '--source', type=str, default='inference/images',
        help='source'
    )  # file/folder
    parser.add_argument(
        '--imgsz', type=int, default=640,
        help='inference size (pixels)'
    )
    parser.add_argument(
        '--conf-thres', type=float, default=0.25,
        help='object confidence threshold'
    )
    parser.add_argument(
        '--iou-thres', type=float, default=0.45,
        help='IOU threshold for NMS'
    )
    parser.add_argument(
        '--device', default='',
        help='cuda device, i.e. 0 or 0,1,2,3 or cpu'
    )
    parser.add_argument(
        '--save-txt', action='store_true',
        help='save results to *.txt'
    )
    parser.add_argument(
        '--project', default='runs/detect',
        help='save results to project/name'
    )
    parser.add_argument(
        '--name', default='exp',
        help='save results to project/name'
    )
    parser.add_argument(
        '--exist-ok', action='store_true',
        help='existing project/name ok, do not increment'
    )
    parser.add_argument(
        '--trace', action='store_true',
        help='don`t trace model'
    )
    opt = parser.parse_args()
    print(opt)

    vaiv = VAIV(ROOT)
    kwargs = {
        'market': 'Kospi',
        'feature': {'Volume': False, 'MA': [-1], 'MACD': False},
        'offset': 1,
        'size': [1800, 650],
        'candle': 245,
        'linespace': 1,
        'candlewidth': 0.8,
        'style': 'default'  # default는 'classic'
    }
    vaiv.set_kwargs(**kwargs)
    vaiv.set_stock()
    vaiv.set_prediction()
    vaiv.set_image()

    with torch.no_grad():
        detect(**vars(opt), vaiv=vaiv)
