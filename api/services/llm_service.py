from openai import OpenAI, APIError
import os
from . import persona_service
from dotenv import load_dotenv

# 함수명 : get_llm_response
# input : persona_id, user_input, model_name
# output : LLM API 응답 문자열
# 작성자 : 최장호
# 작성 날짜 : 2025-08-10 (수정: 2025-08-27)
# 함수 설명 : 페르소나, 사용자 입력을 LLM API에 전달하고 응답을 반환합니다.
#               1. persona_id로 persona 정보 가져오기
#               2. 사용자 입력과 persona 정보를 프롬프트로 구성
#               3. LLM API에 전달하여 응답 받아오기
#               4. 응답 텍스트 반환
def get_llm_response(persona_id, user_input, model_name="gpt-4o-mini"):
    """
    사용자 입력과 페르소나 정보를 받아 LLM API에 전달하고 응답을 반환합니다.
    API 통신 실패 시 예외(Exception)를 발생시킬 수 있습니다.
    """
    try:
        # 1. API 키 설정 및 클라이언트 초기화 (최신 버전 방식)
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        client = OpenAI(api_key=api_key)

        # 2. persona_id로 persona 정보 가져오기
        persona = persona_service.get_persona_by_id(persona_id)
        if not persona:
            return "페르소나 정보를 찾을 수 없습니다."

        # 3. LLM에 전달할 프롬프트 구성
        system_prompt = f"""
        당신은 고객 분석을 위한 롤플레잉 시뮬레이터입니다.
        다음은 당신이 연기해야 할 페르소나의 정보입니다. 이 정보에 기반하여 사용자의 질문에 답해주세요.
        ---
        {persona.persona_summary_tag}
        ---
        """

        # 4. LLM API에 요청 전달 및 응답 받기 (최신 버전 방식)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        
        llm_output = response.choices[0].message.content.strip()
        return llm_output

    except APIError as e:
        # OpenAI API 관련 에러 처리 (최신 버전 방식)
        print(f"OpenAI API 에러 발생: {e}")
        raise Exception(f"LLM API 호출에 실패했습니다: {e}") from e
    except Exception as e:
        # 기타 예외 처리
        print(f"알 수 없는 에러 발생: {e}")
        raise Exception(f"LLM 응답을 가져오는 중 에러가 발생했습니다: {e}") from e
