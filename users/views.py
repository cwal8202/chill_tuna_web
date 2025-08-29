from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic

# class SignUpView(generic.CreateView):
#     form_class = UserCreationForm
#     success_url = reverse_lazy('users:login')
#     template_name = 'users/signup.html'

from .forms import CustomUserCreationForm 

class SignUpView(generic.CreateView):
    # form_class를 우리가 만든 CustomUserCreationForm으로 변경합니다.
    form_class = CustomUserCreationForm 
    success_url = reverse_lazy('users:login')
    template_name = 'users/signup.html'