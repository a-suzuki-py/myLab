#================================================================
# Twitterアカウントがシャドウバンされてないか確認する
# 8時にのみ実行し、シャドウバンを検出した場合はLINEにメッセージを飛ばす
#
# 参考　：　https://qiita.com/eg_i_eg/items/b5da0987ba9eac03019d
#================================================================

import requests
import time
import datetime

Line_Access_Token = "LINEのアクセストークン"

is_touketsu = is_touketsu = is_searchsuggestban = is_searchban = is_ghostban = None # 各フラグ初期化

#================================================================
# main
#================================================================
def main():
    # 8時にだけ処理が動く
    # Herokuが1時間に1回走る予定
    hour = datetime.datetime.now().strftime("%H")
    if hour != "8": return

    # チェックしたいアカウント[@付きでもなしでも良い]
    account_list = ["アカウント1", "アカウント2"]

    # リストに登録されているアカウントをチェックする
    for account in account_list:
        msg = check_shadowban(account)

        # 何か引っかかっていたときだけメッセージを送る
        if is_touketsu or is_searchsuggestban or is_searchban or is_ghostban:
            print(msg)
            send_line(msg)
        time.sleep(5)


#================================================================
# アクセス結果を解析してメッセージを返す
#================================================================
def analyze_shadowban_data(data, account_name):
    marubatsu = lambda x: "×" if x else "○" # バンされている場合(True)は×、されていない場合(False)は○
    try:
        global is_exists
        is_exists = data.get("profile").get("exists") is True
    except:
        pass
    if is_exists is False:
        return f"@{account_name} does not exists!"

    try:
        global is_touketsu
        is_touketsu = marubatsu(data.get("profile").get("protected") is True)
    except:
        pass

    try:
        global is_ghostban
        is_ghostban = marubatsu(data.get("tests").get("ghost").get("ban") is True)
    except:
        pass

    try:
        global is_searchban
        is_searchban = marubatsu(data.get("tests").get("search") is False)
    except:
        pass

    try:
        global is_searchsuggestban
        is_searchsuggestban = marubatsu(data.get("tests").get("typeahead") is False)
    except:
        pass

    # インデント汚いのはLINEの表示で綺麗に見せるため。。。
    msg = f"シャドウバンされてる！！\n\
====================\n\
@{account_name}\n\
Suspend：{is_touketsu}\n\
SearchSuggestBan：{is_searchsuggestban}\n\
SearchBan:{is_searchban}\n\
GhostBan:{is_ghostban}\n\
===================="

    return msg

#================================================================
# シャドウバンチェックサイトにアクセスしてチェックする
#================================================================
def check_shadowban(username):
    username = username.replace("@", "").replace("＠", "") # @マーク(全角、半角)を削除
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
    url = "https://shadowban.eu/.api/" + username
    try_max = 5 # サイトから取得する最大試行回数
    time_sleep = 10 # 取得に失敗した場合の待機時間
    for i in range(try_max):
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return analyze_shadowban_data(res.json(), username)
        if i == try_max - 1:
            return None
        time.sleep(time_sleep*(i+1))


#================================================================
# LINE用クラス
#================================================================
class LINENotifyBot:
    API_URL = 'https://notify-api.line.me/api/notify'

    def __init__(self, access_token):
        self.__headers = {'Authorization': 'Bearer ' + access_token}

    def send(
            self, message,
            image=None, sticker_package_id=None, sticker_id=None,
            ):
        payload = {
            'message': message,
            'stickerPackageId': sticker_package_id,
            'stickerId': sticker_id,
            }
        files = {}
        if image != None:
            files = {'imageFile': open(image, 'rb')}
        r = requests.post(
            LINENotifyBot.API_URL,
            headers=self.__headers,
            data=payload,
            files=files,
            )

line_bot = LINENotifyBot(access_token=Line_Access_Token)


#================================================================
# LINEに通知する処理
#================================================================
def send_line(line_text):
    text = "\n" + line_text
    line_bot.send(message=text)



if __name__ == "__main__":
    main()
