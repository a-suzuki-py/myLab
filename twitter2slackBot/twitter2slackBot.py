#===================================================
# coding: UTF-8
# Twitterから特定の検索ワードを含むTweetを取得
# それをslackに返信として投稿する処理
#===================================================
import os
import csv
import twint
import keyFile
import requests
from datetime import datetime, timedelta


class Tweet:
    """
    Twitter情報用のクラス
    """
    date = ''
    time = ''
    link = ''
    tweet = ''


def fetch_tweet(query):
    """
    Twitterから情報を取得して取得結果をcsvとして出力する
    既にファイルがある場合は上書きする
    """
    try:
        os.remove(keyFile.OUTPUT_FILE)
    except:
        pass

    c = twint.Config()
    c.Search = query
    c.Store_csv = True
    c.Output = keyFile.OUTPUT_FILE
    c.Limit = 1 #1で100Tweet

    today = datetime.today()
    yesterday = today - timedelta(days=1)

    c.Since = datetime.strftime(yesterday, '%Y-%m-%d')
    twint.run.Search(c)


def parse_csv():
    """
    csvファイルからデータを読み取ってList型に変換する処理
    """
    data = []
    i = 0
    #読み込んだcsvファイルを"f"という変数に代入
    #withは開いたファイルを自動で閉じている
    with open(keyFile.OUTPUT_FILE, 'r', encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if i == 0:
                pass
            else:
                t = Tweet()
                t.date = row[3] #csvファイルの3番目の項目
                t.time = row[4]
                t.tweet = row[10]
                t.link = row[20]

                #テキスト内に検索ワードを含んでいるか
                #名前に入っているものも適用されるのでそれを除外するため
                if(keyFile.SERCH_GAME_NAME in t.tweet and ("バグ" in t.tweet or "不具合" in t.tweet or "落ちる" in t.tweet)):
                    data.append(t)

            i += 1
        return data


def send_slack(tweetList):
    """
    slackに送信する処理
    今回はTwitterから取得したリンクを送信している
    """
    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": "Bearer "+keyFile.TOKEN}

    #まずチャンネルに投稿する
    data  = {
        'channel': keyFile.CHANNEL,
        'text': "バグ、不具合に関するTweetを取得したよ"
    }
    r = requests.post(url, headers=headers, data=data)
    ts = r.json()["ts"]

    #↑で投稿したスレッドに返信する形で投稿する
    #チャンネル名とタイムスタンプで判断している
    for tweet in tweetList:
        data2 = {
            'channel': keyFile.CHANNEL,
            'text': "{}".format(tweet.link),
            "thread_ts": ts #data送信した投稿のタイムスタンプ
        }
        r = requests.post(url, headers=headers, data=data2)


def main():
    """
    メイン処理
    Twitterから検索ワードのTweetを取得して
    slackに送信
    """
    search = keyFile.SERCH_GAME_NAME + " AND (バグ OR 不具合 OR 落ちる)"
    fetch_tweet(search)

    try:
        tweetList = parse_csv()
        send_slack(tweetList)
    except:
        pass


#他のファイルからmainを呼ばれないようにしている
if __name__ == "__main__":
    main()