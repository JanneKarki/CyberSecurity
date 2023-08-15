from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'polls'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('<int:pk>/results/', views.ResultsView.as_view(), name='results'),
    path('<int:question_id>/vote/', views.vote, name='vote'),
    path('login/', auth_views.LoginView.as_view(template_name='polls/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='polls:index'), name='logout'),
    path('add/', views.add_question, name='add_question'),
    path('<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('<int:question_id>/add_choice/', views.add_choice, name='add_choice'),
    path('choice/<int:choice_id>/edit/', views.edit_choice, name='edit_choice'),
    path('choice/<int:choice_id>/delete/', views.delete_choice, name='delete_choice'),
]
