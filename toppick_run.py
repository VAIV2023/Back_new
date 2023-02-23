import subprocess
import time

kospi_end = 900
kosdaq_end = 1600
start = 0
end = 100
while end < kosdaq_end:
    print(f"start: {start}, end: {end}")
    subprocess.call(f'nohup python3 /home/ubuntu/Back_new/toppick.py --start {start} --end {end} > toppick_{start}_{end}.out &', shell=True)
    start += 100
    end += 100
    time.sleep(60)