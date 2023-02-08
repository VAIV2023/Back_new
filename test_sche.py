import schedule

num = 10

def job(num):
    print(f"count : {num}")
    num -= 1
    return num

if __name__ == '__main__':
    # 실행 주기 설정
    schedule.every(1).second.do(job, num)

    # 실행 시작
    while True:
        schedule.run_pending()