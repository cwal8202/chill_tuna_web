from django.contrib import admin
from .models import ChatThread, ChatMessage

class ChatThreadAdmin(admin.ModelAdmin):
    # api테스트중 - 박동현
    list_display = ('id', 'persona_id', 'last_updated')

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'sender', 'message', 'timestamp')

admin.site.register(ChatThread, ChatThreadAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)