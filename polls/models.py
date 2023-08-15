import datetime
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.views import generic

class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published', auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    users_voted = models.ManyToManyField(User, related_name='votes', blank=True)

    def __str__(self):
        return self.question_text
    
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now
    was_published_recently.admin_order_field = 'pub_date'
    was_published_recently.boolean = True
    was_published_recently.short_description = 'Published recently?'



class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    

    def __str__(self):
        return self.choice_text


class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)


#QuestionUpdateView, -DeleteView
class QuestionUpdateView(generic.UpdateView):
    model = Question
    fields = ['whatever_fields_you_want_to_edit']
    template_name = 'polls/edit_question.html'

    def get_queryset(self):
        """Only allow the creator to edit the question."""
        qs = super().get_queryset()
        return qs.filter(created_by=self.request.user)

class QuestionDeleteView(generic.DeleteView):
    model = Question
    success_url = '/polls/'
    template_name = 'polls/delete_question.html'

    def get_queryset(self):
        """Only allow the creator to delete the question."""
        qs = super().get_queryset()
        return qs.filter(created_by=self.request.user)
