# 번개장터 API를 통해 브랜드별 JSON데이터 수집 후 Elasticsearch에 저장하는 코드

import requests
import json
import os
from datetime import datetime
from elasticsearch import Elasticsearch

# Elasticsearch 연결 설정 (필요에 따라 인증 정보 추가)
es = Elasticsearch(["http://elasticsearch:9200"])

def send_api_request(brands, category_id, page):
    """
    번개장터 API에서 제품 데이터를 요청하는 함수
    """
    base_url = "https://api.bunjang.co.kr/api/1/find_v2.json"
    params = {
        "q": brands,
        "order": "score",
        "page": page,
        "f_category_id": category_id,
        "n": 100,
        "stat_category_required": 1
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    no_result = data.get("no_result", False)
    total_count = data["categories"][0]["count"]
    print(f"API 요청 (페이지 {page+1}): {response.url}")
    return data, no_result, total_count

def parse_product_data(products, brands):
    """
    API 응답 데이터를 가공하여 저장 가능한 형식으로 변환하는 함수
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    product_list = []
    for product in products:
        price = product["price"]
        product_info = {
            "pid": product["pid"],
            "brands": [brand for brand in brands if brand in product["name"]],
            "name": product["name"],
            "price_updates": [{product["update_time"]: price}],
            "product_image": product["product_image"],
            "status": product["status"],
            "category_id": product["category_id"],
            "collected_timestamp": current_time
        }
        product_list.append(product_info)
    return product_list

def get_product_list(brands, category_id, page):
    data, _, _ = send_api_request(brands, category_id, page)
    products = data["list"]
    product_list = parse_product_data(products, brands)
    return product_list

def update_products(all_products, new_products):
    all_products_dict = {product["pid"]: product for product in all_products}

    for new_product in new_products:
        pid = new_product["pid"]
        if pid in all_products_dict:
            product = all_products_dict[pid]

            if new_product["status"] != product["status"]:
                product["status"] = new_product["status"]

            new_update_time = list(new_product["price_updates"][0].keys())[0]
            if new_update_time not in [list(p.keys())[0] for p in product["price_updates"]]:
                product["price_updates"].insert(0, {
                    new_update_time: list(new_product["price_updates"][0].values())[0]
                })

            for brand in new_product["brands"]:
                if brand not in product["brands"]:
                    product["brands"].append(brand)
        else:
            all_products_dict[pid] = new_product

    return list(all_products_dict.values())

def get_updated_products(yesterday_data, today_data):
    updated_data = []

    for today_product in today_data:
        for yesterday_product in yesterday_data:
            if today_product["pid"] == yesterday_product["pid"]:
                if (
                    today_product["status"] != yesterday_product["status"] or
                    today_product["price_updates"][0] != yesterday_product["price_updates"][0] or
                    set(today_product["brands"]) != set(yesterday_product["brands"])
                ):
                    updated_data.append(today_product)
                break
        else:
            updated_data.append(today_product)

    return updated_data

def filter_products(products, brand_name):
    """
    브랜드명 포함, 가격 10,000원 이상, 마지막 자리가 0인 제품만 필터링
    """
    filtered_products = []
    for product in products:
        price_updates = product["price_updates"]
        latest_price = list(price_updates[0].values())[0]  # 가장 최근 가격
        if (brand_name in product["name"] and
            latest_price.isdigit() and
            latest_price[-1] == "0" and
            int(latest_price) >= 10000):
            # 브랜드 리스트를 해당 브랜드 하나로 변경
            product["brands"] = [brand_name]
            filtered_products.append(product)
    return filtered_products

def save_to_json(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf=8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print(f"{len(data)}개 문서가 {filename}에 저장")

def collect_and_filter_data(brands, output_file):
    """
    브랜드 데이터를 크롤링하여 로컬에 저장하는 함수
    """
    filtered_products = []

    # 최상위 카테고리 조회
    data, _, _ = send_api_request(brands, 320, 0)
    top_level_categories = data["categories"]
    # 최상위 카테고리부터 필터링 시작 (필요시 더 상세하게 변경 가능)
    filtered_categories = [{"id": top_level_categories[0]["id"], "count": top_level_categories[0]["count"]}]
    total_count = filtered_categories[0]["count"]
    print(f"브랜드 {brands[0]} - 전체 제품 수: {total_count}")

    # 각 카테고리별로 데이터 수집
    for category in filtered_categories:
        category_id = category["id"]
        page = 0
        while True:
            print(f"{page + 1} 페이지 데이터 수집 중...")
            data, no_result, _ = send_api_request(brands, category_id, page)
            if no_result:
                break
            products = data["list"]
            collected_products = parse_product_data(products, brands)
            filtered_products.extend(filter_products(collected_products, brands[0]))
            page += 1
            if page == 300:
                break

    # 로컬에 저장
    save_to_json(filtered_products, output_file)
    print(f"브랜드 {brands[0]} - {output_file}에 저장 완료 ({len(filtered_products)}개 데이터)")

def merge_results(input_dir, output_file, lock, brand):
    print(f"Input directory: {input_dir}")
    print(f"Output file: {output_file}")
    print(f"Merging data for brand: {brand}")

    all_products = []

    # 기존에 병합된 결과 파일이 있으면 읽어옴
    if os.path.exists(output_file):
        print(f"Reading existing file: {output_file}")
        with open(output_file, "r", encoding="utf-8") as file:
            lock.acquire()
            try:
                all_products = json.load(file)
            except json.JSONDecodeError as e:
                print(f"Failed to parse existing file: {e}")
                all_products = []
            finally:
                lock.release()
    else:
        print(f"Creating new file: {output_file}")

    # 해당 브랜드의 새로운 데이터 파일 읽기
    brand_file = os.path.join(input_dir, f"{brand}_products.json")
    print(f"Reading brand file: {brand_file}")
    with open(brand_file, "r", encoding="utf-8") as file:
        try:
            brand_products = json.load(file)
        except json.JSONDecodeError as e:
            print(f"Failed to parse brand file: {brand_file}, error: {e}")
            brand_products = []

    # 기존 데이터와 중복되지 않는 제품만 추가
    for product in brand_products:
        if product not in all_products:
            all_products.append(product)

    # 병합된 결과를 저장
    print(f"Saving merged data to: {output_file}")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as file:
        lock.acquire()
        try:
            json.dump(all_products, file, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to save merged data: {e}")
        finally:
            lock.release()

    print(f"Merge completed for brand: {brand}")

if __name__ == "__main__":
    # 브랜드 목록 파일 불러오기 (예: {"나이키": "nike", "아디다스": "adidas", ...})
    with open("/opt/airflow/data/brands_test.json", "r", encoding="utf-8") as f:
        brand_map = json.load(f)

    # 각 브랜드별로 데이터 수집 및 로컬 파일 저장 실행
    for kor_brand, eng_brand in brand_map.items():
        # 출력 파일 경로를 지정합니다.
        output_file = f"/opt/airflow/output/{eng_brand}_products.json"
        collect_and_filter_data([kor_brand], output_file)