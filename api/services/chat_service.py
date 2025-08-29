from chat.models import ChatThread, ChatMessage
from . import persona_service
from django.db import transaction
from datetime import datetime

# 함수명 : get_chat_start_data
# input : request, persona_id, thread_id
# output : 성공 시 (persona, chat_messages, None)을 반환.
#          실패 시 (None, None, error_message)를 반환.
# 작성자 : 최장호
# 작성 날짜 : 2025-08-10
# 함수 설명 : 채팅 시작 시 필요한 데이터 가져오기
#               1. thread_id로 thread확인. 채팅 내용 조회
#               2. persona_id로 persona 조회
#               3. 신규 채팅시 chat_thread 반환
def get_chat_start_data(request, persona_id, thread_id):
    # 1. persona_id 로 persona 조회
    try:
        persona = persona_service.get_persona_by_id(persona_id)
    except Exception as e:
        return None, None, f"페르소나 정보를 찾을 수 없습니다."

    # 2. thread_id 유/무 확인 후 있으면 chatthread 조회, 채팅 내용 조회
    if thread_id and thread_id > 0:
        try:
            chatthread = ChatThread.objects.get(id=thread_id)
        except ChatThread.DoesNotExist:
            return None, None, f"{thread_id}번 채팅 스레드를 찾을 수 없습니다."
        
        if chatthread.persona_id != persona_id:
            return None, None, "thread_id와 persona_id가 일치하지 않습니다."
        
        chat_messages = ChatMessage.objects.filter(thread=chatthread).order_by("timestamp")
        return chatthread, chat_messages, None
    
    # 3. 신규 채팅 (thread_id가 0 또는 None)일 경우 새 ChatThread 생성
    else:
        user = request.user if request.user.is_authenticated else None
        
        # 이전에 페르소나로 채팅한 기록이 있으면 해당 채팅 스레드를 반환
        existing_chat_thread = ChatThread.objects.filter(persona=persona, user=user).first()
        
        if existing_chat_thread:
            chat_thread = existing_chat_thread
            chat_messages = ChatMessage.objects.filter(thread=chat_thread).order_by("timestamp")
            return chat_thread, chat_messages, None
        else:
            # 페르소나 기록도 없고 채팅쓰레드가 없으면 새 스레드 생성
            chat_thread = ChatThread.objects.create(persona=persona, user=user)
            return chat_thread, [], None # 새 스레드이므로 메시지는 비어있음


# 함수명 : save_chat_conversation
# input : request, user_input, persona_id, thread_id
# output : chat_thread 객체, 없으면 None 반환
# 작성자 : 최장호
# 작성 날짜 : 2025-08-10
# 함수 설명 : chatthread, chatmessage 저장 로직.
#               1. thread 생성 or  업데이트 및 저장
#               2. chatmessage 생성 및 저장
#               3. 결과 반환
@transaction.atomic # 하나의 트랜잭션
def save_chat_messsage(request, user_input, persona_id, thread_id, llm_output):
    if thread_id:
       try:
           chat_thread = ChatThread.objects.get(id=thread_id)
           chat_thread.save()
       except ChatThread.DoesNotExist:
           return None, "존재하지 않는 대화입니다."
    
    else:
       persona = persona_service.get_persona_by_id(persona_id)
       if persona is None:
           return None, "페르소나를 찾을 수 없습니다."
       user = request.user if request.user.is_authenticated else None
       chat_thread = ChatThread.objects.create(persona=persona, user=user)
    # fk인 thread_id 에 chat_thread 객체 할당
    ChatMessage.objects.create(thread=chat_thread, sender='user', message=user_input)
    ChatMessage.objects.create(thread=chat_thread, sender='persona', message=llm_output)
    
    return chat_thread, None
