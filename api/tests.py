# api/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from persona.models import Persona
import json

class PersonaFilterAPITestCase(TestCase):
    # 함수명     : setUp
    # 함수설명   : 
    #           1. 각 테스트가 실행되기 전에 필요한 '테스트용 데이터'를 미리 생성합니다.
    #           2. 여기서는 테스트에 사용할 페르소나 3명을 임시 데이터베이스에 만듭니다.
    @classmethod
    def setUpTestData(cls):
        Persona.objects.create(name="김테스트", segment="VIP", age_group="30대", gender="여", job="개발자", family_structure="1인 가구", customer_value="VIP", persona_summary_tag="...")
        Persona.objects.create(name="이테스트", segment="우수고객", age_group="40대", gender="남", job="기획자", family_structure="부부", customer_value="우수고객", persona_summary_tag="...")
        Persona.objects.create(name="박테스트", segment="신규고객", age_group="30대", gender="여", job="마케터", family_structure="자녀 1명", customer_value="신규고객", persona_summary_tag="...")

    # 함수명     : test_filter_api_no_params
    # 함수설명   : 
    #           1. 아무 조건 없이 필터 API를 호출했을 때, 모든 페르소나(3명)가 반환되는지 테스트합니다.
    def test_filter_api_no_params(self):
        client = Client()
        # 'api:persona_filter_api'라는 이름의 URL을 호출합니다.
        response = client.get(reverse('api:persona_filter_api'))
        
        # 1. 응답 상태 코드가 200 (성공)인지 확인합니다.
        self.assertEqual(response.status_code, 200)
        
        # 2. 반환된 데이터의 개수가 우리가 만든 페르소나 수(3개)와 일치하는지 확인합니다.
        self.assertEqual(len(response.json()), 3)

    # 함수명     : test_filter_api_with_params
    # 함수설명   : 
    #           1. '30대 여성'이라는 조건으로 API를 호출했을 때, 조건에 맞는 페르소나(2명)만 정확히 반환되는지 테스트합니다.
    def test_filter_api_with_params(self):
        client = Client()
        # ?age_group=30대&gender=여 라는 파라미터를 붙여서 URL을 호출합니다.
        url = reverse('api:persona_filter_api') + '?age_group=30대&gender=여'
        response = client.get(url)

        # 1. 응답 상태 코드가 200 (성공)인지 확인합니다.
        self.assertEqual(response.status_code, 200)
        
        # 2. 반환된 데이터의 개수가 '30대 여성' 조건에 맞는 2개인지 확인합니다.
        self.assertEqual(len(response.json()), 2)