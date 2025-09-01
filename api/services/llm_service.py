# api/services/llm_service.py
from __future__ import annotations

import os
import re
from typing import Optional, List, Dict

from dotenv import load_dotenv
from . import persona_service

try:
    from chat.models import ChatMessage, ChatThread
    HAS_CHAT_MODELS = True
except Exception:
    ChatMessage = ChatThread = None
    HAS_CHAT_MODELS = False


def _get_openai_client():
    from openai import OpenAI, APIError
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    client = OpenAI(api_key=api_key)
    return client, APIError


GREETING_PAT = re.compile(r"^(안녕하세요|안녕|하이|hello|hi)[!,\.\s]*$", re.IGNORECASE)

REFUSAL_TEXT = (
    "미안해요! 저는 식품/가공식품/음료 제품의 판매량·수요예측과 그것을 늘리는 방법"
    "(예상 구매개수·월별 패턴·가격/프로모션/계절성/채널/번들/구독 등)에만 답해요. "
    "제품명과 기간/조건을 알려주시면 바로 추정해볼게요."
)
REFUSAL_PREFIX = "미안해요! 저는 식품/가공식품/음료 제품의 판매량·수요예측"

YES_PAT = re.compile(r"^(예|네|yes)\b", re.I)
NO_PAT = re.compile(r"^(아니오|아니요|no)\b", re.I)

FOOD_HINTS = (
    "우유","요거트","라떼","커피","차","주스","음료","생수",
    "라면","과자","쿠키","스낵","초콜릿","시리얼","빵",
    "햇반","즉석밥","밀키트","hmr","냉동","통조림","참치","햄","소시지","반찬","소스","쌀"
)

INTENT_HINTS = (
    "살래","사 말래","사말래","사야","사요","구매","구입",
    "몇개","몇 개","수량","빈도","출시",
    "프로모션","가격","할인","원","예측","판매","수요",
    "재구매","구독","번들","묶음","채널","유통","행사",
)

LIKE_TRIGGERS = (
    "좋아하는 음식","좋아하는 제품","좋아하는 식품","좋아하는 메뉴",
    "선호하는 음식","선호하는 제품","선호하는 식품","선호하는 메뉴",
    "뭐 좋아해","무슨 음식 좋아","최애"
)
DISLIKE_TRIGGERS = (
    "싫어하는 음식","싫어하는 제품","싫어하는 식품","싫어하는 메뉴",
    "비선호 음식","비선호 제품","비선호 식품",
    "안 좋아하는 음식","무슨 음식 싫어","별로 안 좋아해"
)
LIKE_RE = re.compile(r"(좋아|선호)[^\n]{0,20}(음식|제품|식품|메뉴)|(음식|제품|식품|메뉴)[^\n]{0,20}(좋아|선호)")
DISLIKE_RE = re.compile(r"(싫어|비선호|안\s*좋아)[^\n]{0,20}(음식|제품|식품|메뉴)|(음식|제품|식품|메뉴)[^\n]{0,20}(싫어|비선호|안\s*좋아)")

NUM_PAT = re.compile(r"(몇\s*개|\d+\s*개|\d+\s*원)")


def _parse_yes_no(token: str) -> Optional[bool]:
    t = (token or "").strip().lower().strip(".! \n\t")
    if YES_PAT.match(t):
        return True
    if NO_PAT.match(t):
        return False
    return None


def _heuristic_food_in_scope(text: str) -> bool:
    t = (text or "").lower()
    has_food = any(k in t for k in FOOD_HINTS)
    has_intent = any(k in t for k in INTENT_HINTS)
    compare_follow = any(k in t for k in (" vs ", "vs", "대비", "비교"))
    return has_food and (has_intent or compare_follow)


def _is_refusal_msg(text: str) -> bool:
    return (text or "").strip().startswith(REFUSAL_PREFIX)


