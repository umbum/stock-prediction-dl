# @author       umbum (umbum7601@gmail.com)
# @date         2019/05/29
# word2vec으로 생성된 바이너리 뉴스 데이터에 주가를 labeling해주는 스크립트

import sys

import os
import numpy as np
import pickle


def labelingNewsIter(stock_file, news_file):
    """
    News Labeling Iterator
    data/stock_label/{} 에 주가 데이터인 .npy 파일이 위치해야 하며
    data/{} 에 뉴스 데이터인 .pickle 파일이 위치해야 합니다.

    Usage
    -----
    from data.news_labeling_util import labelingNewsIter

    for news, closing_price in labelingNewsIter("SK하이닉스_data.npy", 6_news_vectors_100.pickle):
        // do something with...
        news["day"]
        news["subject"]
        news["action"]
        news["object"]
        label
    
    Yields
    ------
    (news, label): tuple
        news = {
            "day"     : str
            "time"    : str
            "subject" : nparray100
            "action"  : nparray100
            "object"  : nparray100
        }
        label : int, 전일 종가 대비 금일 종가가 올랐으면 1, 아니면 0


    """
    stock_data = np.load(stock_file)
    with open(news_file, "rb") as f:
        try:
            news = pickle.load(f)
            s_idx = -1
            while True:
                news_day = news["day"].replace(".", "")
                stock_day = stock_data[s_idx][0]

                if news_day == stock_day:
                    yield news, int(stock_data[s_idx][4] > stock_data[s_idx - 1][4])
                    news = pickle.load(f)
                elif news_day < stock_day:
                    s_idx = s_idx - 1
                elif news_day > stock_day:
                    news = pickle.load(f)

        except (EOFError, IndexError):
            pass
            

if __name__ == "__main__":
    if (len(sys.argv) == 3):
        stock_file = sys.argv[1]
        news_file = sys.argv[2]
    else:
        print("Usage : python {} <stock_label.npy> <event_vector.pickle>".format(__file__))
        sys.exit()

    stock_data = np.load(stock_file)
    print(stock_data[-310:-300])
    n = 0
    a = 0
    b = 0
    for news, closing_price in labelingNewsIter(stock_file, news_file):
        a = news
        b = closing_price
        n = n + 1
    print("num of recods : {}".format(n))
    print(a)
    print("label",format(b))