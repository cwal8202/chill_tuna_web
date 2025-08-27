from django.db import models
from persona.models import Persona  # 페르소나 완성 되면 그때 사용

class ChatThread(models.Model):
    # id = models.IntegerField(auto_created=True, primary_key=True)

    # 채팅 스레드의 고유 ID - 스레드가 어떤 페르소나와 대화한 것인지 연결
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE, default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ChatThread with {self.persona}"
    


class ChatMessage(models.Model):
    
    # 이 메시지가 속한 채팅 스레드
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    
    # 메시지를 보낸 사람 ('user' 또는 'persona')
    sender = models.CharField(max_length=10)
    
    # 메시지 내용
    message = models.TextField()
    
    # 메시지가 생성된 시간
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Message from {self.sender} in thread {self.thread.id}"


class ReferenceProduct(models.Model):
    # RAG 검색에 사용될 제품 정보를 담는 모델
    product_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    
    # 제품 속성을 JSON 형식으로 저장 (예: {"재료": "참치", "특징": "저염"})
    attributes = models.JSONField(null=True, blank=True)
    
    # 월별 판매량을 JSON 배열로 저장
    monthly_sales = models.JSONField(null=True, blank=True)
    
    # 세그먼트별 점유율을 JSON 객체로 저장
    segment_share = models.JSONField(null=True, blank=True)
    
    # 계절적 트렌드에 대한 설명 
    seasonal_trend = models.TextField(blank=True)
    
    # 프로모션 효과 (0.0 ~ 1.0) 
    promotion_effect = models.FloatField(null=True, blank=True)
    
    # RAG에 사용할 요약 문장
    summary = models.TextField()
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "참조 제품"