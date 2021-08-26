from time import sleep
from bs4 import BeautifulSoup, element
import requests
from requests.exceptions import Timeout
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

# ランサーズ実案件演習
# https://www.lancers.jp/work/detail/3693311

# driverの挙動が安定していない
# 3回に1回くらいしか成功しない

def main():
    d_list = []

    options = webdriver.ChromeOptions()
    # options.add_argument('--incognito') # シークレットモードで起動
    options.add_argument('--headless')  # ブラウザを立ち上げない

    # chromedriverを読み込む
    driver = webdriver.Chrome(
            executable_path="#ここにchromedriverのパスを設定する",
            options=options
        )

    # 要素が見つかるまで最大10秒待つ
    driver.implicitly_wait(10)

    driver.get("https://jp.indeed.com/?from=gnav-jobsearch--jasx")
    sleep(3)

    # キーワード検索で「私学教員」と入力する
    search_box = driver.find_element_by_css_selector("input.icl-TextInput-control.icl-TextInput-control--whatWhere")
    sleep(3)

    search_box.send_keys("私学教員")
    sleep(3)

    search_box.submit()
    sleep(3)

    page_count = 0


    while(True):
        # ページとアドレス確認用
        print(page_count)
        print(driver.current_url + "&start=" + str(page_count*10))

        driver.get(driver.current_url + "&start=" + str(page_count*10))
        page_count += 1
        sleep(5)

        # 件数が多いのでとりあえず20ページまで
        if page_count >= 20:
            break;

        #ソースを取得
        soup = BeautifulSoup(driver.page_source, "lxml")
        elems = soup.select("div.jobsearch-SerpJobCard.unifiedRow.row.result.clickcard")

        for i, elem in enumerate(elems):
            print("="*15, i, "="*15)

            # タイトル
            title = elem.select_one("h2")
            if title is not None:
                title = title.get_text().strip()
                print(title)

            # 会社名
            company = elem.select_one(".company")
            if company is not None:
                company = company.get_text().strip()
                print(company)

            # 勤務地
            location = elem.select_one(".location.accessible-contrast-color-location")
            if location is not None:
                location = location.get_text().strip()
                print(location)

            # リンク
            link = elem.select_one(".title > a")
            if link is not None:
                link = "https://jp.indeed.com" + link.get("href").strip()
                print(link)

            d = {
                "title": title,
                "company": company,
                "location": location,
                "link": link
            }

            d_list.append(d)

    # csv出力
    df = pd.DataFrame(d_list)
    df.to_csv('indeed_teacher.csv', index=None, encoding='utf-8-sig')


#他のファイルからmainを呼ばれないようにしている
if __name__ == "__main__":
    main()

