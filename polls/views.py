from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Choice, Question, Vote, LoginAttempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .forms import QuestionForm
from .forms import ChoiceForm, ChoiceFormset
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.forms import formset_factory
from django.db import connection
from django.contrib.auth.views import LoginView
from datetime import timedelta



@method_decorator(login_required, name='dispatch')
class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        #Return the last five published questions
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

        choices_data = [{'choice_text': choice.choice_text} for choice in question.choice_set.all()]
        formset = ChoiceFormSet(prefix='choices', initial=choices_data)

    return render(request, 'polls/edit_question.html', {'form': form, 'formset': formset, 'question_id': question.id})


#flaw broken authentication
#fix_a
#@login_required
def delete_question(request, question_id):

    question = get_object_or_404(Question, pk=question_id) #flaw_b
    #fix_b
    #question = get_object_or_404(Question, pk=question_id, user=request.user)
    
    # flaw Cross-Site Request Forgery (CSRF)
    if request.method == "GET": #flaw fix -> if request.method == "POST":
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

def search(request):
    """
    Search for questions based on a keyword provided by GET request.

    Currently, this method uses a vulnerable SQL query prone to SQL injection.
    There's a safe parameterized query approach commented out.
    """
    keyword = request.GET.get('keyword')
    
    #Vulnerable SQL query
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM polls_question WHERE question_text LIKE '%" + keyword + "%'")
        # Fix by using parameterized queries:
        # cursor.execute("SELECT * FROM polls_question WHERE question_text LIKE %s", ['%' + keyword + '%'])

        rows = cursor.fetchall()
        columns = [col[0] for col in cursor.description]
        results = [
            dict(zip(columns, row))
            for row in rows
        ]

    return render(request, 'polls/search_results.html', {'results': results})





class LoginView(LoginView):
    """
    Logs every login attempt in the `LoginAttempt` model.
    If a user exceeds 5 failed login attempts, they are prevented
    from making another attempt for the next 5 minute.
        
    """

    # Monitoring logging attempts:

    """
    def post(self, request, *args, **kwargs):

        response = super().post(request, *args, **kwargs)
        username = request.POST.get('username')
        # computes the datetime 5 minutes prior to the current time.
        time_threshold = timezone.now() - timedelta(minutes=5)
        recent_attempts = LoginAttempt.objects.filter(username=username, timestamp__gte=time_threshold, success=False).count()
        
        if recent_attempts >= 5:
            return HttpResponse("Too many failed login attempts. Please wait 5 minutes and try again.")
        
        was_successful = response.status_code == 302  
        LoginAttempt.objects.create(username=username, success=was_successful)

        if was_successful:
            LoginAttempt.objects.filter(username=username, success=False).delete()
        
        return response

    """