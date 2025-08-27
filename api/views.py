from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from decouple import config
from openai import OpenAI
import json

from chat.models import ChatMessage, ChatThread

@csrf_exempt # 외부 API 호출을 허용하기 위해 CSRF 검증을 비활성화
def chat_message_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 지원합니다'}, status=405)
    try:
        data = json.loads(request.body)
        thread_id = data.get('thread_id')
        user_message = data.get('message')
        
        if not thread_id or not user_message:
            return JsonResponse({'error': 'thread_id와 message는 필수 항목입니다'}, status=400)
        
        # 채팅 스레드와 페르소나 가져오기
        thread = get_object_or_404(ChatThread, id=thread_id)
        persona = thread.persona
        
        # 사용자 메시지 DB에 저장하기
        ChatMessage.objects.create(
            thread=thread,
            sender='user',
            message=user_message
        )
        
        # RAG 검색
        # rag_context = get_rag_context(user_message, persona)
        rag_context = "이 제품은 고단백 저염식 참치로, 건강을 중시하는 소비자에게 인기가 많아"  # 실제 RAG 검색 로직을 구현해야 함
        
        # OpenAI API 호출
        client = OpenAI(api_key=config('OPENAI_API_KEY'))
        
        system_prompt = f" 페르소나입니다. 다음 페르소나당신은 {persona.name}입니다. 정보와 참고 데이터를 바탕으로 사용자의 질문에 답변해주세요: {persona.persona_summary_tag}. 참고 데이터: {rag_context}"
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        persona_response = completion.choices[0].message.content

        # 페르소나 답변을 DB에 저장
        ChatMessage.objects.create(thread=thread, sender='persona', message=persona_response)
        
        # 생성된 답변을 채팅창에 JSON 형태로 반환
        return JsonResponse({'response': persona_response})
        
    # 예외 처리
    except json.JSONDecodeError:
        return JsonResponse({'error': '잘못된 JSON 형식입니다.'}, status=400)
    except ChatThread.DoesNotExist:
        return JsonResponse({'error': '존재하지 않는 채팅입니다.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'서버 내부 오류: {str(e)}'}, status=500)
