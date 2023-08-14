from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Choice, Question
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import QuestionForm

@method_decorator(login_required, name='dispatch')
class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]


@method_decorator(login_required, name='dispatch')
class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'

    def get_queryset(self):
        return Question.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'

@login_required
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))

@login_required
def add_question(request):
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.pub_date = timezone.now()
            question.user = request.user
            question.save()
            return HttpResponseRedirect(reverse('polls:index'))
    else:
        form = QuestionForm()

    return render(request, 'polls/add_question.html', {'form': form})


@login_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id, user=request.user)
    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('polls:index'))
    else:
        form = QuestionForm(instance=question)

    return render(request, 'polls/edit_question.html', {'form': form})


@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id, user=request.user)
    question.delete()
    return HttpResponseRedirect(reverse('polls:index'))