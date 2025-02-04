# 번개장터 API를 통해 브랜드별 JSON데이터 수집하는 코드
from heapq import merge

import requests
import json
import os
import threading
from datetime import datetime

def send_api_request(brands, category_id, page):
    base_url = "https://api.bunjang.co.kr/api/1/find_v2.json"
    params = {
        "q": brands,        # 검색어: 브랜드명
        "order": "score",
        "page": page,
        "f_category_id": category_id,  # 남성 카테고리 (고정)
        "n": 100,
        "stat_category_required": 1
    }
    # no_result: 더 이상 결과가 없거나, 검색 결과가 비어있을 때 True
    # list: 실제 상품 목록
    response = requests.get(base_url, params=params)
    print(f"API 요청 (페이지 {page + 1}): {response.url}")
    data = response.json()
    total_count = data["categories"][0]["count"]
    no_result = data.get("no_result", False)
    return data, no_result, total_count

def parse_product_data(products, brands):
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
            "category_id": product["category_id"]
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

def save_to_json(data, filename):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def extract_categories(categories, threshold=30000, include_parent=False):
    result = []
    for category in categories:
        if category["count"] > threshold:
            if include_parent:
                result.append({"id": category["id"], "count": category["count"]})
            if "categories" in category:
                result.extend(extract_categories(category["categories"], threshold, False))
        else:
            result.append({"id": category["id"], "count": category["count"]})
    return result

def collect_and_filter_data(brands, output_file):
    filtered_products = []

    data, _, _ = send_api_request(brands, 320, 0)
    top_level_categories = data["categories"]
    filtered_categories = [{"id": top_level_categories[0]["id"], "count": top_level_categories[0]["count"]}]
    filtered_categories.extend(extract_categories(top_level_categories, include_parent=False))

    total_count = filtered_categories[0]["count"]
    print(f"브랜드 {brands[0]} - 전체 제품 수: {total_count}")

    for category in filtered_categories[1:]:
        category_id = category["id"]
        page = 0
        while True:
            print(f"{page + 1} 페이지 데이터 수집 중...")
            data, no_result, total_count = send_api_request(brands, category_id, page)

            if no_result:
                break

            products = data["list"]
            collected_products = parse_product_data(products, brands)
            filtered_products.extend(filter_products(collected_products, brands[0]))

            page += 1
            if page == 300:
                break

    save_to_json(filtered_products, output_file)
    print(f"브랜드 {brands[0]} - 필터링 후 남은 제품 수: {len(filtered_products)}")
    print()


def filter_products(products, brand_name):
    """
    브랜드명이 상품명에 포함되어 있고,
    가격이 10,000원 이상이며,
    마지막 자리가 0으로 끝나는 상품만 필터링
    """
    filtered_products = []
    for product in products:
        price_updates = product["price_updates"]
        latest_price = list(price_updates[0].values())[0]  # 가장 최근 가격
        if brand_name in product["name"] and latest_price.isdigit() and latest_price[-1] == "0" and int(
                latest_price) >= 10000:
            product["brands"] = [brand_name]
            filtered_products.append(product)

    return filtered_products

def merge_results(input_dir, output_file, lock, brand):
    print(f"Input directory: {input_dir}")
    print(f"Output file: {output_file}")
    print(f"Merging data for brand: {brand}")

    all_products = []

    # 기존 파일이 있는 경우 읽어옴
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

    # 특정 브랜드 파일 읽어와서 병합
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

    # 병합된 데이터를 파일로 저장
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
    # 브랜드 목록을 data파일에서 불러오고 해달 브랜드들의 JSON 불러오기
    with open("data/brands_test.json", "r", encoding="utf-8") as file:
        brand_map = json.load(file)

    output_dir = "output_data"
    os.makedirs(output_dir, exist_ok=True)

    for kor_brand, eng_brand in brand_map.items():
        search_brand = kor_brand
        # 영문명을 출력해 파일명으로 사용
        output_file = os.path.join(output_dir, f"{eng_brand}_products.json")
        collect_and_filter_data([search_brand], output_file)

    # 각 브랜드별 파일에 해당 브랜드의 정보를 겹치지 않는 데이터만 병합
    # merge_results 함수의 두번째 인자는 각 브랜드 파일 경로이다.
    lock = threading.Lock()
    for kor_brand, eng_brand in brand_map.items():
        # 여기서는 각 브랜드의 결과 파일경로가 output_file과 같다
        brand_file = os.path.join(output_dir, f"{eng_brand}_products.json")
        merge_results(output_dir, brand_file, lock, eng_brand)

