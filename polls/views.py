from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Choice, Question, Vote
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import QuestionForm
from .forms import ChoiceForm, ChoiceFormset
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.forms import formset_factory

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

    def get(self, request, *args, **kwargs):
        # Call the base implementation to get the question
        response = super().get(request, *args, **kwargs)

        question = self.get_object()

        user_vote = Vote.objects.filter(user=request.user, question=question).first()
        if user_vote:
            # Redirect to results page if the user has already voted
            return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))

        return response
    #def get_queryset(self):
     #   return Question.objects.filter(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'


@login_required
def poll_detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    
    # Check if the user has already voted for this question
    user_vote = Vote.objects.filter(user=request.user, question=question).first()
    if user_vote:
        # Redirect to results page if the user has already voted
        return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
    else:
        # Display the form to vote
        return render(request, 'polls/detail.html', {'question': question})

@login_required
def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(request, 'polls/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        # Check if the user has already voted for this question
        user_vote = Vote.objects.filter(user=request.user, question=question).first()
        if user_vote:
            # Redirect to results page if the user has already voted
            return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))
        else:
            # Record the vote
            selected_choice.votes += 1
            selected_choice.save()
            
            # Create a new Vote instance to record the user's vote
            Vote.objects.create(user=request.user, question=question, choice=selected_choice)
            
            return HttpResponseRedirect(reverse('polls:results', args=(question.id,)))


@login_required
def add_question(request):

    ChoiceFormSet = formset_factory(ChoiceForm, extra=5)

    if request.method == "POST":
        form = QuestionForm(request.POST)
        formset = ChoiceFormSet(request.POST, prefix='choices')
        if form.is_valid() and formset.is_valid():
            question = form.save(commit=False)
            question.pub_date = timezone.now()
            question.user = request.user
            question.save()

            # Save only filled out choices.
            for choice_form in formset:
                choice_text = choice_form.cleaned_data.get('choice_text')
                if choice_text:  # Only if choice_text is filled
                    choice = choice_form.save(commit=False)
                    choice.question = question
                    choice.user = request.user  # Assign the user to the choice here.
                    choice.save()


            return HttpResponseRedirect(reverse('polls:index'))
    else:
        form = QuestionForm()
        formset = ChoiceFormSet(prefix='choices')

    return render(request, 'polls/add_question.html', {'form': form, 'formset': formset})



@login_required
def edit_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id, user=request.user)
    
    existing_choices_count = question.choice_set.count()
    extra_forms = max(0, 5 - existing_choices_count)  # Adjust 5 to your desired max

    ChoiceFormSet = formset_factory(ChoiceForm, extra=extra_forms, can_delete=False)  # can_delete set to False

    if request.method == "POST":
        
        form = QuestionForm(request.POST, instance=question)
        formset = ChoiceFormSet(request.POST, prefix='choices')
           
        if form.is_valid() and formset.is_valid():
            # Remove all existing choices related to the question
            question.choice_set.all().delete()

            # Save the updated question
            form.save()
            
            # Handle new choices
            for choice_form in formset:
                if choice_form.cleaned_data and choice_form.cleaned_data.get('choice_text').strip():  # check for non-empty choice_text
                    new_choice = choice_form.save(commit=False)
                    new_choice.question = question
                    new_choice.user = request.user
                    new_choice.save()
            
            return HttpResponseRedirect(reverse('polls:index'))

    else:
        form = QuestionForm(instance=question)

        # For the GET request, bind choices manually
        choices_data = [{'choice_text': choice.choice_text} for choice in question.choice_set.all()]
        formset = ChoiceFormSet(prefix='choices', initial=choices_data)

    return render(request, 'polls/edit_question.html', {'form': form, 'formset': formset, 'question_id': question.id})




@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, pk=question_id, user=request.user)
    if request.method == "POST":
        question.delete()
        return HttpResponseRedirect(reverse('polls:index'))
    return render(request, 'polls/confirm_delete.html', {'question': question})




def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in.
            login(request, user)
            return redirect('polls:index')
    else:
        form = UserCreationForm()
    return render(request, 'polls/register.html', {'form': form})