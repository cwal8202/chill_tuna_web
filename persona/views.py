from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Persona
import json
import random


# 함수명      : create_persona
# input      : request
# output     : HttpResponse (render 또는 redirect)
# 작성자      : 주용곤
# 작성일자    : 2025-08-08
# 함수설명    : 
#               1. GET 요청 시, 페르소나 조건 선택 페이지를 렌더링
#               2. 해당 페이지의 버튼/폼에 필요한 선택 옵션 목록을 context를 통해 전달

def create_persona(request):
    context = {
        "age_options": ["20대", "30대", "40대", "50대", "60대 이상", "랜덤"],
        "gender_options": ["남", "여", "랜덤"],
        "job_options": ["회사원", "학생", "자영업자", "프리랜서", "은퇴자", "랜덤"],
        "family_options": ["1인 가구", "부모동거", "부부", "자녀1명", "자녀2명 이상", "기타", "랜덤"],
        "purchase_pattern_options": [
            "통조림/즉석/면류", "생수/음료/커피", "과자/떡/베이커리",
            "냉장/냉동/간편식", "유제품", "건강식품", "랜덤"
        ],
        "customer_value_options": [
            "VIP", "우수고객", "잠재우수고객", "신규고객",
            "잠재이탈고객", "이탈/휴면고객", "랜덤"
        ],
        "lifestyle_options": ["트렌드추종", "가격민감", "브랜드선호", "건강중시", "랜덤"],
    }
    return render(request, "persona/create_persona.html", context)
    

# 함수명      : build_persona
# input       : request
# output      : JsonResponse
# 작성자      : 주용곤
# 작성일자    : 2025-08-08
# 함수설명    : 
#               1. 

def build_persona(request):
    options_map = {
        "age_group": ["20대", "30대", "40대", "50대", "60대 이상", "랜덤"],
        "gender": ["남", "여", "랜덤"],
        "family_structure": ["1인 가구", "부모동거", "부부", "자녀1명", "자녀2명 이상", "기타", "랜덤"],
        "customer_value": ["vip", "우수고객", "잠재우수고객", "신규고객", "잠재이탈고객", "이탈/휴면고객", "랜덤"],
        "job": ["회사원", "학생", "자영업자", "프리랜서", "은퇴자", "랜덤"],
        "purchase_pattern": ["통조림/즉석/면류", "생수/음료/커피", "과자/떡/베이커리", "냉장/냉동/간편식", "유제품", "건강식품", "랜덤"],
        "lifestyle": ["트렌드추종", "가격민감", "브랜드선호", "건강중시", "랜덤"],
    }
    
    # 랜덤 선택 헬퍼
    def pick_random_single(options):
        pure = [option for option in options if option != "랜덤"]
        return random.choice(pure) if pure else None

    def pick_random_multi(options, max_count=None):
        pure = [option for option in options if option != "랜덤"]
        if max_count is None:
            cnt = random.randint(1, len(pure))
        else:
            cnt = random.randint(1, min(max_count, len(pure)))
        return random.sample(pure, cnt)

    # 단일 처리
    def resolve_single(param_name):
        value = request.GET.get(param_name)
        options = options_map[param_name]
        if not value or value.lower() == "랜덤":
            return pick_random_single(options)
        return value

    # 다중 처리
    def resolve_multi(param_name, max_count=None):
        values = request.GET.getlist(param_name)
        options = options_map[param_name]
        if (not values) or ("랜덤" in [v.lower() for v in values]):
            return pick_random_multi(options, max_count)
        whitelisted = []
        seen = set()
        allow = set([option for option in options if option != "랜덤"])
        for value in values:
            if value in allow and value not in seen:
                whitelisted.append(value)
                seen.add(value)
        if max_count and len(whitelisted) > max_count:
            whitelisted = whitelisted[:max_count]
        return whitelisted

    # 모든 항목 처리
    persona_data = {
        "나이": resolve_single("age_group"),
        "성별": resolve_single("gender"),
        "가족구성": resolve_single("family_structure"),
        "고객가치(rfm)": resolve_single("customer_value"),
        "직업": resolve_single("job"),
        "고객취향": resolve_multi("purchase_pattern", max_count=3),
        "라이프스타일": resolve_multi("lifestyle"),
    }

    return JsonResponse(persona_data, json_dumps_params={"ensure_ascii": False})

# 함수명      : chat_persona_view
# input       : request, persona_id
# output      : HttpResponse
# 작성자      : 박동현
# 작성일자    : 2025-08-07
# 함수설명    : 
#               1. URL로부터 특정 페르소나의 ID를 입력받아 해당 ID를 가진 Persona 객체를 데이터베이스에서 조회
#               2. 조회된 페르소나 정보를 받아 실제 채팅이 이루어지는 페이지(chat_persona.html)를 렌더링

def chat_persona_view(request, persona_id):
    persona = Persona.objects.get(id=persona_id)
    context = {
        'persona': persona,
    }
    return render(request, 'persona/chat_persona.html', context)

# 함수명      : find_and_chat_view
# input       : request
# output      : HttpResponse
# 작성자      : 박동현
# 작성일자    : 2025-08-07
# 함수설명    : 
#               1. 사용자가 조건 선택 페이지에서 선택한 조건들을 GET 파라미터로 입력받고 유사도 점수를 계산함
#               2. 가장 높은 점수를 획득한 페르소나를 '최적 페르소나'로 선정함
#               3. 선정된 최적 페르소나의 채팅 페이지로 이동해서 인터뷰를 시작

# 페르소나를 찾아 채팅으로 바로 연결하는 함수 (유사도 검색 로직 수정 필요)
def find_and_chat_view(request):
    selected_age = request.GET.get('age_group')
    selected_gender = request.GET.get('gender')
    selected_family = request.GET.get('family_structure')
    selected_customer_value = request.GET.get('customer_value')
    
    selected_lifestyles = request.GET.getlist('lifestyle') 

    all_personas = Persona.objects.all()
    scores = {}

    for persona in all_personas:
        score = 0
        if selected_age and persona.age_group == selected_age:
            score += 5
        if selected_gender and persona.gender == selected_gender:
            score += 5
        if selected_family and persona.family_structure == selected_family:
            score += 3
        if selected_customer_value and persona.customer_value == selected_customer_value:
            score += 3

        if selected_lifestyles and isinstance(persona.lifestyle, list):
            common_lifestyles = set(selected_lifestyles) & set(persona.lifestyle)
            score += len(common_lifestyles) * 2

        scores[persona.id] = score

    if scores and sum(scores.values()) > 0:
        best_persona_id = max(scores, key=scores.get)
        best_persona = Persona.objects.get(id=best_persona_id)
        # Redirect to chat app's chat view with persona_id and thread_id=0 for a new chat
        return redirect('chat:chat_view', persona_id=best_persona.id, thread_id=0)
    else:
        if all_personas.exists():
            # Redirect to chat app's chat view with the first persona and thread_id=0
            return redirect('chat:chat_view', persona_id=all_personas.first().id, thread_id=0)
        else:
            return redirect('persona:create_persona')
        