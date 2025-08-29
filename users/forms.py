from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User # Django의 기본 사용자 모델

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label="이메일", 
        help_text="비밀번호 찾기 등에 사용되니 정확하게 입력해주세요."
    )
    first_name = forms.CharField(label="이름", max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        # UserCreationForm의 Meta 클래스를 상속받아 사용합니다.
        model = User
        
        # 기본 필드('username')에 새로운 필드('email', 'first_name')를 추가합니다.
        # 순서도 여기서 정할 수 있습니다.
        fields = UserCreationForm.Meta.fields + ('email', 'first_name')

        # 각 필드의 라벨(화면에 보여지는 이름)을 변경할 수도 있습니다.
        labels = {
            'username': '사용자 아이디',
        }