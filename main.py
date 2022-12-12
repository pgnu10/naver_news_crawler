# 네이버 뉴스 크롤러입니다.
## INPUT : 검색어, 검색 시작 날짜, 검색 종료 날짜, 정렬
## OUTPUT : 제목, 날짜, 언론사, 기사 내용, 링크가 담긴 csv 파일

# 라이브러리
## 파일 로드
import yaml
import pandas as pd
## 데이터 전처리
import re
## 크롤링
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
## 편의 기능
import time
import warnings
warnings.filterwarnings('ignore')


def naver_news_crawler(search_keyword, start_day, end_day, sorting, p_num=1):
    search_keyword = search_keyword.replace(' ','%20')
    title, link, date, press, content = [], [], [], [], []

    while True:
        url = f'https://search.naver.com/search.naver?where=news&sm=tab_pge&query={search_keyword}&sort={sorting}&photo=0&field=0&pd=3&ds={start_day}&de={end_day}&mynews=0&office_type=0&office_section_code=0&news_office_checked=&nso=so:r,p:from{start_day.replace(".","")}to{end_day.replace(".","")},a:all&start={p_num}'
        headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/98.0.4758.102" }
        original_html = requests.get(url, headers=headers)
        html = BeautifulSoup(original_html.text, "html.parser")
        
        check = html.find_all('div', attrs={'class':'not_found02'})
        if check:
            break

        hrefs = html.find_all('a', attrs={'class':'news_tit'})
        date_infos = html.find_all('span', attrs={'class':'info'})
        companies = html.find_all('a', attrs={'class':'info press'})
        
        title.extend(list(map(lambda x: x.text, hrefs)))
        link.extend(list(map(lambda x: x.attrs['href'], hrefs)))
        date.extend(list([date.text.strip('.') for date in date_infos if '면' not in date.text]))
        press.extend(list(map(lambda x: x.text, companies)))
        
        p_num += 10

    print(f"{len(set(press))} 개의 언론사에서 총 {len(title)} 개의 뉴스 기사를 가져왔습니다.")
    if len(title) != len(set(title)):
        print(f"제목이 동일한 기사가 {len(title)-len(set(title))}개 있습니다. 중복에 주의하세요.")
    print("크롬 브라우저로 뉴스 기사 내용 크롤링을 시작합니다.")

    content = content_crawler(link)

    news_df = pd.DataFrame({'title':title, 'date':date, 'press':press, 'content':content, 'link':link})
    return news_df

def content_crawler(link):
    content = [] 
    options = webdriver.ChromeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.implicitly_wait(2)

    for url in link:
        driver.get(url)
        time.sleep(2)

        text = driver.find_element(By.XPATH, "/html/body").text
        temp_ls = re.split('\n\n\n\n\n+', text)
        content.append(max(temp_ls, key=len))
    driver.close()
    return content

def main():
    with open('config.yml', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    print(f"{config['search_keyword']}를 키워드로")
    print(f"{config['start_day']}부터 {config['end_day']}까지의 뉴스 기사를 크롤링 합니다.")
    print('-'*70)

    news_df = naver_news_crawler(config['search_keyword'], config['start_day'], config['end_day'], config['sorting'])
    
    print(f"크롤링 완료\n{config['search_keyword']}.csv에 저장합니다.")
    news_df.to_csv(f"{config['search_keyword']}.csv", encoding='utf-8-sig', index=False)


if __name__ == "__main__":
	main()