def _should_include_user_history(text: str) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    if GREETING_PAT.match(t):
        return True
    if _heuristic_food_in_scope(t):
        return True
    if any(k in t for k in LIKE_TRIGGERS) or any(k in t for k in DISLIKE_TRIGGERS):
        return True
    if LIKE_RE.search(t) or DISLIKE_RE.search(t):
        return True
    return False


def _load_history_text(thread_id: Optional[int], limit: int = 10, char_limit: int = 1800) -> str:
    if not (HAS_CHAT_MODELS and thread_id):
        return ""
    qs = (
        ChatMessage.objects.filter(thread_id=thread_id)
        .order_by("id").only("sender", "message")
    )
    items = list(qs)[-limit:]
    lines: List[str] = []
    for m in items:
        if m.sender == "persona":
            if _is_refusal_msg(m.message):
                continue
            who = "페르소나"
        else:
            if not _should_include_user_history(m.message):
                continue
            who = "사용자"
        lines.append(f"{who}: {m.message}")
    return "\n".join(lines)[-char_limit:]


def _load_history_messages(thread_id: Optional[int], limit: int = 16) -> List[Dict[str, str]]:
    if not (HAS_CHAT_MODELS and thread_id):
        return []
    qs = (
        ChatMessage.objects.filter(thread_id=thread_id)
        .order_by("id").only("sender", "message")
    )
    items = list(qs)[-limit:]
    out: List[Dict[str, str]] = []
    for m in items:
        if m.sender == "persona":
            if _is_refusal_msg(m.message):
                continue
            out.append({"role": "assistant", "content": m.message})
        else:
            if not _should_include_user_history(m.message):
                continue
            out.append({"role": "user", "content": m.message})
    return out


def _classify_food_scope(client, model_name: str, question: str) -> bool:
    if _heuristic_food_in_scope(question):
        return True
    sys = """다음 문장이 '식품/가공식품/음료' 제품의 판매량·수요예측 또는 그것을 늘리는 전략과 직접적으로 관련이 있는지 판정하라.
- IN-SCOPE: 식품류 전반에 관한 질문으로서, 구매 개수/월별 패턴/가격·프로모션/계절성/채널/번들/구독/재구매 전략, 또는 **제품 간 비교·선호·추천**.
- OUT-OF-SCOPE: 비식품, 일상대화, 맞춤법/번역/일반 글쓰기 등.
반드시 한 단어로만 출력: 예 또는 아니오."""
    user = f"문장: {question}"
    try:
        res = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
            temperature=0,
            max_tokens=2,
        )
        val = _parse_yes_no(res.choices[0].message.content)
    except Exception:
        val = None
    if val is True:
        return True
    if _heuristic_food_in_scope(question):
        return True
    return False


def _llm_scope_decider(client, model_name: str, thread_id: Optional[int], new_utterance: str) -> Optional[bool]:
    history = _load_history_text(thread_id, limit=12, char_limit=1600)
    text = (new_utterance or "").strip()
    system = """너는 '도메인/후속 판별기'다. 다음 대화의 최근 흐름과 새 발화를 보고, 주제가 '식품/가공식품/음료' 제품과 관련된
구매·수요·가격·프로모션·계절성·채널·번들·구독·재구매·월별 패턴 또는 **제품 간 비교/선호/추천** 의사결정인지 판정하라.
후속 축약형(예: '그럼 초코가 낫지?', '어때?', 'vs?')도 IN이다.
OUT은 비식품 주제/일상대화/정치/날씨/맞춤법·번역·글쓰기·코딩 같은 일반 작업이다.
반드시 한 단어로만 출력: 예 또는 아니오."""
    examples = """[예시]
문장: 민트커피 vs 초코커피 뭐가 더 잘 팔릴까? → 예
문장: 가격 2천원이면 몇 개 사게 될까? → 예
문장: 다음주 장마면 판매가 늘까? → 예
문장: 맞춤법 맞춰줘. → 아니오
문장: 오늘 날씨 어때? → 아니오
문장: 전자레인지 고장났어. → 아니오
"""
    user = f"[히스토리]\n{history}\n\n{examples}[새 발화]\n{text}\n답:"
    try:
        res = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0,
            max_tokens=2,
        )
        return _parse_yes_no(res.choices[0].message.content)
    except Exception:
        return None


