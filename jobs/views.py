from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.list import ListView
from .models import JobModel
from django.views.generic import DetailView,CreateView,UpdateView,DeleteView
from .forms import JobForm,JobSearchForm
from django.urls import reverse_lazy
from django.db import models
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
# Create your views here.

class EmployerRequiredMixin(LoginRequiredMixin):

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        profile = getattr(request.user, 'profile', None)
        if profile is None or profile.role != 'employer':
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)

class HomeView(ListView):
    model = JobModel
    template_name = 'home.html'
    context_object_name = 'jobs'

    def get_queryset(self):
        return JobModel.objects.filter(status='Published').filter(
            models.Q(application_deadline__isnull=True) |
            models.Q(application_deadline__gte=timezone.now())
        ).order_by('-created_at')[:6]


class JobListView(ListView):
    model = JobModel
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10
    ordering = ['-created_at']

    def get_queryset(self):
        jobs = JobModel.objects.filter(status='Published')

        jobs = jobs.filter(
            models.Q(application_deadline__isnull=True) |
            models.Q(application_deadline__gte=timezone.now())
        )

        form = JobSearchForm(self.request.GET)
        if form.is_valid():
            location = form.cleaned_data.get('location')
            if location:
                jobs = jobs.filter(location__icontains=location)
            for field in ('job_type', 'work_mode', 'experience_level'):
                value = form.cleaned_data.get(field)
                if value:
                    jobs = jobs.filter(**{field: value})
        return jobs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = JobSearchForm(self.request.GET or None)
        return context

class JobDetailView(DetailView):
    model = JobModel
    template_name = 'jobs/one_job.html'
    context_object_name = 'job'

    def get_queryset(self):
        return JobModel.objects.filter(status='Published').filter(
            models.Q(application_deadline__isnull=True) |
            models.Q(application_deadline__gte=timezone.now())
        )

@login_required
def EmployerJobListView(request):
    profile = getattr(request.user, 'profile', None)
    if profile is None or profile.role != 'employer':
        return redirect('home')
    jobs = JobModel.objects.filter(employer=profile)
    context = {
        'jobs' : jobs
    }
    return render(request,'employerjobs.html',context)

class JobCreateView(EmployerRequiredMixin, CreateView):
    model = JobModel
    form_class = JobForm
    template_name = 'create_job.html'
    success_url = reverse_lazy('employerjobs')

    def form_valid(self, form):
        form.instance.employer = self.request.user.profile
        response = super().form_valid(form)
        messages.success(self.request, 'Job posted successfully.')
        return response

class JobUpdateView(EmployerRequiredMixin,UpdateView):
    model = JobModel
    form_class = JobForm
    template_name = 'update_job.html'
    success_url = reverse_lazy('employerjobs')

    def get_queryset(self):
        return JobModel.objects.filter(
            employer=self.request.user.profile
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Job updated successfully.')
        return response

@login_required
def JobCloseView(request, pk):

    profile = getattr(request.user, 'profile', None)
    if profile is None or profile.role != 'employer':
        return redirect('home')

    obj = get_object_or_404(JobModel,
        pk=pk,
        employer=profile
    )

    if request.method == 'POST':
        obj.status = 'Closed'
        obj.save()
        messages.success(request, 'Job closed successfully.')
        return redirect('employerjobs')

    return render(request, 'close_job.html', {'job': obj})

class JobDeleteView(EmployerRequiredMixin,DeleteView):
    model = JobModel
    template_name = 'delete_job.html'
    context_object_name = 'job'
    success_url = reverse_lazy('employerjobs')

    def get_queryset(self):
        return JobModel.objects.filter(
            employer=self.request.user.profile
        )

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Job deleted successfully.')
        return super().delete(request, *args, **kwargs)
