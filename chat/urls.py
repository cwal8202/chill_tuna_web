from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("<int:persona_id>/<int:thread_id>/", views.ChatView.as_view(), name="chat_view"),
    path("all/", views.AllChatsView.as_view(), name="all_chats"), # New URL pattern
]