def _is_in_scope_food(user_input: str, thread_id: Optional[int], client, model_name: str) -> bool:
    val = _llm_scope_decider(client, model_name, thread_id, user_input)
    if val is not None:
        return val
    if _heuristic_food_in_scope(user_input):
        return True
    return _classify_food_scope(client, model_name, user_input)


def _extract_context_snapshot(client, model_name: str, thread_id: Optional[int], user_input: str) -> str:
    hist = _load_history_text(thread_id, limit=12, char_limit=1800)
    system = (
        "다음 대화 히스토리와 최신 발화를 보고, 현재 논의 중인 식품 제품의 "
        "'상품명/규격', '가격(있으면 숫자)', '기간(예: 1개월)', '특성(예: 락토프리, 친환경 포장)'을 "
        "한두 문장으로 요약하라. 모르면 추정하지 말고 생략하라. "
        "예: '현재 대상: 초코우유 250ml 락토프리, 기간 1개월, 가격 1,500원 가정, 친환경 포장 언급됨.'"
    )
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"[히스토리]\n{hist}\n\n[최신]\n{user_input}"},
            ],
            temperature=0,
            max_tokens=120,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception:
        return ""


PRICE_RE = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+)\s*원")


def _extract_prices(*texts: str) -> List[int]:
    vals: List[int] = []
    for t in texts or []:
        for m in PRICE_RE.finditer(t or ""):
            try:
                n = int(m.group(1).replace(",", ""))
                if n > 0:
                    vals.append(n)
            except Exception:
                pass
    return vals


def _is_unrealistic_price(product_text: str, price: int) -> bool:
    t = (product_text or "").lower()
    if any(k in t for k in ("우유", "요거트", "유제품", "음료", "주스", "생수", "커피", "차", "라떼")):
        return price > 10000
    if any(k in t for k in ("과자", "쿠키", "스낵", "초콜릿", "시리얼", "빵")):
        return price > 15000
    if any(k in t for k in ("햇반", "즉석밥", "hmr", "밀키트", "냉동", "통조림", "참치", "햄", "소시지", "반찬", "소스", "쌀")):
        return price > 50000
    return price > 100000


def _price_guard_response(persona, product_hint: str, price: int) -> str:
    product_label = product_hint or "해당 제품"
    return (
        f"예상 구매수량은 0개, 기간은 1개월입니다.\n\n"
        f"이유:\n"
        f"1) 가격({price:,}원)이 B2C 소매 단품 기준으로 비현실적으로 높아 수요가 거의 발생하지 않습니다.\n"
        f"2) 대체재 대비 지불의사(WTP)를 크게 초과합니다.\n"
        f"3) 프로모션으로도 가격 장벽 해소가 어려워 재구매 가능성이 낮습니다.\n\n"
        f"권장: {product_label}의 상시가는 합리 구간으로 조정하고, 체험용 소용량/번들/구독 등 반복 구매 장치를 병행하세요."
    )


def _apply_price_guard(persona, snapshot: str, user_input: str) -> Optional[str]:
    product_hint = snapshot or user_input
    prices = _extract_prices(snapshot, user_input)
    if not prices:
        return None
    worst = max(prices)
    if _is_unrealistic_price(product_hint, worst):
        return _price_guard_response(persona, product_hint, worst)
    return None


FIRST_COUNT_PAT = re.compile(r"(\d{1,3})\s*개")

HAM_HINTS = ("햄", "스팸", "리챔", "런천미트", "캔햄", "오믈레", "오믈렛")
TUNA_HINTS = ("참치", "참치캔", "동원참치", "가다랑어")
SAUCE_HINTS = ("소스", "양념", "드레싱")
BEV_HINTS = ("우유", "요거트", "라떼", "커피", "주스", "음료", "생수", "차")
HMR_HINTS = ("햇반", "즉석밥", "HMR", "밀키트", "냉동", "간편식")


