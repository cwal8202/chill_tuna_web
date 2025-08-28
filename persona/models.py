from django.db import models

# Create your models here.

class Persona(models.Model):
    # id = models.IntegerField(auto_created=True, primary_key=True)
    name = models.CharField(max_length=20)
    segment = models.CharField(max_length=50, help_text="예: 웰빙추구형 VIP")    
    gender = models.CharField(max_length=10, help_text="예: 여")
    age = models.CharField(max_length=10, help_text="예: 40대")
    household = models.CharField(max_length=50, help_text="예: 부부")
    marriage = models.CharField(max_length=20, null=True, blank=True)
    income_status = models.CharField(max_length=20, null=True, blank=True)
    income_month = models.CharField(max_length=20, null=True, blank=True)
    # customer_value = models.CharField(max_length=50, help_text="예: VIP")
    # purchase_pattern = models.JSONField(max_length=100, help_text="예: 유제품, 통조림/즉석/면류")
    # lifestyle = models.JSONField(max_length=100, help_text="예: 웰빙추구형, 트렌드추종형")
    job = models.CharField(max_length=50, help_text="예: 은퇴자")
    education = models.CharField(max_length=30, null=True, blank=True)
    region = models.CharField(max_length=30, null=True, blank=True)
    purchase_pattern = models.TextField(max_length=500, null=True, blank=True)
    segment_decription = models.TextField(max_length=500, null=True, blank=True)
    persona_summary_tag = models.TextField(max_length=500, 
                                        # help_text="예: 윤하진, 여자, 50대, 1인 가구, 미혼(사별/이혼 포함), 맞벌이 하지 않음, " \
                                        # "월소득 100-200만원 미만, 트렌드 주도형 소비자, 자신의 취향과 경험을 중시하는 소비자 그룹입니다. " \
                                        # "단순히 배를 채우는 것 이상의 가치를 추구하며, 새로운 제품을 가장 먼저 경험하고 공유하려는 경향이 강합니다, " \
                                        # "소비성향은 다음과 같습니다. brand_loyalty : 0.54, cooking_convenience : 0.598, " \
                                        # "health_orientation : 0.371, hmr_preference : 0.804, premium_orientation : 0.469, " \
                                        # "price_sensitivity : 0.316, variety_seeking : 0.409, " \
                                        # "단순노무 종사자, 고졸(대학 재학 포함), 부산광역시 거주"
                                        )

    def __str__(self):
        return f"{self.segment} - 페르소나 {self.id} {self.name}"

    class Meta:
        verbose_name_plural = "페르소나" # Django 관리자 페이지에서 보여지는 이름