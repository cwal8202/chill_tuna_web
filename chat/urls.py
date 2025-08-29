from django.urls import path
from . import views

app_name = "chat"
urlpatterns = [
    path("<int:persona_id>/<int:thread_id>/", views.ChatView.as_view(), name="chat_view"),
    path("all/", views.AllChatsView.as_view(), name="all_chats"),
    path("search/", views.ChatSearchView.as_view(), name="chat_search"), # New URL pattern for search
    path("thread/<int:thread_id>/delete/", views.DeleteChatThreadView.as_view(), name="delete_chat_thread"),
]