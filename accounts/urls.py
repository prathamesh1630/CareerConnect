
from django.urls import path
from django.contrib.auth import views as auth_view
from . import views

urlpatterns = [
    path('login/', auth_view.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_view.LogoutView.as_view(), name='logout'),

    path('candidate_register/', views.CandidateRegisterView.as_view(), name='register_candidate'),
    path('employer_register/', views.EmployerRegisterView.as_view(), name='register_employer'),

    path('profile/', views.profile_detail, name='profile'),
    path('profile/edit/', views.update_profile, name='profile_edit'),
    path('profile_detail/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('update_profile/<int:pk>/', views.update_profile, name='update_profile'),
]
