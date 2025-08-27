from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('chat/send/', views.chat_message_api, name='chat_message_api'),
    # path('personas/filter/', views.persona_filter_api, name='persona_filter_api'),
]