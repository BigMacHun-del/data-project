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
#--------------- 실습 1 끝
# 0.7 : 2026년 7월 15일 - 파일 로딩 로직을 safe_load_csv() 함수로 분리
# 0.8 : 2026년 7월 15일 - Pydantic v2 검증 파이프라인 추가
# 0.9 : 2026년 7월 15일 - valid 레코드를 CSV로, errors를 JSON으로 저장하고
#                        다시 읽어 건수가 일치하는지 검증하는 기능 추가
# 0.10 : 2026년 7월 15일 - 자체 테스트 추가
#         - safe_load_csv가 존재하지 않는 파일에 None을 반환하는지 assert로 확인
#         - ValidationError 발생 시 오류 내용을 콘솔에 즉시 출력
#         - valid 4건 / errors 3건이 되도록 만든 테스트 데이터로 파이프라인 검증
#         - 재로딩 후 len(reloaded)==4 assert 검증
#         - safe_load_csv가 "sales = [...]" 할당문 형식뿐 아니라
#           순수 JSON 배열 형식(예: Python_Practice2_Data.json)도 예외 없이 읽도록 수정
# --------------

import csv
import json
import logging
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from pydantic import BaseModel, ValidationError, field_validator
except ImportError:
    print("[오류] pydantic 패키지가 필요합니다. 'pip install pydantic' 실행 후 다시 시도하세요.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 파일 로딩 함수
def safe_load_csv(filepath):
    """
    매출 데이터 파일을 안전하게 읽어 dict 리스트로 반환한다.

    - 파일이 없거나(FileNotFoundError) 읽기/파싱 중 오류가 발생하면
      logger.error로 기록하고 None을 반환한다.
    - 정상적으로 읽고 파싱에 성공하면 dict 리스트를 반환하며 logger.info로 기록한다.
    - 성공/실패 여부와 관계없이 finally에서 '로딩 종료'를 출력한다.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        stripped_content = content.strip()

        if stripped_content.startswith("[") or stripped_content.startswith("{"):
            # 이미 순수 JSON 형식인 경우 그대로 파싱
            json_str = stripped_content
        elif "=" in content:
            # "변수 = [...]" 형태의 파이썬 할당문인 경우 '=' 뒤 리스트만 추출
            json_str = content.split("=", 1)[1].strip()
        else:
            logger.error("지원하지 않는 파일 형식입니다: %s", filepath)
            return None

        data = json.loads(json_str)

        if not isinstance(data, list) or not data:
            logger.error("매출 데이터가 비어 있거나 리스트 형태가 아닙니다: %s", filepath)
            return None

        logger.info("파일 로딩 성공: %s (거래 %d건)", filepath, len(data))
        return data

    except FileNotFoundError:
        logger.error("파일을 찾을 수 없습니다: %s", filepath)
        return None
    except OSError as e:
        logger.error("파일을 읽는 중 문제가 발생했습니다: %s", e)
        return None
    except json.JSONDecodeError as e:
        logger.error("JSON 파싱에 실패했습니다: %s", e)
        return None
    finally:
        print("로딩 종료")


class SalesRecord(BaseModel):
    #개별 매출 거래 한 건을 검증하기 위한 Pydantic v2 스키마.
    date: str
    region: str
    amount: float
    category: str | None = None

    @field_validator("date", "region")
    @classmethod
    def not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("빈 값은 허용되지 않습니다.")
        return value

    @field_validator("amount")
    @classmethod
    def must_be_positive(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("amount는 0보다 커야 합니다.")
        return value


def validate_sales(raw_sales):
    """
    raw_sales(dict 리스트)를 SalesRecord 스키마로 한 건씩 검증한다.
    원본 데이터의 'month' 필드를 SalesRecord의 'date' 필드로 매핑해서 검증한다.
    ValidationError가 발생하면 오류 내용을 즉시 콘솔에 출력한다.

    반환값: (검증 통과한 원본 dict 리스트, 통과한 SalesRecord 리스트, 오류 리포트 리스트)
    """
    valid_rows, valid_records, errors = [], [], []
    for i, row in enumerate(raw_sales):
        try:
            record = SalesRecord(
                date=row.get("month", ""),
                region=row.get("region", ""),
                amount=row.get("amount", 0),
                category=row.get("category"),
            )
            valid_rows.append(row)
            valid_records.append(record)
        except ValidationError as e:
            print(f"[검증 오류] row {i}: {e}")
            errors.append({"row": i, "error": str(e)})
    return valid_rows, valid_records, errors


# 결과 파일 저장 함수 : valid는 CSV로, errors는 JSON으로 저장
def save_results(valid_records, errors, valid_path="valid.csv", errors_path="errors.json"):
    """
    검증을 통과한 valid_records를 CSV 파일로, errors를 JSON 파일로 저장한다.
    파일 쓰기 중 문제가 발생하면 logger.error로 기록한다.
    """
    fieldnames = ["date", "region", "amount", "category"]
    try:
        with open(valid_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for record in valid_records:
                writer.writerow(record.model_dump())
    except OSError as e:
        logger.error("valid.csv 저장 중 문제가 발생했습니다: %s", e)
        return False

    try:
        Path(errors_path).write_text(
            json.dumps(errors, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        logger.error("errors.json 저장 중 문제가 발생했습니다: %s", e)
        return False

    logger.info("결과 파일 저장 완료: %s(%d건), %s(%d건)", valid_path, len(valid_records), errors_path, len(errors))
    return True


# 재로딩 검증 함수 : 저장된 파일을 다시 읽어 건수가 일치하는지 확인
def reload_and_verify(valid_path, errors_path, expected_valid_count, expected_error_count):
    """
    저장한 valid.csv와 errors.json을 다시 읽어, 저장 전 건수와 일치하는지 assert로 검증한다.
    파일이 없거나 읽기/파싱에 실패하면 logger.error로 기록하고 False를 반환한다.
    """
    try:
        with open(valid_path, "r", encoding="utf-8") as f:
            reloaded_valid = list(csv.DictReader(f))
    except FileNotFoundError:
        logger.error("재로딩 실패: %s 파일을 찾을 수 없습니다.", valid_path)
        return False
    except OSError as e:
        logger.error("재로딩 중 문제가 발생했습니다: %s", e)
        return False

    try:
        reloaded_errors = json.loads(Path(errors_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.error("재로딩 실패: %s 파일을 찾을 수 없습니다.", errors_path)
        return False
    except json.JSONDecodeError as e:
        logger.error("errors.json 재로딩 중 파싱에 실패했습니다: %s", e)
        return False

    try:
        assert len(reloaded_valid) == expected_valid_count, \
            f"valid.csv 건수 불일치: 저장 {expected_valid_count}건, 재로딩 {len(reloaded_valid)}건"
        assert len(reloaded_errors) == expected_error_count, \
            f"errors.json 건수 불일치: 저장 {expected_error_count}건, 재로딩 {len(reloaded_errors)}건"
    except AssertionError as e:
        logger.error("재로딩 검증 실패: %s", e)
        return False

    logger.info("재로딩 검증 통과: valid.csv %d건, errors.json %d건", len(reloaded_valid), len(reloaded_errors))
    return True


# --------------------------------------------------------
# Checkpoint 자체 테스트
# --------------------------------------------------------
# 4건은 유효, 3건은 의도적으로 검증에 실패하도록 구성한 테스트 데이터
TEST_SALES_DATA = [
    {"month": "2024-01", "region": "서울", "amount": 1000, "category": "전자"},   # valid
    {"month": "2024-01", "region": "부산", "amount": 500, "category": "의류"},    # valid
    {"month": "2024-02", "region": "대구", "amount": 700, "category": "식품"},    # valid
    {"month": "2024-02", "region": "인천", "amount": 300, "category": None},      # valid (category 없어도 됨)
    {"month": "", "region": "광주", "amount": 400, "category": "전자"},           # invalid: date(month) 비어있음
    {"month": "2024-03", "region": "", "amount": 200, "category": "의류"},        # invalid: region 비어있음
    {"month": "2024-03", "region": "대전", "amount": -50, "category": "식품"},    # invalid: amount가 0 이하
]


def run_self_test():
    """
    safe_load_csv / validate_sales / save_results / reload_and_verify 파이프라인이
    의도한 대로 동작하는지 검증하는 자체 테스트.

    Checkpoint 항목:
      1) safe_load_csv 동작 + assert None 통과
      2) ValidationError 발생 시 오류 내용 출력
      3) valid 4건 / errors 3건 assert 통과
      4) 재로딩 후 len(reloaded)==4 통과
    """
    print("\n[Checkpoint 자체 테스트 시작]")

    # 1) safe_load_csv 동작 + assert None 통과 (존재하지 않는 파일)
    result = safe_load_csv("존재하지_않는_파일.json")
    assert result is None, "safe_load_csv가 존재하지 않는 파일에 대해 None을 반환하지 않음"
    print("-> safe_load_csv(존재하지 않는 파일) None 반환 확인 (assert 통과)")

    # 2) validate_sales 실행 (ValidationError 발생 시 오류 내용은 함수 내부에서 즉시 출력됨)
    test_valid_rows, test_valid_records, test_errors = validate_sales(TEST_SALES_DATA)

    # 3) valid 4건 / errors 3건 assert 통과
    assert len(test_valid_records) == 4, f"valid 건수 불일치: {len(test_valid_records)}건 (기대값 4건)"
    assert len(test_errors) == 3, f"errors 건수 불일치: {len(test_errors)}건 (기대값 3건)"
    print(f"-> valid {len(test_valid_records)}건 / errors {len(test_errors)}건 assert 통과")

    # 4) 결과 저장 후 재로딩하여 len(reloaded) == 4 assert 통과
    save_results(test_valid_records, test_errors, valid_path="test_valid.csv", errors_path="test_errors.json")

    with open("test_valid.csv", "r", encoding="utf-8") as f:
        reloaded = list(csv.DictReader(f))
    assert len(reloaded) == 4, f"재로딩 건수 불일치: {len(reloaded)}건 (기대값 4건)"
    print(f"-> 재로딩 후 len(reloaded)=={len(reloaded)} 통과")

    print("[Checkpoint 자체 테스트 완료] 모든 항목 통과\n")


try:
    run_self_test()
except AssertionError as e:
    print(f"[Checkpoint 검증 실패] {e}")
    sys.exit(1)

raw_sales = safe_load_csv("Python_Practice2_Data.json")
if raw_sales is None:
    sys.exit(1)

sales, valid_records, validation_errors = validate_sales(raw_sales)
print(f"유효: {len(valid_records)}건, 오류: {len(validation_errors)}건")

if not save_results(valid_records, validation_errors):
    sys.exit(1)

if not reload_and_verify("valid.csv", "errors.json", len(valid_records), len(validation_errors)):
    sys.exit(1)

if not sales:
    logger.error("검증을 통과한 유효 데이터가 없어 분석을 진행할 수 없습니다.")
    sys.exit(1)

# 1. amount >= 1000인 거래만 필터링 (리스트 컴프리헨션)
high_value_sales = [sale for sale in sales if sale.get("amount", 0) >= 1000]

print(f"amount >= 1000 거래 건수: {len(high_value_sales)}")
for sale in high_value_sales:
    print(sale)

# 2. 지역별 총매출 dict (딕셔너리 컴프리헨션)
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
region_counts = Counter(sale.get("region", "미상") for sale in sales)

print("\n지역별 거래 건수 (Counter):")
for region, count in region_counts.items():
    print(f"{region}: {count}건")

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
category_amounts = defaultdict(list)
for sale in sales:
    if "category" in sale and "amount" in sale:
        category_amounts[sale["category"]].append(sale["amount"])

print("\n카테고리별 amount 리스트 (defaultdict):")
for category, amounts in category_amounts.items():
    print(f"{category}: {amounts}")

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


high_value_list = [sale for sale in sales if sale.get("amount", 0) > 1000]
high_value_gen = high_value_sales_generator(sales)

list_size = sys.getsizeof(high_value_list)
gen_size = sys.getsizeof(high_value_gen)

print("\n[리스트 vs 제너레이터 메모리 크기 비교] (amount > 1000)")
print(f"리스트 버전 크기   : {list_size:,} bytes (원소 {len(high_value_list)}개 포함)")
print(f"제너레이터 버전 크기 : {gen_size:,} bytes (아직 값을 생성하지 않은 상태)")
print(f"차이               : 약 {list_size - gen_size:,} bytes 만큼 리스트가 더 큼")

try:
    assert gen_size < list_size, "제너레이터 크기가 리스트보다 작지 않음"
    print("-> generator sys.getsizeof < list 확인 (assert 통과)")
except AssertionError as e:
    print(f"[검증 실패] {e}")
    sys.exit(1)

print("\n제너레이터로 순회하며 값 확인 (앞 3개만):")
for i, sale in enumerate(high_value_sales_generator(sales)):
    if i >= 3:
        break
    print(sale)

# 6. month·category 기준 그룹핑 총매출 dict (컴프리헨션 + defaultdict)
months = sorted({sale["month"] for sale in sales if "month" in sale})
categories = sorted({sale["category"] for sale in sales if "category" in sale})

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