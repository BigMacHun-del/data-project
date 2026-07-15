# --------------
# 작성자 : 김대훈
# 작성목적 : 컴프리헨션, 제너레이터의 이해를 돕기 위한 연습문제
# 작성일 : 2026년 7월 15일

# 컴프리헨션, 제너레이터의 이해를 돕기 위한 연습문제입니다.
#
# 변경사항 내역
# 0.1 : 2026년 7월 15일 - 최초 작성
# 0.2 : 2026년 7월 15일 - Counter(지역별 거래 건수), defaultdict(카테고리별 amount 리스트) 추가
# 0.3 : 2026년 7월 15일 - amount > 1000 제너레이터 추가, 리스트 버전과 메모리 크기 비교 추가
# 0.4 : 2026년 7월 15일 - month·category 기준 그룹핑 총매출 dict 추가 (컴프리헨션 + defaultdict)
# --------------

import json
import sys
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

# 5. amount > 1000 인 행만 yield 하는 제너레이터, 리스트 버전과 메모리 비교
def high_value_sales_generator(data):
    """amount > 1000인 거래만 하나씩 yield하는 제너레이터"""
    for sale in data:
        if sale["amount"] > 1000:
            yield sale


# 리스트 버전 (컴프리헨션) : 모든 결과를 메모리에 즉시 생성/보관
high_value_list = [sale for sale in sales if sale["amount"] > 1000]

# 제너레이터 버전 : 값을 미리 만들지 않고 필요할 때마다 하나씩 생성
high_value_gen = high_value_sales_generator(sales)

list_size = sys.getsizeof(high_value_list)
gen_size = sys.getsizeof(high_value_gen)

print("\n[리스트 vs 제너레이터 메모리 크기 비교] (amount > 1000)")
print(f"리스트 버전 크기   : {list_size:,} bytes (원소 {len(high_value_list)}개 포함)")
print(f"제너레이터 버전 크기 : {gen_size:,} bytes (아직 값을 생성하지 않은 상태)")
print(f"차이               : 약 {list_size - gen_size:,} bytes 만큼 리스트가 더 큼")

# 제너레이터는 실제로 순회해야 값을 하나씩 만들어낸다 (지연 평가 확인용)
print("\n제너레이터로 순회하며 값 확인 (앞 3개만):")
for i, sale in enumerate(high_value_sales_generator(sales)):
    if i >= 3:
        break
    print(sale)

# 6. month·category 기준 그룹핑 총매출 dict (컴프리헨션 + defaultdict)
months = sorted({sale["month"] for sale in sales})
categories = sorted({sale["category"] for sale in sales})

# 먼저 딕셔너리 컴프리헨션으로 (month, category) 조합별 총매출을 계산하고,
# 그 결과를 defaultdict(float)로 감싸서 없는 키를 조회해도 KeyError 없이 0.0이 나오게 한다.
month_category_sales = defaultdict(float, {
    (month, category): sum(
        sale["amount"] for sale in sales
        if sale["month"] == month and sale["category"] == category
    )
    for month in months
    for category in categories
})

print("\nmonth·category별 총매출 (defaultdict + 컴프리헨션):")
for month in months:
    print(f"[{month}]")
    for category in categories:
        total = month_category_sales[(month, category)]
        print(f"  {category}: {total:,.0f}")

# defaultdict 특성 확인: 존재하지 않는 조합을 조회해도 KeyError 없이 0.0 반환
print("\n존재하지 않는 조합 조회 예시 (defaultdict 동작 확인):")
print(f"('2099-01', '없는카테고리') -> {month_category_sales[('2099-01', '없는카테고리')]}")