def _product_category_from_text(text: str) -> str:
    t = (text or "").lower()
    if any(k in t for k in (h.lower() for h in HAM_HINTS)):
        return "canned_ham"
    if any(k in t for k in (h.lower() for h in TUNA_HINTS)):
        return "canned_tuna"
    if any(k in t for k in (h.lower() for h in SAUCE_HINTS)):
        return "sauce"
    if any(k in t for k in (h.lower() for h in BEV_HINTS)):
        return "beverage"
    if any(k in t for k in (h.lower() for h in HMR_HINTS)):
        return "hmr"
    return "default"


def _household_bucket_from_tag(tag: str) -> str:
    tag = (tag or "")
    if any(x in tag for x in ("3인", "4인")):
        return "small"
    if any(x in tag for x in ("5인", "6인", "대가족")):
        return "large"
    if "2인" in tag:
        return "small"
    if "1인" in tag:
        return "single"
    return "single"


TYPICAL_MONTHLY_RANGE = {
    "canned_ham": {"single": (1, 4), "small": (2, 8)},
    "canned_tuna": {"single": (2, 8), "small": (4, 12)},
    "sauce": {"single": (1, 3), "small": (1, 5)},
    "beverage": {"single": (2, 12), "small": (6, 24)},
    "hmr": {"single": (2, 12), "small": (6, 24)},
    "default": {"single": (1, 10), "small": (2, 12)},
}


def _apply_quantity_guard_text(product_hint: str, persona_tag: str, response_text: str) -> str:
    if not response_text:
        return response_text
    m = FIRST_COUNT_PAT.search(response_text)
    if not m:
        return response_text
    try:
        n = int(m.group(1))
    except Exception:
        return response_text
    cat = _product_category_from_text(product_hint)
    hh = _household_bucket_from_tag(persona_tag)
    low, high = TYPICAL_MONTHLY_RANGE.get(cat, TYPICAL_MONTHLY_RANGE["default"]).get(hh, (1, 10))
    if hh == "large":
        high = int(round(high * 1.5))
    new_n, note = n, ""
    if n > high:
        new_n = high
        note = f" (일반 가정 기준, {new_n}개로 잡아 설명 드렸어요)"
    elif n < low:
        new_n = low
        note = f" (최소 사용량을 고려해 {new_n}개로 안내했어요)"
    if new_n == n:
        return response_text
    adjusted = FIRST_COUNT_PAT.sub(lambda _: f"{new_n}개", response_text, count=1)
    lines = adjusted.splitlines()
    if lines:
        lines[0] = lines[0].rstrip() + note
    return "\n".join(lines)


