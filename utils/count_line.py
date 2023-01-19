from pathlib import Path
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--directory', type=str, help='Directory of text files'
    )
    opt = parser.parse_args()
    print(opt)
    
    p = Path(opt.directory)
    files_path = list(p.iterdir())
    
    total = 0
    for file_path in files_path:
        f = open(file_path, 'r')
        lines = list(enumerate(f))
        total += len(lines)
    avg = total / len(files_path)
    print(total)
    print(round(avg, 0))