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
# 0.5 : 2026년 7월 15일 - region_total 정확성, Counter.most_common() 순서, generator < list 메모리 크기,
#                        amount 기준 top3 내림차순 정렬 추가 및 검증
# 0.6 : 2026년 7월 15일 - 예외 처리 추가
#        - 파일 읽기/파싱 실패(FileNotFoundError, OSError, JSONDecodeError) 처리
#        - 거래 데이터에 필요한 키(region/category/amount/month)가 없는 경우 방어
#        - 카테고리별 평균 계산 시 0으로 나누는 상황(빈 리스트) 방어
#        - assert 검증 실패 시 트레이스백 대신 안내 메시지 출력 후 종료
# --------------

import json
import sys
from collections import Counter, defaultdict

# 파일이 순수 JSON이 아니라 "sales = [...]" 형태의 파이썬 변수 할당문이므로
# '=' 뒤의 리스트 부분만 잘라내서 JSON으로 파싱한다.
try:
    with open("Python_Practice1_Data.json", "r", encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print("[오류] 파일을 찾을 수 없습니다: Python_Practice1_Data.json")
    sys.exit(1)
except OSError as e:
    print(f"[오류] 파일을 읽는 중 문제가 발생했습니다: {e}")
    sys.exit(1)

if "=" not in content:
    print("[오류] 예상한 '변수 = [...]' 형식이 아닙니다.")
    sys.exit(1)

json_str = content.split("=", 1)[1].strip()

try:
    sales = json.loads(json_str)
except json.JSONDecodeError as e:
    print(f"[오류] JSON 파싱에 실패했습니다: {e}")
    sys.exit(1)

if not isinstance(sales, list) or not sales:
    print("[오류] 매출 데이터가 비어 있거나 리스트 형태가 아닙니다.")
    sys.exit(1)

# 1. amount >= 1000인 거래만 필터링 (리스트 컴프리헨션)
# 'amount' 키가 없는 거래는 0으로 간주해 필터링에서 제외한다.
high_value_sales = [sale for sale in sales if sale.get("amount", 0) >= 1000]

print(f"amount >= 1000 거래 건수: {len(high_value_sales)}")
for sale in high_value_sales:
    print(sale)

# 2. 지역별 총매출 dict (딕셔너리 컴프리헨션)
# 'region' 키가 없는 거래는 지역 집계에서 제외한다.
regions = {sale["region"] for sale in sales if "region" in sale}
region_total_sales = {
    region: sum(sale.get("amount", 0) for sale in sales if sale.get("region") == region)
    for region in regions
}

print("\n지역별 총매출:")
for region, total in region_total_sales.items():
    print(f"{region}: {total}")

# 검증 : region_total 값 정확성
try:
    for region in regions:
        expected_total = sum(sale.get("amount", 0) for sale in sales if sale.get("region") == region)
        assert region_total_sales[region] == expected_total, f"{region} 총매출 불일치"
    print("-> region_total 값 정확 (assert 통과)")
except AssertionError as e:
    print(f"[검증 실패] {e}")
    sys.exit(1)

# 3. Counter로 지역별 거래 건수 집계
# 'region' 키가 없는 거래는 "미상"으로 집계한다.
region_counts = Counter(sale.get("region", "미상") for sale in sales)

print("\n지역별 거래 건수 (Counter):")
for region, count in region_counts.items():
    print(f"{region}: {count}건")

# most_common()으로 거래 건수 많은 순 정렬도 바로 확인 가능
print("\n거래 건수 상위 3개 지역:")
top3_regions_by_count = region_counts.most_common(3)
for region, count in top3_regions_by_count:
    print(f"{region}: {count}건")

# 검증 : Counter.most_common() 순서 정확성
try:
    for i in range(len(top3_regions_by_count) - 1):
        assert top3_regions_by_count[i][1] >= top3_regions_by_count[i + 1][1], \
            "Counter.most_common() 순서 오류"
    print("-> Counter.most_common() 순서 정확 (assert 통과)")
except AssertionError as e:
    print(f"[검증 실패] {e}")
    sys.exit(1)

# 4. defaultdict로 카테고리별 amount 리스트 수집
# 'category' 또는 'amount' 키가 없는 거래는 건너뛴다.
category_amounts = defaultdict(list)
for sale in sales:
    if "category" in sale and "amount" in sale:
        category_amounts[sale["category"]].append(sale["amount"])

print("\n카테고리별 amount 리스트 (defaultdict):")
for category, amounts in category_amounts.items():
    print(f"{category}: {amounts}")

# 카테고리별 평균 amount도 함께 확인 (빈 리스트로 인한 ZeroDivisionError 방어)
print("\n카테고리별 평균 amount:")
for category, amounts in category_amounts.items():
    if not amounts:
        print(f"{category}: 데이터 없음")
        continue
    avg = sum(amounts) / len(amounts)
    print(f"{category}: 평균 {avg:.1f} (건수: {len(amounts)})")

# 5. amount > 1000 인 행만 yield 하는 제너레이터, 리스트 버전과 메모리 비교
def high_value_sales_generator(data):
    """amount > 1000인 거래만 하나씩 yield하는 제너레이터. 'amount' 키가 없으면 건너뛴다."""
    for sale in data:
        if sale.get("amount", 0) > 1000:
            yield sale


# 리스트 버전 (컴프리헨션) : 모든 결과를 메모리에 즉시 생성/보관
high_value_list = [sale for sale in sales if sale.get("amount", 0) > 1000]

# 제너레이터 버전 : 값을 미리 만들지 않고 필요할 때마다 하나씩 생성
high_value_gen = high_value_sales_generator(sales)

list_size = sys.getsizeof(high_value_list)
gen_size = sys.getsizeof(high_value_gen)

print("\n[리스트 vs 제너레이터 메모리 크기 비교] (amount > 1000)")
print(f"리스트 버전 크기   : {list_size:,} bytes (원소 {len(high_value_list)}개 포함)")
print(f"제너레이터 버전 크기 : {gen_size:,} bytes (아직 값을 생성하지 않은 상태)")
print(f"차이               : 약 {list_size - gen_size:,} bytes 만큼 리스트가 더 큼")

# 검증 : generator sys.getsizeof < list
try:
    assert gen_size < list_size, "제너레이터 크기가 리스트보다 작지 않음"
    print("-> generator sys.getsizeof < list 확인 (assert 통과)")
except AssertionError as e:
    print(f"[검증 실패] {e}")
    sys.exit(1)

# 제너레이터는 실제로 순회해야 값을 하나씩 만들어낸다 (지연 평가 확인용)
print("\n제너레이터로 순회하며 값 확인 (앞 3개만):")
for i, sale in enumerate(high_value_sales_generator(sales)):
    if i >= 3:
        break
    print(sale)

# 6. month·category 기준 그룹핑 총매출 dict (컴프리헨션 + defaultdict)
# 'month' 또는 'category' 키가 없는 거래는 그룹 목록 산출에서 제외한다.
months = sorted({sale["month"] for sale in sales if "month" in sale})
categories = sorted({sale["category"] for sale in sales if "category" in sale})

# 먼저 딕셔너리 컴프리헨션으로 (month, category) 조합별 총매출을 계산하고,
# 그 결과를 defaultdict(float)로 감싸서 없는 키를 조회해도 KeyError 없이 0.0이 나오게 한다.
month_category_sales = defaultdict(float, {
    (month, category): sum(
        sale.get("amount", 0) for sale in sales
        if sale.get("month") == month and sale.get("category") == category
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

# 7. amount 기준 top3 거래 (내림차순 정렬)
top3_by_amount = sorted(sales, key=lambda sale: sale.get("amount", 0), reverse=True)[:3]

print("\namount 기준 top3 거래 (내림차순):")
for sale in top3_by_amount:
    print(sale)

# 검증 : amount 기준 top3 내림차순 정렬 정확성
try:
    for i in range(len(top3_by_amount) - 1):
        assert top3_by_amount[i].get("amount", 0) >= top3_by_amount[i + 1].get("amount", 0), \
            "top3 금액 내림차순 정렬 오류"
    print("-> top3 금액 내림차순 정렬 정확 (assert 통과)")
except AssertionError as e:
    print(f"[검증 실패] {e}")
    sys.exit(1)