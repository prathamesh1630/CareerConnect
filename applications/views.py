from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.db import IntegrityError
from django.http import FileResponse, Http404
from jobs.models import JobModel
from .models import Application
from .forms import ApplicationForm, ApplicationStatusForm


@login_required
def ApplyJobView(request, pk):

    profile = getattr(request.user, 'profile', None)
    if profile is None or profile.role != 'candidate':
        return redirect('home')

    try:
        job = JobModel.objects.get(pk=pk)
    except JobModel.DoesNotExist:
        return redirect('joblist')

    if job.status != 'Published':
        return redirect('joblist')

    if job.application_deadline and job.application_deadline <= timezone.now():
        return redirect('joblist')

    if Application.objects.filter(
        candidate=profile,
        job=job
    ).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('joblist')

    if request.method == 'POST':
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():
            application = form.save(commit=False)
            application.candidate = profile
            application.job = job

            try:
                application.save()
                messages.success(request, 'Application submitted successfully!')
                return redirect('joblist')
            except IntegrityError:
                messages.warning(request, 'You have already applied for this job.')
                return redirect('joblist')

    else:
        form = ApplicationForm()

    return render(request, 'apply_job.html', {
        'form': form,
        'job': job
    })

@login_required
def MyApplicationsView(request):

    profile = getattr(request.user, 'profile', None)
    if profile is None or profile.role != 'candidate':
        return redirect('home')

    applications = Application.objects.filter(
        candidate=profile
    ).select_related('job').order_by('-applied_at')

    return render(request, 'my_applications.html', {
        'applications': applications
    })

@login_required
def JobApplicantsView(request, job_pk):

    profile = getattr(request.user, 'profile', None)
    if profile is None or profile.role != 'employer':
        return redirect('home')

    applications = Application.objects.filter(
        job__pk=job_pk,
        job__employer=profile
    ).select_related('candidate').order_by('-applied_at')

    return render(request, 'job_applicants.html', {
        'applications': applications
    })

@login_required
def UpdateApplicationStatusView(request, pk):

    profile = getattr(request.user, 'profile', None)
    if profile is None or profile.role != 'employer':
        return redirect('home')

    application = get_object_or_404(Application,
        pk=pk,
        job__employer=profile
    )

    if request.method == 'POST':
        form = ApplicationStatusForm(request.POST, instance=application)

        if form.is_valid():
            form.save()
            messages.success(request, 'Application status updated.')
            return redirect(
                'jobapplicants',
                job_pk=application.job.pk
            )

    else:
        form = ApplicationStatusForm(instance=application)

    return render(request, 'update_application.html', {
        'form': form,
        'application': application
    })


@login_required
def DownloadResumeView(request, pk):
    profile = getattr(request.user, 'profile', None)
    if profile is None:
        raise Http404
    if profile.role == 'candidate':
        application = get_object_or_404(
            Application, pk=pk, candidate=profile
        )
    elif profile.role == 'employer':
        application = get_object_or_404(
            Application, pk=pk, job__employer=profile
        )
    else:
        raise Http404

    if not application.resume:
        raise Http404

    filename = application.resume.name.rsplit('/', 1)[-1]
    return FileResponse(
        application.resume.open('rb'),
        as_attachment=True,
        filename=filename,
    )
