import io
import shutil
import tempfile
import zipfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import ProfileModel
from jobs.models import JobModel
from .forms import ApplicationForm
from .models import Application

User = get_user_model()


class ApplicationWorkflowTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.mkdtemp(prefix='careerconnect-test-media-')
        self.addCleanup(shutil.rmtree, self.media_dir, ignore_errors=True)
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

        self.candidate = User.objects.create_user(username='candidate', password='StrongPass!234')
        self.candidate_profile = ProfileModel.objects.create(
            user=self.candidate, role='candidate', full_name='Casey Candidate',
        )
        self.employer = User.objects.create_user(username='employer', password='StrongPass!234')
        self.employer_profile = ProfileModel.objects.create(
            user=self.employer, role='employer', full_name='Erin Employer',
        )
        self.other_employer = User.objects.create_user(username='otheremployer', password='StrongPass!234')
        self.other_employer_profile = ProfileModel.objects.create(user=self.other_employer, role='employer')
        self.job = JobModel.objects.create(
            employer=self.employer_profile, title='Django Developer', company_name='Acme',
            location='Pune', job_type='Full-time', work_mode='Hybrid',
            description='Build web applications.', requirements='Django experience.',
            salary_min=50000, salary_max=80000, salary_currency='INR',
            experience_level='Entry', vacancies=2, status='Published',
            application_deadline=timezone.now() + timedelta(days=5),
        )

    @staticmethod
    def pdf_upload(name='resume.pdf', content=b'%PDF-1.7\nvalid test PDF'):
        return SimpleUploadedFile(name, content, content_type='application/pdf')

    def create_application(self, candidate=None, job=None, resume=None, **kwargs):
        return Application.objects.create(
            candidate=candidate or self.candidate_profile,
            job=job or self.job,
            resume=resume or self.pdf_upload(),
            **kwargs,
        )

    def test_candidate_can_apply_with_valid_resume(self):
        self.client.force_login(self.candidate)
        response = self.client.post(reverse('applyjob', args=[self.job.pk]), {
            'resume': self.pdf_upload(), 'cover_letter': 'I am interested.',
        })
        self.assertRedirects(response, reverse('joblist'))
        application = Application.objects.get(candidate=self.candidate_profile, job=self.job)
        self.assertEqual(application.status, 'Submitted')
        self.assertTrue(application.resume.name.endswith('.pdf'))
        self.assertTrue(application.resume.storage.exists(application.resume.name))

    def test_duplicate_application_is_prevented(self):
        self.create_application()
        self.client.force_login(self.candidate)
        response = self.client.post(reverse('applyjob', args=[self.job.pk]), {
            'resume': self.pdf_upload('second.pdf'), 'cover_letter': '',
        })
        self.assertRedirects(response, reverse('joblist'))
        self.assertEqual(Application.objects.filter(candidate=self.candidate_profile, job=self.job).count(), 1)

    def test_application_form_rejects_disallowed_extension_and_invalid_documents(self):
        cases = [
            self.pdf_upload('resume.txt', b'%PDF-1.7'),
            self.pdf_upload('broken.pdf', b'not a PDF'),
            SimpleUploadedFile('broken.docx', b'not a zip', content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
        ]
        for upload in cases:
            with self.subTest(filename=upload.name):
                self.assertFalse(ApplicationForm(data={}, files={'resume': upload}).is_valid())

    def test_application_form_rejects_oversized_resume(self):
        upload = self.pdf_upload('large.pdf', b'%PDF-' + b'x' * (5 * 1024 * 1024))
        form = ApplicationForm(data={}, files={'resume': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('5 MB', str(form.errors))

    def test_application_form_accepts_minimal_structural_docx(self):
        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w') as docx:
            docx.writestr('[Content_Types].xml', '<Types/>')
            docx.writestr('word/document.xml', '<document/>')
        upload = SimpleUploadedFile(
            'resume.docx', content.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        )
        self.assertTrue(ApplicationForm(data={}, files={'resume': upload}).is_valid())

    def test_candidate_application_history_is_private(self):
        application = self.create_application()
        self.client.force_login(self.candidate)
        response = self.client.get(reverse('myapplications'))
        self.assertContains(response, self.job.title)
        self.assertContains(response, reverse('download_resume', args=[application.pk]))

        other_candidate = User.objects.create_user(username='othercandidate', password='StrongPass!234')
        other_profile = ProfileModel.objects.create(user=other_candidate, role='candidate')
        self.client.force_login(other_candidate)
        self.assertNotContains(self.client.get(reverse('myapplications')), self.job.title)

    def test_only_job_owner_can_view_applicants(self):
        application = self.create_application()
        self.client.force_login(self.employer)
        response = self.client.get(reverse('jobapplicants', args=[self.job.pk]))
        self.assertContains(response, self.candidate_profile.full_name)
        self.assertEqual(len(response.context['applications']), 1)

        other_job = JobModel.objects.create(
            employer=self.other_employer_profile, title='Other job', company_name='Other',
            location='Delhi', job_type='Full-time', work_mode='Remote', description='Job',
            requirements='Skill', salary_min=1, salary_max=2, experience_level='Entry',
        )
        self.assertEqual(self.client.get(reverse('jobapplicants', args=[other_job.pk])).context['applications'].count(), 0)
        self.client.force_login(self.candidate)
        self.assertRedirects(self.client.get(reverse('jobapplicants', args=[self.job.pk])), reverse('home'))

    def test_employer_can_update_status_only_for_own_job_applicant(self):
        application = self.create_application()
        self.client.force_login(self.employer)
        response = self.client.post(reverse('updatestatus', args=[application.pk]), {
            'status': 'Shortlisted', 'employer_note': 'Invite to interview.',
        })
        self.assertRedirects(response, reverse('jobapplicants', args=[self.job.pk]))
        application.refresh_from_db()
        self.assertEqual(application.status, 'Shortlisted')
        self.assertEqual(application.employer_note, 'Invite to interview.')

        self.client.force_login(self.other_employer)
        self.assertEqual(self.client.post(reverse('updatestatus', args=[application.pk]), {
            'status': 'Hired', 'employer_note': '',
        }).status_code, 404)

    def test_resume_download_is_authorized_by_candidate_or_job_owner(self):
        application = self.create_application()
        self.client.force_login(self.candidate)
        response = self.client.get(reverse('download_resume', args=[application.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'].split(';')[0], 'attachment')

        self.client.force_login(self.employer)
        self.assertEqual(self.client.get(reverse('download_resume', args=[application.pk])).status_code, 200)

    def test_resume_download_denies_unrelated_users_and_anonymous_users(self):
        application = self.create_application()
        unrelated_candidate = User.objects.create_user(username='unrelated', password='StrongPass!234')
        ProfileModel.objects.create(user=unrelated_candidate, role='candidate')
        self.client.force_login(unrelated_candidate)
        self.assertEqual(self.client.get(reverse('download_resume', args=[application.pk])).status_code, 404)

        self.client.force_login(self.other_employer)
        self.assertEqual(self.client.get(reverse('download_resume', args=[application.pk])).status_code, 404)

        self.client.logout()
        response = self.client.get(reverse('download_resume', args=[application.pk]))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('download_resume', args=[application.pk])}")
