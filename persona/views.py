from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Persona
import json
import random
from django.contrib.auth.decorators import login_required      


# 함수명      : create_persona
# input      : request
# output     : HttpResponse (render 또는 redirect)
# 작성자      : 주용곤
# 작성일자    : 2025-08-28
# 함수설명    : 
#               1. GET 요청 시, 페르소나 조건 선택 페이지를 렌더링
#               2. 해당 페이지의 버튼/폼에 필요한 선택 옵션 목록을 context를 통해 전달
# @login_required
def create_persona(request):
    context = {
        "age_options": ["랜덤", "20대", "30대", "40대", "50대", "60대 이상"],
        "gender_options": ["랜덤", "남자", "여자"],
        "job_options": ["랜덤", "관리자", "군인", "기능원 및 관련 기능 종사자", "농림어업 숙련 종사자", "단순노무 종사자", "사무 종사자",
            "서비스 종사자", "전문가 및 관련 종사자", "판매 종사자", "장치·기계 조작 및 조립 종사자", "주부", "취업 준비 중", "학생"],
        "household_options": ["랜덤", "1인 가구", "1세대가족", "2세대가족"],
        "income_month_options": ["랜덤", "100만원 미만", "100-200만원 미만", "200-300만원 미만", "300-400만원 미만", "400-500만원 미만", 
            "500-600만원 미만", "600-700만원 미만", "700-800만원 미만", "800-900만원 미만", "900-1000만원 미만", "1,000만원 이상"],
        "segment_options": ["랜덤", "실속형 미식가", "건강 추구형 소비자", "트렌드 주도형 소비자"],
    }
    return render(request, "persona/create_persona.html", context)
    

# 함수명      : build_persona
# input       : request
# output      : JsonResponse
# 작성자      : 주용곤
# 작성일자    : 2025-08-28
# 함수설명    : 

