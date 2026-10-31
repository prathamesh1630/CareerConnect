from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('jobs/', views.JobListView.as_view(), name='joblist'),
    path('jobs/<int:pk>/', views.JobDetailView.as_view(), name='jobdetail'),

    path('employer/jobs/', views.EmployerJobListView, name='employerjobs'),
    path('employer/jobs/create/', views.JobCreateView.as_view(), name='jobcreate'),
    path('employer/jobs/<int:pk>/update/', views.JobUpdateView.as_view(), name='jobupdate'),
    path('employer/jobs/<int:pk>/close/', views.JobCloseView, name='jobclose'),
    path('employer/jobs/<int:pk>/delete/', views.JobDeleteView.as_view(), name='jobdelete'),
]