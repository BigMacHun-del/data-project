# --------------
# 작성자 : 김대훈
# 작성목적 : 컴프리헨션, 제너레이터의 이해를 돕기 위한 연습문제
# 작성일 : 2026년 7월 15일

# 컴프리헨션, 제너레이터의 이해를 돕기 위한 연습문제입니다.
#
# 변경사항 내역
# 0.1 : 2026년 7월 15일 - 최초 작성 
# --------------

import json

# 파일이 순수 JSON이 아니라 "sales = [...]" 형태의 파이썬 변수 할당문이므로
# '=' 뒤의 리스트 부분만 잘라내서 JSON으로 파싱한다.
with open("Python_Practice1_Data.json", "r", encoding="utf-8") as f:
    content = f.read()

json_str = content.split("=", 1)[1].strip()
sales = json.loads(json_str)

# 1. amount >= 1000인 거래만 필터링 (리스트 컴프리헨션)
high_value_sales = [sale for sale in sales if sale["amount"] >= 1000]

print(f"amount >= 1000 거래 건수: {len(high_value_sales)}")
for sale in high_value_sales:
    print(sale)

# 2. 지역별 총매출 dict (딕셔너리 컴프리헨션)
regions = {sale["region"] for sale in sales}  # 중복 제거된 지역 목록
region_total_sales = {
    region: sum(sale["amount"] for sale in sales if sale["region"] == region)
    for region in regions
}

print("\n지역별 총매출:")
for region, total in region_total_sales.items():
    print(f"{region}: {total}")