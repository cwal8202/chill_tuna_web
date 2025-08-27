from django.db import models

# Create your models here.

class Persona(models.Model):
    # id = models.IntegerField(auto_created=True, primary_key=True)
    name = models.CharField(max_length=20)
    segment = models.CharField(max_length=50, help_text="예: 웰빙추구형 VIP")
    age_group = models.CharField(max_length=10, help_text="예: 40대")
    family_structure = models.CharField(max_length=50, help_text="예: 부부")
    gender = models.CharField(max_length=10, help_text="예: 여")
    customer_value = models.CharField(max_length=50, help_text="예: VIP")
    purchase_pattern = models.JSONField(max_length=100, help_text="예: 유제품, 통조림/즉석/면류")
    lifestyle = models.JSONField(max_length=100, help_text="예: 웰빙추구형, 트렌드추종형")
    job = models.CharField(max_length=50, help_text="예: 은퇴자")
    persona_summary_tag = models.TextField(max_length=500, help_text="예: 40대 여, 은퇴자, 부부, 우수고객, 유제품, 통조림/즉석/면류, 웰빙추구형, 트렌드추종형")

    def __str__(self):
        return f"{self.segment} - 페르소나 {self.id} {self.name}"

    class Meta:
        verbose_name_plural = "페르소나" # Django 관리자 페이지에서 보여지는 이름