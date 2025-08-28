from chat.models import ChatThread

def recent_chats_processor(request):
    recent_chats = []
    if request.user.is_authenticated:
        recent_chats = ChatThread.objects.filter(user=request.user).order_by('-created_at')[:5]
    return {'recent_chats': recent_chats}