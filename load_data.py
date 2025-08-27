# load_data.py
# 페르소나를 저장한 json파일을 모델에 맞춰 집어넣는 파일로 임시사용용

import os
import django
import json

# Django 환경 설정 (프로젝트 이름에 맞게 수정하세요)
# manage.py가 있는 폴더에서 실행하기 위함.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

# 모델 임포트
from persona.models import Persona # '앱이름'을 실제 앱 이름으로 변경하세요

# 함수명      : load_persona_data
# input       : 페르소나 정보를 담은 json 파일
# output      : 데이터 베이스에 페르소나 정보 저장
# 작성자      : 박진성
# 작성일자    : 2025-08-08
# 함수설명    : 
#               1. 매핑사전을 이용해 json 항목과 모델의 스키마를 매핑한다
#               2. json 파일을 로드 후 새 딕셔너리를 만들어 JSON 키를 모델 필드명으로 변경
#               3. 페르소나 모델 객체를 생성 후 bulk_create를 사용해 대량으로 데이터 삽입
    
def load_persona_data():
    # JSON 파일의 경로
    # json_file_path = 'persona/static/json/personas_batch1.json' # 페르소나 저장 파일명
    json_file_path = 'persona/static/json/personas_batch2-6.json'

    # 매핑 사전 
    field_mapping = {
        "이름": "name",
        "마이크로세그먼트": "segment",
        "연령대": "age_group",
        "성별": "gender",
        "직업": "job",
        "가족구성": "family_structure",
        "고객가치(RFM)": "customer_value",
        "구매패턴": "purchase_pattern",
        "라이프스타일": "lifestyle",
        "페르소나 요약 태그": "persona_summary_tag",
    }

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        persona_objects = []
        for item in data:
            # 새로운 딕셔너리를 만들어서 JSON 키를 모델 필드명으로 변경
            new_item = {}
            for json_key, model_field in field_mapping.items():
                if json_key in item:
                    new_item[model_field] = item[json_key]

            # Persona 객체 생성
            persona_objects.append(Persona(**new_item))

        # bulk_create를 사용해 대량으로 데이터 삽입
        Persona.objects.bulk_create(persona_objects)
        print(f"{len(persona_objects)}개의 페르소나 데이터가 성공적으로 저장되었습니다.")

    except FileNotFoundError:
        print(f"오류: {json_file_path} 파일을 찾을 수 없습니다.")
    except Exception as e:
        print(f"데이터 삽입 중 오류 발생: {e}")

if __name__ == '__main__':
    load_persona_data()