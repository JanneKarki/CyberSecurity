from django import forms
from .models import Question, Choice

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['question_text']

ChoiceFormset = forms.inlineformset_factory(
    Question, Choice, fields=('choice_text',), extra=1, max_num=10, validate_max=True
)

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['choice_text']

    choice_text = forms.CharField(required=False)