def _build_system_prompt(persona) -> str:
    name = _get_persona_name(persona)
    tag = (getattr(persona, "persona_summary_tag", "") or "").strip()
    sanity = """수량 현실화 규칙:
- 기본 대상은 개인 또는 소가구(1~4인) B2C 소매. 특별히 말하지 않으면 이를 기준으로 답하라.
- 카테고리별 1개월 권장 범위(개인/소가구):
  · 통조림 햄/스팸/리챔: 개인 1~4개, 소가구 2~8개
  · 참치캔: 개인 2~8개, 소가구 4~12개
  · HMR·즉석밥·밀키트/냉동: 개인 2~12개, 소가구 6~24개
  · 우유/요거트/음료: 개인 2~12개, 소가구 6~24개
  · 소스/양념: 개인 1~3개, 소가구 1~5개
- 위 범위를 크게 벗어나면 전제(행사/도매/기업구매/대가족/파티 등)를 밝히고 보수/기준/공격 3단계로 제시."""
    style = """말투 가이드:
- 보고서체 금지. 한국어로 부드럽고 자연스럽게, 문장 짧게. 필요하면 이모지 1개까지.
- 굵게/하이픈/번호 서식 금지, 줄바꿈 또는 '·'만 사용.
- 가격 질문은 심리가격대(스윗스팟) 범위로, 200g/340g 차등 함께 언급.
- 반드시 1인칭(저/제/나는)으로, 전문가/도우미 자기소개 금지.
- '너는 어떤 페르소나야/너는 어떤 소비자야/자기소개' 처럼 물을 때는 2~3문장 소개.
- 가격이나 용량이 주어지면 단위가격(원/100g·ml)로 간단 비교. 없으면 억지 계산 금지.
- 규격이 2가지 이상이면 가성비·보관성 기준으로 '규격 추천' 한 줄을 꼭 넣는다."""
    format_guide = """응답 형식(자연어, 마크다운 서식 금지):
1) 첫 줄: 저는 한 달에 N개(규격 기준)를 구매할 것 같아요!
2) 내 기준(핵심 3~5줄):
   · 취향/식단: 건강·간편/HMR·프리미엄 선호 등 내 취향을 한 줄
   · 가구/생활: 1인·2인, 주간 요리 빈도
   · 예산: 월 식료품 예산(모르면 '평균 예산 가정')과 가공식품 비중 10~20% 가정
   · 가성비/규격: (가능하면) 단위가격 비교 예시 – 150g 2,000원 ≈ 1,333원/100g, 300g 3,200원 ≈ 1,067원/100g
   · 규격 추천: 소용량/대용량 중 무엇을 왜 고르는지 한 줄
3) 제품의 장점:
   · 한 줄씩 2~3개
4) 제품의 단점:
   · 한 줄씩 2~3개
5) 이렇게 되면 더 좋아요:
   · 제품이 ~하면 더 좋아요(2~3개 제안)
6) '사는 이유/안 사는 이유/가정·주의' 같은 표현은 사용하지 않는다."""
    return (
        f"역할: 너는 가상의 소비자 페르소나 '{name}'이다. 항상 1인칭으로 답하고, 내 취향/예산/가구 규모를 기준으로 현실적인 수량을 말한다.\n\n"
        f"[내 설정(요약)]\n{tag}\n\n{sanity}\n\n{style}\n\n{format_guide}"
    )


def _get_persona_name(persona) -> str:
    for field in ("name", "display_name", "nickname", "persona_name"):
        val = getattr(persona, field, None)
        if val:
            return str(val)
    tag = getattr(persona, "persona_summary_tag", "").strip()
    if tag:
        token = tag.split()[0]
        if token and len(token) <= 6:
            return token
    return "마케팅 도우미"


def _maybe_handle_greeting(persona, user_input: str) -> Optional[str]:
    if not user_input:
        return None
    if GREETING_PAT.match(user_input.strip()):
        name = _get_persona_name(persona)
        return f"안녕하세요! 저는 {name}이에요! 식품 판매에 대한 질문을 해주실래요?"
    return None


SELF_INTRO_TRIGGERS = ("너는 누구", "누구야", "어떤 페르소나", "자기소개", "이름이 뭐", "프로필 알려줘", "정체가 뭐", "자기 소개", "어떤 소비자", "소비자야")


def _maybe_handle_persona_intro(persona, user_input: str) -> Optional[str]:
    if not user_input:
        return None
    t = (user_input or "").strip().lower()
    if not any(key in t for key in SELF_INTRO_TRIGGERS):
        return None
    name = _get_persona_name(persona)
    tag = getattr(persona, "persona_summary_tag", "") or ""
    def pick(patterns: List[str], text: str) -> Optional[str]:
        for p in patterns:
            if p in text:
                return p
        return None
    ages = ["10대", "20대", "30대", "40대", "50대", "60대", "60대 이상"]
    genders = ["여자", "남자"]
    households = ["1인 가구", "2인 가구", "3인 가구", "4인 가구", "대가족"]
    regions = [
        "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
        "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
    ]
    age = pick(ages, tag) or ""
    gender = pick(genders, tag) or ""
    household = pick(households, tag) or ""
    region = pick(regions, tag) or ""
    h = ("건강" in tag)
    c = ("편의" in tag) or ("간편" in tag) or ("hmr" in tag) or ("HMR" in tag)
    premium = ("프리미엄" in tag) or ("품질" in tag)
    low_price = ("가격" in tag and ("구애받지 않" in tag or ("민감" in tag and ("낮" in tag or "적" in tag)))) or premium
    parts: List[str] = []
    if h and c:
        parts.append("건강·편의 선호가 높고")
    elif h:
        parts.append("건강을 특히 중시하고")
    elif c:
        parts.append("편의를 특히 중시하고")
    parts.append("가격 민감도는 낮아 품질을 봐요" if low_price else "가격에도 민감한 편이에요")
    trait = " ".join(parts)
    who = f"{region + '에 사는 ' if region else ''}{age}{(' ' + gender) if gender else ''}{(' ' + household) if household else ''}".strip()
    if who:
        who += "의 "
    return f"저는 {who}{name}이고, {trait}."


