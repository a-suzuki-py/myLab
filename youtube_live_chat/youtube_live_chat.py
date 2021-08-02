#===================================================
# coding: UTF-8
# YouTubeLiveのコメント付きアーカイブから
# 指定のキーワードが多く含まれる箇所を抽出して
# TOP10をcsvとして出力するツール
# （コメント一覧ファイルも出力される）
# テスト回数は超少ないのでバグると思う
#===================================================
from bs4 import BeautifulSoup
import json
import requests_html
from urllib.parse import urlparse, parse_qs
import pandas as pd
import datetime

# 定数
TARGET_URL = "https://youtu.be/gD1uPh_f5gQ"           # 抽出したいYouTubeLiveアーカイブの動画URL ※共有用のリンクを指定すれば出力時に飛べるリンクが生成される
TARGET_KEYWORD = "草"                                 # 検索したいワード
OUTPUT_COMMENT_FILE_NAME = "youtube_comment.csv"      # 出力するコメント一覧用のファイル名
OUTPUT_RANK_FILE_NAME = "youtube_rank.csv"            # 最終的に出力するランク情報用のファイル名


def get_youtube_comment_csv():
    """
    TARGET_URLのYouTube動画からコメントを取得
    csvとして出力する処理
    （ほぼweb上のもの）
    """

    dict_str = ""
    next_url = ""
    comment_data = []
    session = requests_html.HTMLSession()

    # まず動画ページにrequestsを実行しhtmlソースを手に入れてlive_chat_replayの先頭のurlを入手
    resp = session.get(TARGET_URL)
    resp.html.render(sleep=3)   # 描画しきる前に処理すると情報が取れない場合があるので3秒ほど待つ

    for iframe in resp.html.find("iframe"):
        if("live_chat_replay" in iframe.attrs["src"]):
            next_url= "".join(["https://www.youtube.com", iframe.attrs["src"]])

    while(1):

        try:
            html = session.get(next_url)    # チャット情報の取得
            soup = BeautifulSoup(html.text,"lxml")

            # 次に飛ぶurlのデータがある部分をfind_allで探してsplitで整形
            for scrp in soup.find_all("script"):
                if "window[\"ytInitialData\"]" in scrp.next:
                    dict_str = scrp.next.split(" = ", 1)[1]

            # 辞書形式と認識すると簡単にデータを取得できるが,末尾に邪魔なのがあるので消しておく（「空白2つ + \n + ;」を消す）
            dict_str = dict_str.rstrip("  \n;")
            # 辞書形式に変換
            dics = json.loads(dict_str)

            # "https://www.youtube.com/live_chat_replay?continuation=" + continue_url が次のlive_chat_replayのurl
            continue_url = dics["continuationContents"]["liveChatContinuation"]["continuations"][0]["liveChatReplayContinuationData"]["continuation"]
            next_url = "https://www.youtube.com/live_chat_replay?continuation=" + continue_url
            # dics["continuationContents"]["liveChatContinuation"]["actions"]がコメントデータのリスト。
            for samp in dics["continuationContents"]["liveChatContinuation"]["actions"][1:]:
                if 'addChatItemAction' not in samp["replayChatItemAction"]["actions"][0]:
                    continue
                if 'liveChatTextMessageRenderer' not in samp["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]:
                    continue
                str1 = str(samp["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["message"]["runs"])
                if 'emoji' in str1:
                    continue
                str1 = str1.replace('[','').replace('{\'text\': \'','').replace('\'}','').replace(', ','').replace(']','')
                comment_data.append(str(samp["replayChatItemAction"]["actions"][0]["addChatItemAction"]["item"]["liveChatTextMessageRenderer"]["timestampText"]["simpleText"]))
                comment_data.append(","+str1+"\n")

        # next_urlが入手できなくなったら終わり
        except:
            break

    # (動画ID).csv として出力したい場合はこれを使う
    # url = urlparse(TARGET_URL)
    # query = parse_qs(url.query)
    # title = query["v"][0] + ".csv"

    with open(OUTPUT_COMMENT_FILE_NAME, mode='w', encoding="utf-8") as f:
        f.writelines(comment_data)



def get_word_ranking():
    """
    出力したOUTPUT_FILE_NAMEを読み込み、
    TARGET_KEYWORDが含まれるコメントを抽出
    20秒間隔ごとに分けて
    TARGET_KEYWORDを含んだコメントが多い時間帯の
    ランキングTOP10を出力する
    """
    df = pd.read_csv(filepath_or_buffer=OUTPUT_COMMENT_FILE_NAME, encoding="utf-8", sep=",", header=None, skipinitialspace=True, names = [0,1]) # names:空白エラー回避用
    df = (df[df[1].str.contains(TARGET_KEYWORD, na=False)]) #df[0]にタイムスタンプ df[1]にコメントが入っている

    separateTime = 20  # 20秒間隔で区切る（適当な値）

    # 取得したデータの最後の時間を取得する
    # iloc[-1]で最後の行を取得
    endTime = df.iloc[-1][0]
    td = convert_str_datetime(endTime)

    # 最終時間を秒数に変換
    endSec = td.total_seconds()
    listSize = int(endSec // separateTime)
    commentList = [[0] for i in range(listSize+1)]

    for index, data in df.iterrows():
        # 秒数に変換
        time = convert_str_datetime(data[0])
        time = time.total_seconds()
        listCount = int(time // separateTime)    # //で商を求めている
        commentList[listCount].append(data[0])

    # 要素数が多い順に並び替える
    dicNum = {}
    for i in range(len(commentList)):
        if len(commentList[i])-1 != 0 :
            count = len(commentList[i])-1
            dicNum[i] = count

    # 降順ソート
    dicNum = sorted(dicNum.items(), key=lambda x:x[1], reverse=True)

    rankCount = 0
    rankData = []
    for d in dicNum :
        # print(d[0])                   # keyの値確認用
        # print(commentList[d[0]])      # 要素の確認用
        # print(commentList[d[0]][1])   # 最初に格納した時間確認用
        time = convert_str_datetime(commentList[d[0]][1]);
        # print("base time =", time)    #基準値時間

        # 基準値時間の前後20秒の範囲を結果として出力する（適当な値）
        startTime = time - datetime.timedelta(seconds=20)
        finishTime = time + datetime.timedelta(seconds=20)
        rankCount += 1;

        # 出力用
        rankData.append("==============================")
        rankData.append("\n")
        rankData.append("rank" + str(rankCount))
        rankData.append("\n")
        rankData.append(str(startTime) + "~" + str(finishTime))
        rankData.append("\n")
        rankData.append(str(TARGET_URL) + "?t=" + str(int(startTime.total_seconds())))
        rankData.append("\n")

        # コンソール確認用
        print("==============================")
        print("rank",rankCount)
        print(startTime,"~",finishTime)
        print(str(TARGET_URL) + "?t=" + str(int(startTime.total_seconds())))   # 動画の対象時間へのリンク

        # ランキング10位までとったら処理を終了する
        if(rankCount >= 10):
            break;

    # csv出力して終了
    with open(OUTPUT_RANK_FILE_NAME, mode='w', encoding="utf-8") as f:
        f.writelines(rankData)



def convert_str_datetime(strTime):
    """
    文字列の時間をdatetime型に変換する処理
    （既存機能で何かありそうだけどわからなかったので手作り）
    """
    time = 0
    splitCount = len(strTime.split(":"))

    # splitCount == 2  1時間未満     50:00
    # splitCount == 3  1時間以上   1:50:00
    # 1分未満は無さそうなので無視
    if splitCount == 2:
        minutes, seconds = map(int, strTime.split(":"))
        time = datetime.timedelta(minutes=minutes, seconds=seconds)
    elif splitCount == 3:
        hours, minutes, seconds = map(int, strTime.split(":"))
        time = datetime.timedelta(hours=hours, minutes=minutes, seconds=seconds)
    else :
        print ("error!! count = ", splitCount)

    return time



def main():
    get_youtube_comment_csv()
    get_word_ranking()


#他のファイルからmainを呼ばれないようにしている
if __name__ == "__main__":
    main()


