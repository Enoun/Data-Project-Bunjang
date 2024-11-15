from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import pandas as pd
import os
import time as t
import schedule

# ChromeDriver 경로 설정
service = Service('/Users/data-project/chromedriver-mac-arm64/chromedriver')

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

# ChromeDriver 실행
driver = webdriver.Chrome(service=service, options=chrome_options)

# 다 로드 될때까지 기다리기
driver.implicitly_wait(10)

# 셀별 데이터를 저장할 리스트
product_data_list = []

# 페이지 수집 함수 정의
def collect_data_from_page(page_num, category_num):
    page_url = f"https://m.bunjang.co.kr/categories/{category_num}?page={page_num}&req_ref=popular_category"
    driver.get(page_url)

    # 스크롤을 내려 동적 콘텐츠 로드 시도
    scroll_count = 1
    for i in range(scroll_count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        t.sleep(3)  # 스크롤 후 페이지 로드 대기

    # 상품 리스트가 로드될 때까지 대기
    products = driver.find_elements(By.XPATH, "//*[@id='root']/div/div/div[4]/div/div[4]/div/div")  # 상품 셀의 XPATH

    # 상품 정보 추출 및 저장
    for product in products:
        try:
            # 상품명 추출
            item_name = product.find_element(By.XPATH, ".//a/div[2]/div[1]").text
            price = product.find_element(By.XPATH, ".//a/div[2]/div[2]/div[1]").text
            time_info = product.find_element(By.XPATH, ".//a/div[2]/div[2]/div[2]").text
            location = product.find_element(By.XPATH, ".//a/div[3]").text

            # 현재 날짜와 시간
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            product_data = {
                '수집된 시간': current_time,
                '상품명': item_name,
                '가격': price,
                '시간': time_info,
                '지역 정보': location
            }

            # 리스트에 저장
            product_data_list.append(product_data)

        except Exception as e:
            print(f"데이터 추출 중 오류 발생: {e}")
    return product_data_list

def collect_all(category_num):
    print("데이터 수집을 시작.")
    global product_data_list

    product_data_list = []
    for page_num in range(1, 291):
        collect_data_from_page(page_num, category_num)
        print(f"{page_num}번 페이지 추출 성공")

    df = pd.DataFrame(product_data_list)

    if category_num == 320:
        sex_category = "mans_category"
    else:
        sex_category = "woman_category"

    # 타임스탬프 기반 파일명 생성
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = f"/Users/data-project/data-pipeline-project/collectedData/{sex_category}/{sex_category}_{current_time}.csv"

    # 파일이 존재하는지 확인하여 헤더 설정
    df.to_csv(file_path, mode='w', header=True, encoding="utf-8-sig", index=False)
    print("데이터 수집 및 저장 완료")
    print(datetime.now().strftime('x%x %X'))

collect_all(320) #남자
collect_all(310) #여자
# schedule.every(7).hours.do(lambda: collect_all(320))
# schedule.every(7).hours.do(lambda: collect_all(310))
# schedule.every(14).hours.do(lambda: collect_all(320))
# schedule.every(14).hours.do(lambda: collect_all(310))



# 스케줄이 실행되도록 유지
try:
    while True:
        schedule.run_pending()
        t.sleep(60)
except KeyboardInterrupt:
    print("브라우저 종료")
    driver.quit()