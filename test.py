# coding: utf-8
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def spider(page):
    time.sleep(page)
    print(f"crawl task{page} finished")
    return page


def main():
    # print(os.environ['HOME'])
    print(os.path.expandvars('$HOMEPATH'))
    print(os.path.expanduser('~'))
    with ThreadPoolExecutor(max_workers=1) as t:
        obj_list = []
        for page in range(1, 5):
            obj = t.submit(spider, page)
            obj_list.append(obj)

        print("------------")
        for future in as_completed(obj_list):
            data = future.result()
            print(f"main: {data}")


if __name__ == '__main__':
    main()