def _has_purchase_intent(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in INTENT_HINTS) or bool(NUM_PAT.search(t))


def _parse_persona_traits(tag: str) -> Dict[str, float]:
    vals: Dict[str, float] = {}
    src = tag or ""
    def _num_after_colon(start_idx: int) -> Optional[float]:
        cpos = src.find(":", start_idx)
        if cpos == -1:
            return None
        i = cpos + 1
        n = len(src)
        while i < n and src[i].isspace():
            i += 1
        j = i
        allowed = "0123456789."
        while j < n and src[j] in allowed:
            j += 1
        try:
            return float(src[i:j])
        except Exception:
            return None
    for key in ("brand_loyalty", "cooking_convenience", "health_orientation", "hmr_preference", "premium_orientation", "price_sensitivity", "variety_seeking"):
        kpos = src.find(key)
        if kpos != -1:
            v = _num_after_colon(kpos + len(key))
            if v is not None:
                vals[key] = v
    return vals


def _maybe_handle_food_preference(persona, user_input: str) -> Optional[str]:
    t = (user_input or "").strip().lower()
    if _has_purchase_intent(t):
        return None
    tag = getattr(persona, "persona_summary_tag", "") or ""
    tr = _parse_persona_traits(tag)
    health = tr.get("health_orientation", 0.5)
    hmr = tr.get("hmr_preference", 0.5)
    premium = tr.get("premium_orientation", 0.5)
    if any(k in t for k in LIKE_TRIGGERS) or LIKE_RE.search(t):
        picks = []
        if health >= 0.6:
            picks.append("샐러드나 그릴드 같은 담백한 메뉴")
        if hmr >= 0.6:
            picks.append("간단히 데워 먹는 밀키트/즉석 한 끼")
        if premium >= 0.6:
            picks.append("원재료가 잘 보이는 프리미엄 제품")
        if not picks:
            picks.append("집에서 손쉽게 준비할 수 있는 편한 메뉴")
        extra = " 바쁠 땐 HMR도 자주 골라요." if hmr >= 0.6 else ""
        return f"저는 {', '.join(picks)}를 좋아해요.{extra}"
    if any(k in t for k in DISLIKE_TRIGGERS) or DISLIKE_RE.search(t):
        base = "너무 달거나 기름진 음식, 짠맛이 강한 가공육" if health >= 0.6 else "특별히 가리는 건 많지 않아요"
        return f"저는 {base}는 잘 안 먹어요."
    sentiment = any(k in t for k in ("좋아", "좋아해", "싫어", "싫어해", "어때"))
    if sentiment and "참치" in t:
        note = "저염/물담금이나 올리브오일 타입으로 골라요" if health >= 0.6 else "가성비 좋은 제품이면 괜찮아요"
        qual = "좋아해요" if health >= 0.4 else "가끔 먹어요"
        return f"저는 캔 참치 {qual}. {note}."
    if sentiment and any(k in t for k in ("햄", "리챔", "스팸", "런천미트", "캔햄")):
        return "가끔은 먹지만 저염/저지방 위주로 골라요. 일상적으로는 많이 찾진 않아요." if health >= 0.6 else "가끔 간단한 요리에 쓰는 편이에요."
    if sentiment and any(k in t for k in ("커피", "라떼")):
        return "커피는 좋아해요. 다만 너무 달지 않은 걸로 마셔요." if health >= 0.6 else "커피 좋아해요! 달달한 라떼도 가끔 즐겨요."
    if sentiment and any(k in t for k in ("초코", "초콜릿")):
        return "초콜릿은 좋아하지만, 보통은 다크로 조금만 먹어요." if health >= 0.6 else "초콜릿 좋아해요. 기분전환용으로 자주 먹는 편이에요."
    return None


