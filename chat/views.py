from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ChatThread, ChatMessage, Persona
from django.http import HttpResponse, JsonResponse
import json
import api.services.chat_service as chat_service
import api.services.llm_service as llm_service
from django.forms.models import model_to_dict
from django.views import View
from datetime import datetime # Added this line
from django.db.models import Max # Import Max for ordering


# Create your views here.

#-------- Chat 전체 흐름 ---------#
# 1. 채팅 목록, 페르소나 확인 
#   1) thread_id 로 chatthread 조회. 없으면 에러
#   2) persona_id 로 persona 조회 후 정보 전달
# 2. 채팅 유/무 확인
#   1). 채팅 있으면 채팅 불러오기
# 3. 사용자가 채팅을 치면 값 llm에 전달.
# 4. llm에서 output으로 나온 값을 화면에 전달.
# 5. 만약 화면 꺼지거나, session 종료되거나, 사용자가 끄면 chatthread에 저장

class ChatView(LoginRequiredMixin, View):
    login_url = '/users/login/'
    # 함수명 : get
    # input : request, persona_id, thread_id
    # output : chat_persona.html 화면 + context
    # 작성자 : 최장호
    # 작성 날짜 : 2025-08-07
    # 함수 설명 : GET 요청을 처리하여 채팅 페이지를 처음 렌더링합니다.
    #               1. 페르소나 id, thread_id로 페르소나, 채팅 내용 가져오기
    #               2. 화면전달 : persona, chat_message, thread_id
    def get(self, request, persona_id, thread_id):
        print(persona_id, thread_id, "###########################")
        # 1. 페르소나 id, thread_id로 chat_thread, 채팅 내용 가져오기
        chat_thread, chat_messages, error_message = chat_service.get_chat_start_data(request, persona_id, thread_id)
        persona = chat_thread.persona
        thread_id = chat_thread.id
        if error_message:
            messages.error(request, error_message)
            print(f"{thread_id}번 채팅 스레드를 찾을 수 없습니다.") # 삭제해야함
            # return redirect("home")
        
        # 3. 화면에 정보전달 : persona, chat_message
        persona_dict = model_to_dict(persona)
        persona_json = json.dumps(persona_dict, ensure_ascii=False)
        print(persona_json, "@@@@@@@")
        context = {
            "persona": persona,
            "persona_json": persona_json,
            "chat_messages": chat_messages,
            "thread_id": thread_id,
        }
        return render(request, "chat/chat_persona.html", context)

    # 함수명      : post
    # input       : 사용자 입력 request(message, model, persona_id, thread_id)
    # output      : LLM 답변 전달 (JSON)
    # 작성자      : 최장호
    # 작성일자    : 2025-08-08
    # 함수설명    : POST 요청을 처리하여 사용자의 메시지를 받고 LLM 응답을 반환합니다.
    #               1. request 받은 사용자 질문을 LLM에 전달.
    #               2. LLM 답변 오면 chatthread db, chatmessage db 에 저장.
    #               3. 화면에 LLM 답변 전달.
    def post(self, request, *args, **kwargs):
        # 1) request 받은 사용자 질문을 LLM에 전달.
        payload = json.loads(request.body.decode('utf-8'))
        user_input = payload.get("message") # 사용자가 입력한 내용
        selected_model = payload.get("model")  # base.html에서 온 값
        persona_id = payload.get("persona_id")
        thread_id = payload.get("thread_id")

        # 2) LLM 답변이 온 뒤에 db에 저장. chatthread db, chatmessage db
        llm_output = llm_service.get_llm_response(request, persona_id, user_input, selected_model)
        chat_thread = None
        if llm_output:
            chat_thread = chat_service.save_chat_messsage(request, user_input, persona_id, thread_id, llm_output)
        ## 2-1) llm 답변으로 chat_thread, chat_message 저장
        # 3) 화면에 LLM 답변 전달.

        # 3) 화면에 LLM 답변과 새로 생성/업데이트된 thread_id를 전달
        if chat_thread:
            if thread_id:
                is_new_thread = False
            else:
                is_new_thread = True
            response_data = {
                "persona_msg": llm_output,
                "thread_id": chat_thread.id,
                "is_new_thread": is_new_thread
            }
            return JsonResponse(response_data)
        else:
            # 저장 중 에러가 발생한 경우
            return JsonResponse({"error": "메시지 저장에 실패했습니다."}, status=500)



class AllChatsView(LoginRequiredMixin, View):
    login_url = '/users/login/'

    def get(self, request):
        all_chats = ChatThread.objects.filter(user=request.user).order_by('-created_at')
        context = {
            'all_chats': all_chats
        }
        return render(request, 'chat/all_chats.html', context)


class ChatSearchView(LoginRequiredMixin, View):
    login_url = '/users/login/'

    def get(self, request):
        query = request.GET.get('q', '')
        results_data = []

        if query:
            # Get all chat messages for the current user that match the query
            matching_messages = ChatMessage.objects.filter(
                thread__user=request.user,
                message__icontains=query
            ).order_by('timestamp') # Order by timestamp to get messages in chronological order within a thread

            # Group messages by thread
            threads_with_matches = {}
            for msg in matching_messages:
                thread_id = msg.thread.id
                if thread_id not in threads_with_matches:
                    threads_with_matches[thread_id] = {
                        'thread_id': thread_id,
                        'persona_id': msg.thread.persona.id,
                        'persona_name': msg.thread.persona.name,
                        'persona_summary_tag': msg.thread.persona.persona_summary_tag,
                        'last_message_date': (msg.thread.messages.aggregate(Max('timestamp'))['timestamp__max'] or datetime.now()).strftime("%Y년 %m월 %d일 %H:%M"), # Get last message date of the thread
                        'messages': []
                    }
                threads_with_matches[thread_id]['messages'].append({
                    'sender': msg.sender,
                    'message': msg.message,
                    'timestamp': msg.timestamp.strftime("%Y년 %m월 %d일 %H:%M")
                })
            
            # Convert dictionary to list and sort by last message date of the thread
            # (This sorting is already done by the aggregate Max('timestamp') and then by the loop order)
            # For consistent ordering, we might want to sort the threads_with_matches by last_message_date
            # However, the current structure groups by thread_id, so let's just convert to list
            # and ensure messages within each thread are chronological (which they are due to initial filter)
            
            # Sort threads by their last message date (descending)
            sorted_threads = sorted(threads_with_matches.values(), key=lambda x: x['last_message_date'], reverse=True)

            results_data = sorted_threads

        return JsonResponse({'results': results_data})