def build_persona(request):
    options_map = {
        "age": ["랜덤", "20대", "30대", "40대", "50대", "60대 이상"],
        "gender": ["랜덤", "남자", "여자"],
        "job": ["랜덤", "관리자", "군인", "기능원 및 관련 기능 종사자", "농림어업 숙련 종사자", "단순노무 종사자", "사무 종사자",
            "서비스 종사자", "전문가 및 관련 종사자", "판매 종사자", "장치·기계 조작 및 조립 종사자", "주부", "취업 준비 중", "학생"],
        "household": ["랜덤", "1인 가구", "1세대가족", "2세대가족"],
        "income_month": ["랜덤", "100만원 미만", "100-200만원 미만", "200-300만원 미만", "300-400만원 미만", "400-500만원 미만", 
            "500-600만원 미만", "600-700만원 미만", "700-800만원 미만", "800-900만원 미만", "900-1000만원 미만", "1,000만원 이상"],
        "segment": ["랜덤", "실속형 미식가", "건강 추구형 소비자", "트렌드 주도형 소비자"],
    }
    
    # 랜덤 선택 헬퍼
    def pick_random_single(options):
        pure = [option for option in options if option != "랜덤"]
        return random.choice(pure) if pure else None

    # 단일 처리
    def resolve_single(param_name):
        value = request.GET.get(param_name)
        options = options_map[param_name]
        if not value or value.lower() == "랜덤":
            return pick_random_single(options)
        return value

    # 모든 항목 처리
    persona_data = {
        "성별": resolve_single("gender"),
        "나이": resolve_single("age_group"),       
        "직업": resolve_single("job"),
        "가족구성": resolve_single("household"), 
        "소득": resolve_single("income_month"),
        "라이프스타일": resolve_single("segment"),
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
# 작성자      : 주용곤
# 작성일자    : 2025-08-28
# 함수설명    : 
#               1. 사용자가 조건 선택 페이지에서 선택한 조건들을 GET 파라미터로 입력받고 가중치를 계산함
#               2. 가중치가 페르소나를 '최적 페르소나'로 선정함
#               3. 선정된 최적 페르소나의 채팅 페이지로 이동해서 인터뷰를 시작

# 페르소나를 찾아 채팅으로 바로 연결하는 함수
def find_and_chat_view(request):
    selected_criteria = {
        'gender': request.GET.get('gender'),
        'age': request.GET.get('age'),
        'job': request.GET.get('job'),
        'household': request.GET.get('household'),
        'income_month': request.GET.get('income_month'),
        'segment': request.GET.get('segment'),
    }

    RANDOM_OPTIONS = {
        'gender': ['남자', '여자'],
        'age': ['20대', '30대', '40대', '50대', '60대 이상'],
        'job': ["관리자", "군인", "기능원 및 관련 기능 종사자", "농림어업 숙련 종사자", "단순노무 종사자", "사무 종사자",
                "서비스 종사자", "전문가 및 관련 종사자", "판매 종사자", "장치·기계 조작 및 조립 종사자", "주부", "취업 준비 중", "학생"],
        'household': ["1인 가구", "1세대가족", "2세대가족"],
        'income_month': ["100만원 미만", "100-200만원 미만", "200-300만원 미만", "300-400만원 미만", "400-500만원 미만", 
                         "500-600만원 미만", "600-700만원 미만", "700-800만원 미만", "800-900만원 미만", "900-1000만원 미만", "1,000만원 이상"],
        'segment': ["실속형 미식가", "건강 추구형 소비자", "트렌드 주도형 소비자"],
    }

    for key, value in selected_criteria.items():
        if value == '랜덤' or not value:
            selected_criteria[key] = random.choice(RANDOM_OPTIONS[key])

    fixed_keys = ['gender', 'age']
    fixed_weights = {'gender': 5, 'age': 5}

    flexible_weights = {
        'job': 1,
        'household': 3,
        'income_month': 2,
        'segment': 4,
    }

    all_personas = Persona.objects.all()

    if not all_personas.exists():
        return redirect('persona:create_persona')
    
    filtered = all_personas
    for key in fixed_keys:
        value = selected_criteria.get(key)
        if value:
            filtered = filtered.filter(**{key: value})

    if not filtered.exists():
        return redirect('persona:create_persona')

    sorted_flexible_keys = sorted(flexible_weights, key=lambda k: -flexible_weights[k])
    for loosen_level in range(len(sorted_flexible_keys) + 1):
        active_keys = sorted_flexible_keys[:len(sorted_flexible_keys) - loosen_level]
        temp_filtered = filtered

        for key in active_keys:
            value = selected_criteria.get(key)
            if value:
                temp_filtered = temp_filtered.filter(**{key: value})

        if temp_filtered.exists():
            best_persona = random.choice(temp_filtered)
            break
        else:
        # flexible 조건까지 모두 불일치할 경우 → gender/age 일치 대상 중 랜덤
            best_persona = random.choice(list(filtered))

    matched_fixed_score = sum(
        fixed_weights[key]
        for key in fixed_keys
        if selected_criteria.get(key) and getattr(best_persona, key) == selected_criteria[key]
    )

    matched_flexible_score = sum(
        flexible_weights[key]
        for key in flexible_weights
        if selected_criteria.get(key) and getattr(best_persona, key) == selected_criteria[key]
    )

    total_score_possible = sum(fixed_weights.values()) + sum(flexible_weights.values())
    matched_total_score = matched_fixed_score + matched_flexible_score

    match_percentage = round((matched_total_score / total_score_possible) * 100, 1)

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.headers.get("Accept", "").startswith("application/json"):
        return JsonResponse({
            "persona_id": best_persona.id,
            "match_percentage": match_percentage,
            "redirect_url": f"/chat/{best_persona.id}/0/",
            "persona_data": {
                "name": best_persona.name,
                "gender": best_persona.gender,
                "age": best_persona.age,
                "household": best_persona.household,
                "job": best_persona.job,
                "region": best_persona.region,
                "education": best_persona.education,
                "income_month": best_persona.income_month,
                "income_status": best_persona.income_status,
                "marriage" : best_persona.marriage,
                "segment": best_persona.segment,
                # "persona_summary_tag": best_persona.persona_summary_tag 
            }
        })

    return redirect('chat:chat_view', persona_id=best_persona.id, thread_id=0)