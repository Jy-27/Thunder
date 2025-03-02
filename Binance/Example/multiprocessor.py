# import multiprocessing

# def worker(num):
#     """thread worker function"""
#     print('Worker:', num)
#     return

# if __name__ == '__main__':
#     jobs = []
#     for i in range(10000):
#         p = multiprocessing.Process(target=worker, args=(i,))
#         jobs.append(p)
#         p.start()



# import multiprocessing

# def worker(num):
#     """thread worker function"""
#     print('Worker:', num)

# if __name__ == '__main__':
#     num_workers = multiprocessing.cpu_count()  # CPU 개수만큼 병렬 실행
#     with multiprocessing.Pool(processes=num_workers) as pool:
#         pool.map(worker, range(10000))  # 10000개의 작업을 병렬 처리


import multiprocessing

def worker(num):
    return f"Worker: {num}"

if __name__ == '__main__':
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        results = pool.map(worker, range(1000))  # 입력 순서대로 결과 반환

    print("\n".join(results))  # 순서 유지됨
