# --------------
# 작성자 : 김대훈
# 작성목적 : 컴프리헨션, 제너레이터의 이해를 돕기 위한 연습문제
# 작성일 : 2026년 7월 15일

# 컴프리헨션, 제너레이터의 이해를 돕기 위한 연습문제입니다.
#
# 변경사항 내역
# 0.1 : 2026년 7월 15일 - 최초 작성
# 0.2 : 2026년 7월 15일 - Counter(지역별 거래 건수), defaultdict(카테고리별 amount 리스트) 추가
# --------------

import json
from collections import Counter, defaultdict

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

# 3. Counter로 지역별 거래 건수 집계
region_counts = Counter(sale["region"] for sale in sales)

print("\n지역별 거래 건수 (Counter):")
for region, count in region_counts.items():
    print(f"{region}: {count}건")

# most_common()으로 거래 건수 많은 순 정렬도 바로 확인 가능
print("\n거래 건수 상위 3개 지역:")
for region, count in region_counts.most_common(3):
    print(f"{region}: {count}건")

# 4. defaultdict로 카테고리별 amount 리스트 수집
category_amounts = defaultdict(list)
for sale in sales:
    category_amounts[sale["category"]].append(sale["amount"])

print("\n카테고리별 amount 리스트 (defaultdict):")
for category, amounts in category_amounts.items():
    print(f"{category}: {amounts}")

# 카테고리별 평균 amount도 함께 확인
print("\n카테고리별 평균 amount:")
for category, amounts in category_amounts.items():
    avg = sum(amounts) / len(amounts)
    print(f"{category}: 평균 {avg:.1f} (건수: {len(amounts)})")