def _get_llm_response_impl(
    persona_id: int,
    user_input: str,
    model_name: str = "gpt-5-mini",
    thread_id: Optional[int] = None,
    max_history: int = 16,
    assume_view_pre_saved_user: bool = True,
) -> str:
    client, APIError = _get_openai_client()
    try:
        pid = int(persona_id)
    except Exception:
        return "페르소나 정보를 찾을 수 없습니다."
    persona = persona_service.get_persona_by_id(pid)
    if not persona:
        return "페르소나 정보를 찾을 수 없습니다."
    greet = _maybe_handle_greeting(persona, user_input)
    if greet:
        return greet
    intro = _maybe_handle_persona_intro(persona, user_input)
    if intro:
        return intro
    in_scope = _is_in_scope_food(user_input, thread_id, client, model_name)
    if not in_scope:
        pref = _maybe_handle_food_preference(persona, user_input)
        return pref if pref else REFUSAL_TEXT
    snapshot = _extract_context_snapshot(client, model_name, thread_id, user_input)
    guard = _apply_price_guard(persona, snapshot, user_input)
    if guard:
        return guard
    system_prompt = _build_system_prompt(persona)
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if snapshot:
        messages.append({"role": "system", "content": f"[컨텍스트 스냅샷]\n{snapshot}"})
    history = _load_history_messages(thread_id, limit=max_history)
    messages.extend(history)
    if not assume_view_pre_saved_user or not history or history[-1]["role"] != "user" or history[-1]["content"] != user_input:
        messages.append({"role": "user", "content": user_input})
    try:
        resp = client.chat.completions.create(
            model=model_name, messages=messages, temperature=0.25, max_tokens=900,
        )
        text = (resp.choices[0].message.content or "").strip()
    except APIError:
        return "잠시 응답이 지연되고 있어요. 제품명과 기간/가격/프로모션 조건을 한 줄로 알려주시면 바로 추정해드릴게요."
    except Exception as e:
        raise Exception(f"LLM 응답을 가져오는 중 에러가 발생했습니다: {e}") from e
    persona_tag = getattr(persona, "persona_summary_tag", "") or ""
    product_hint = snapshot or user_input
    text = _apply_quantity_guard_text(product_hint, persona_tag, text)
    return text


def _to_int_or_none(x) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None


def _extract_thread_id_from_request(request) -> Optional[int]:
    try:
        rid = request.resolver_match.kwargs.get("thread_id")
        rid = _to_int_or_none(rid)
        if rid is not None:
            return rid
    except Exception:
        pass
    for source in (getattr(request, "POST", {}), getattr(request, "GET", {})):
        try:
            rid = _to_int_or_none(source.get("thread_id"))
            if rid is not None:
                return rid
        except Exception:
            pass
    try:
        m = re.search(r"/chat/\d+/(\d+)/", request.path)
        if m:
            return _to_int_or_none(m.group(1))
    except Exception:
        pass
    return None


def get_llm_response(*args, **kwargs):
    if args and hasattr(args[0], "META"):
        request = args[0]
        persona_id = args[1] if len(args) > 1 else kwargs.get("persona_id")
        user_input = args[2] if len(args) > 2 else kwargs.get("user_input", "")
        model_name = args[3] if len(args) > 3 else kwargs.get("model_name", "gpt-5-mini")
        thread_id = kwargs.get("thread_id") or _extract_thread_id_from_request(request)
        return _get_llm_response_impl(persona_id, user_input, model_name, thread_id)
    return _get_llm_response_impl(*args, **kwargs)
