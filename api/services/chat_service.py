from chat.models import ChatThread, ChatMessage
from . import persona_service
from django.db import transaction
from datetime import datetime

# 함수명 : get_chat_start_data
# input : persona_id, thread_id
# output : 성공 시 (persona, chat_messages, None)을 반환.
#          실패 시 (None, None, error_message)를 반환.
# 작성자 : 최장호
# 작성 날짜 : 2025-08-10
# 함수 설명 : 채팅 시작 시 필요한 데이터 가져오기
#               1. thread_id로 thread확인. 채팅 내용 조회
#               2. persona_id로 persona 조회
#               3. 신규 채팅시 persona만 반환
def get_chat_start_data(persona_id, thread_id):
    # 1. thread_id 유/무 확인 후 있으면 chatthread 조회, 채팅 내용 조회
    if thread_id and thread_id > 0:
        try:
            chatthread = ChatThread.objects.get(id=thread_id)
        except ChatThread.DoesNotExist:
            return None, None, f"{thread_id}번 채팅 스레드를 찾을 수 없습니다."
        
        if chatthread.persona_id != persona_id:
            return None, None, "thread_id와 persona_id가 일치하지 않습니다."
        
        # chatmessage 모델 확인 결과 thread 객체 자체를 넣음.
        chat_messages = ChatMessage.objects.filter(thread=chatthread).order_by("timestamp")
        persona = persona_service.get_persona_by_id(persona_id)
        return persona, chat_messages, None
    
    # 2. persona_id 로 persona 조회
    try:
        persona = persona_service.get_persona_by_id(persona_id)
    except Exception as e:
        return None, None, f"페르소나 정보를 찾을 수 없습니다."
    
    # 3. 신규 채팅시 persona만 반환
    return persona, None, None


# 함수명 : save_chat_conversation
# input : user_input, persona_id, thread_id
# output : chat_thread 객체, 없으면 None 반환
# 작성자 : 최장호
# 작성 날짜 : 2025-08-10
# 함수 설명 : chatthread, chatmessage 저장 로직.
#               1. thread 생성 or  업데이트 및 저장
#               2. chatmessage 생성 및 저장
#               3. 결과 반환
@transaction.atomic # 하나의 트랜잭션
def save_chat_messsage(user_input, persona_id, thread_id, llm_output):
    if thread_id:
       try:
           chat_thread = ChatThread.objects.get(id=thread_id)
           chat_thread.save()
       except ChatThread.DoesNotExist:
           return None
    
    else:
       persona = persona_service.get_persona_by_id(persona_id)
       if persona is None:
           return None
       # fk인 persona_id 에 persona객체 할당
       chat_thread = ChatThread.objects.create(persona=persona)
    # fk인 thread_id 에 chat_thread 객체 할당
    ChatMessage.objects.create(thread=chat_thread, sender='user', message=user_input)
    ChatMessage.objects.create(thread=chat_thread, sender='persona', message=llm_output)
    
    return chat_thread
