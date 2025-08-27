from django.urls import path
from . import views

app_name = 'persona'

urlpatterns = [
    path('create/', views.create_persona, name='create_persona'),
    path('build/', views.build_persona, name='build_persona'),
    path('chat/<int:persona_id>/', views.chat_persona_view, name='chat_persona'),
    path('find_and_chat/', views.find_and_chat_view, name='find_and_chat'),
]