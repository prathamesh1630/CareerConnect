from django.urls import path
from . import views

urlpatterns = [
    path('jobs/<int:pk>/apply/', views.ApplyJobView, name='applyjob'),

    path('candidate/applications/', views.MyApplicationsView, name='myapplications'),

    path('employer/jobs/<int:job_pk>/applicants/', views.JobApplicantsView, name='jobapplicants'),

    path('employer/applications/<int:pk>/status/', views.UpdateApplicationStatusView, name='updatestatus'),
    path('applications/<int:pk>/resume/', views.DownloadResumeView, name='download_resume'),
]
