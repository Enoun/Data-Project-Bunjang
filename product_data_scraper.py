from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import pandas as pd
import os

# 페이지 수집 함수 정의
def collect_data_from_page(page_num, category_num, driver):
    print(f"페이지 {page_num} 데이터 수집 시작 (카테고리: {category_num})")
    page_url = f"https://m.bunjang.co.kr/categories/{category_num}?page={page_num}&req_ref=popular_category"
    driver.get(page_url)

    # 스크롤을 내려 동적 콘텐츠 로드 시도 및 다 로드가 될 떄 까지 대기
    scroll_count = 1
    for _ in range(scroll_count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    wait = WebDriverWait(driver, 5)

    # 상품 정보 추출 및 저장
    products = driver.find_elements(By.XPATH, "//*[@id='root']/div/div/div[4]/div/div[4]/div/div")
    product_data_list = []

    # print(f"데이터 수집중{page_num}")
    for product in products:
        try:
            item_name = product.find_element(By.XPATH, ".//a/div[2]/div[1]").text
            price = product.find_element(By.XPATH, ".//a/div[2]/div[2]/div[1]").text
            time_info = product.find_element(By.XPATH, ".//a/div[2]/div[2]/div[2]").text
            location = product.find_element(By.XPATH, ".//a/div[3]").text

            product_data = {
                '수집된 시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '상품명': item_name,
                '가격': price,
                '시간': time_info,
                '지역 정보': location
            }
            product_data_list.append(product_data)
        except Exception as e:
            print(f"데이터 추출 중 오류 발생: {e}")
    return product_data_list

def collect_all(category_num):
    print(f"{category_num}번 데이터 수집 시작")
    SELENIUM_URL = os.getenv('SELENIUM_URL', 'http://selenium:4444/wd/hub')

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ) # User-Agent를 설정해 봇으로 보이지 않도록 설정

    def create_driver():
        return webdriver.Remote(command_executor=SELENIUM_URL, options=chrome_options)

    def fetch_page(page_num):
        driver = create_driver()
        try:
            data = collect_data_from_page(page_num, category_num, driver)
            return data
        finally:
            driver.quit()

    all_data = []
    pages = range(1, 301)

    with ThreadPoolExecutor(max_workers=3) as executor:  # 최대 4개의 스레드 설정 가능
        futures = [executor.submit(fetch_page, page_num) for page_num in pages]
        for future in futures:
            try:
                all_data.extend(future.result())
            except Exception as e:
                print(f"크롤링 중 에러 발생: {e}")

    df = pd.DataFrame(all_data)
    base_path = "/shared/collectedData"
    sex_category = "mans_category" if category_num == 320 else "woman_category"
    file_dir = f"{base_path}/{sex_category}"
    os.makedirs(file_dir, exist_ok=True)
    file_path = f"{file_dir}/{sex_category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(file_path, mode='w', header=True, encoding="utf-8-sig", index=False)
    print(f"데이터 수집 및 저장 완료: {file_path}")

if __name__ == "__main__":
    collect_all(320)
    collect_all(310)