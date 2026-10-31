'''title, company_name, location, job_type,
work_mode, description, requirements,
salary_min, salary_max, experience_level,
vacancies, application_deadline, status if
permitted
'''

#Employer creates or edits a job.

from django import forms
from .models import JobModel
from django.utils import timezone

class JobForm(forms.ModelForm):
    application_deadline = forms.DateTimeField(
    required=False,
    widget=forms.DateTimeInput(
        attrs={'type': 'datetime-local'}))
    class Meta:
        model = JobModel
        fields = ['title', 'company_name', 'location', 'job_type', 'work_mode', 'description', 'requirements','salary_min', 'salary_max','salary_currency', 'experience_level','vacancies', 'application_deadline', 'status' ]

    def clean(self):
        cleaned_data = super().clean()
        min_sal = cleaned_data.get('salary_min')
        max_sal = cleaned_data.get('salary_max')
        if (min_sal is not None and min_sal < 0) or (max_sal is not None and max_sal < 0):
            raise forms.ValidationError('Salary amounts cannot be negative.')
        if min_sal is not None and max_sal is not None:
            if min_sal >= max_sal:
                raise forms.ValidationError('Minimum salary must be less than maximum salary.')
        return cleaned_data

    def clean_vacancies(self):
        vacancy = self.cleaned_data.get('vacancies')

        if vacancy is not None and vacancy <= 0:
            raise forms.ValidationError(
                'Vacancies must be greater than zero.'
            )

        return vacancy

    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')

        if deadline is not None:
            minimum_deadline = timezone.now() + timezone.timedelta(hours=16)

            if deadline <= minimum_deadline:
                raise forms.ValidationError(
                    'Application deadline must be at least 16 hours from now.'
                )

        return deadline


class JobSearchForm(forms.Form):
    location = forms.CharField(required=False)
    job_type = forms.ChoiceField(
        choices=[('', 'All Job Types')] + JobModel._meta.get_field('job_type').choices,
        required=False
    )
    work_mode = forms.ChoiceField(
        choices=[('', 'All Work Modes')] + JobModel._meta.get_field('work_mode').choices,
        required=False
    )
    experience_level = forms.ChoiceField(
        choices=[('', 'All Experience Levels')] + JobModel._meta.get_field('experience_level').choices,
        required=False
    )
