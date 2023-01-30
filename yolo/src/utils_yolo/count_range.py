import pandas as pd
import numpy as np
from pathlib import Path
import argparse

def main(dir):
    p = Path(dir) / 'dataframes'
    filePath = list(p.iterdir())
    date_count = []
    
    for file in filePath:
        df = pd.read_csv(file)
        dranges = df.Range.tolist()
        for drange in dranges:
            date_count.append(drange.count('/') + 1)
    print(round(np.mean(date_count), 2))
    print(date_count.count(75))
    print(max(date_count), min(date_count))
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory', type=str, help='Directory of text files'
    )
    opt = parser.parse_args()
    print(opt)
    main(opt.directory)