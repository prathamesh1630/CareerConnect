from django.shortcuts import get_object_or_404, redirect, render
from .forms import CandidateRegistrationForm,EmployerRegistrationForm,CandidateProfileForm,EmployerProfileForm
from django.views.generic import FormView
from django.urls import reverse_lazy
from .models import ProfileModel
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

# Create your views here.
class CandidateRegisterView(FormView):
    form_class = CandidateRegistrationForm
    template_name = 'accounts/register_candidate.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
            ProfileModel.objects.create(
                user=user,
                role='candidate',
                full_name=user.get_full_name().strip(),
            )
        messages.success(self.request, 'Candidate account created. You can now log in.')
        return super().form_valid(form)

class EmployerRegisterView(FormView):
    form_class = EmployerRegistrationForm
    template_name = 'accounts/register_employer.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
            ProfileModel.objects.create(
                user=user,
                role='employer',
                full_name=user.get_full_name().strip(),
            )
        messages.success(self.request, 'Employer account created. You can now log in.')
        return super().form_valid(form)

class CandidateProfileView(LoginRequiredMixin, FormView):
    form_class = CandidateProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        profile = ProfileModel.objects.get(
            user=self.request.user,
            role='candidate'
        )
        form.instance = profile
        form.save()

        return super().form_valid(form)


class EmployerProfileView(LoginRequiredMixin, FormView):
    form_class = EmployerProfileForm
    template_name = 'accounts/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.request.user.profile
        return kwargs

    def form_valid(self, form):
        profile = ProfileModel.objects.get(
            user=self.request.user,
            role='employer'
        )
        form.instance = profile
        form.save()

        return super().form_valid(form)

@login_required
def profile_detail(request, pk=None):
    profile = request.user.profile if pk is None else get_object_or_404(
        ProfileModel, pk=pk, user=request.user
    )

    return render(request, 'accounts/profile.html', {'profile': profile})

@login_required
def update_profile(request, pk=None):
    profile = request.user.profile if pk is None else get_object_or_404(
        ProfileModel, pk=pk, user=request.user
    )

    # Select the form based on the profile's role
    if profile.role == 'candidate':
        FormClass = CandidateProfileForm
    else:
        FormClass = EmployerProfileForm
    if request.method == 'POST':
        fm = FormClass(instance=profile,data=request.POST)
        if fm.is_valid():
            fm.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile_detail',pk=profile.pk)
        context = {
            'form':fm
        }
        return render(request, 'accounts/profile_edit.html', context)
    context = {
        'form' : FormClass(instance=profile)
    }
    return render(request, 'accounts/profile_edit.html', context)
