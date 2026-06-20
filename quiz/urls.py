from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'quiz'

urlpatterns = [
    # AUTH
    path('', auth_views.LoginView.as_view(
        template_name='quiz/login.html'
    ), name='login'),

    path('login/', auth_views.LoginView.as_view(
        template_name='quiz/login.html'
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('signup/', views.signup, name='signup'),

    # QUIZ
    path('subjects/', views.subject_list, name='subject_list'),
    path('subject/<int:subject_id>/start/', views.start_quiz, name='start_quiz'),
    path('subject/<int:subject_id>/question/', views.quiz_question, name='quiz_question'),
    path('subject/<int:subject_id>/result/', views.quiz_result, name='quiz_result'),

    path("student-level-json/", views.student_level_json, name="student_level_json"),
]