from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import ProfileModel
from .models import JobModel

User = get_user_model()


class JobWorkflowTests(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(username='employer', password='StrongPass!234')
        self.employer_profile = ProfileModel.objects.create(
            user=self.employer, role='employer', full_name='Employer', company_name='Acme',
        )
        self.client.force_login(self.employer)

    def job_data(self, **overrides):
        data = {
            'title': 'Django Developer', 'company_name': 'Acme', 'location': 'Pune',
            'job_type': 'Full-time', 'work_mode': 'Hybrid',
            'description': 'Build web applications.', 'requirements': 'Django experience.',
            'salary_min': '50000', 'salary_max': '80000', 'salary_currency': 'INR',
            'experience_level': 'Entry', 'vacancies': '2',
            'application_deadline': (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%dT%H:%M'),
            'status': 'Published',
        }
        return {**data, **overrides}

    def create_job(self, owner=None, **overrides):
        data = {
            'title': 'Django Developer', 'company_name': 'Acme', 'location': 'Pune',
            'job_type': 'Full-time', 'work_mode': 'Hybrid', 'description': 'Build web applications.',
            'requirements': 'Django experience.', 'salary_min': 50000, 'salary_max': 80000,
            'salary_currency': 'INR', 'experience_level': 'Entry', 'vacancies': 2,
            'status': 'Published',
        }
        return JobModel.objects.create(employer=owner or self.employer_profile, **{**data, **overrides})

    def test_employer_can_create_job(self):
        response = self.client.post(reverse('jobcreate'), self.job_data())
        self.assertRedirects(response, reverse('employerjobs'))
        job = JobModel.objects.get(title='Django Developer')
        self.assertEqual(job.employer, self.employer_profile)
        self.assertEqual(job.status, 'Published')

    def test_job_form_rejects_invalid_salary_and_vacancy_values(self):
        invalid_cases = [
            {'salary_min': '90000', 'salary_max': '80000'},
            {'salary_min': '-1'},
            {'vacancies': '0'},
        ]
        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                response = self.client.post(reverse('jobcreate'), self.job_data(**overrides))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(JobModel.objects.count(), 0)

    def test_employer_can_update_and_delete_own_job(self):
        job = self.create_job()
        response = self.client.post(reverse('jobupdate', args=[job.pk]), self.job_data(title='Senior Django Developer'))
        self.assertRedirects(response, reverse('employerjobs'))
        job.refresh_from_db()
        self.assertEqual(job.title, 'Senior Django Developer')

        response = self.client.post(reverse('jobdelete', args=[job.pk]))
        self.assertRedirects(response, reverse('employerjobs'))
        self.assertFalse(JobModel.objects.filter(pk=job.pk).exists())

    def test_employer_cannot_update_or_delete_another_employers_job(self):
        another_user = User.objects.create_user(username='another', password='StrongPass!234')
        another_profile = ProfileModel.objects.create(user=another_user, role='employer')
        job = self.create_job(owner=another_profile)
        self.assertEqual(self.client.get(reverse('jobupdate', args=[job.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('jobupdate', args=[job.pk]), self.job_data()).status_code, 404)
        self.assertEqual(self.client.get(reverse('jobdelete', args=[job.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('jobdelete', args=[job.pk])).status_code, 404)
        self.assertTrue(JobModel.objects.filter(pk=job.pk).exists())

    def test_employer_can_close_only_own_job_with_post(self):
        job = self.create_job()
        response = self.client.post(reverse('jobclose', args=[job.pk]))
        self.assertRedirects(response, reverse('employerjobs'))
        job.refresh_from_db()
        self.assertEqual(job.status, 'Closed')

    def test_only_published_and_unexpired_jobs_are_public(self):
        public_job = self.create_job()
        self.create_job(title='Draft job', status='Draft')
        self.create_job(title='Expired job', application_deadline=timezone.now() - timedelta(days=1))
        response = self.client.get(reverse('joblist'))
        self.assertContains(response, public_job.title)
        self.assertNotContains(response, 'Draft job')
        self.assertNotContains(response, 'Expired job')

    def test_job_search_filters_location_and_type(self):
        self.create_job()
        self.create_job(title='Remote internship', location='Delhi', job_type='Internship', work_mode='Remote')
        response = self.client.get(reverse('joblist'), {'location': 'Pune', 'job_type': 'Full-time'})
        self.assertContains(response, 'Django Developer')
        self.assertNotContains(response, 'Remote internship')

    def test_job_list_paginates_ten_results_and_keeps_search_query(self):
        for index in range(12):
            self.create_job(title=f'Developer {index}')
        response = self.client.get(reverse('joblist'), {'location': 'Pune'})
        self.assertEqual(len(response.context['jobs']), 10)
        self.assertTrue(response.context['is_paginated'])
        self.assertContains(response, 'page=2')
