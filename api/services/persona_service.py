from persona.models import Persona

# 함수명 : get_persona_by_id
# input : persona_id
# output : persona 객체 반환.
# 작성자 : 최장호
# 작성 날짜 : 2025-08-10
# 함수 설명 : chatthread, chatmessage 조회 후 정보 반환.
#               1. thread_id로 thread확인. 채팅 내용 조회
def get_persona_by_id(persona_id):
    try:
        persona = Persona.objects.get(id=persona_id)
        return persona
    except Persona.DoesNotExist:
        return None