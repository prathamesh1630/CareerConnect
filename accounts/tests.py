from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import ProfileModel

User = get_user_model()


class AccountWorkflowTests(TestCase):
    def test_candidate_registration_creates_candidate_profile(self):
        response = self.client.post(reverse('register_candidate'), {
            'first_name': 'Casey', 'last_name': 'Candidate',
            'email': 'casey@example.com', 'username': 'casey',
            'password1': 'StrongPass!234', 'password2': 'StrongPass!234',
        })
        self.assertRedirects(response, reverse('login'))
        profile = ProfileModel.objects.get(user__username='casey')
        self.assertEqual(profile.role, 'candidate')
        self.assertEqual(profile.full_name, 'Casey Candidate')

    def test_employer_registration_creates_employer_profile(self):
        response = self.client.post(reverse('register_employer'), {
            'first_name': 'Elliot', 'last_name': 'Employer',
            'email': 'elliot@example.com', 'username': 'elliot',
            'password1': 'StrongPass!234', 'password2': 'StrongPass!234',
        })
        self.assertRedirects(response, reverse('login'))
        self.assertEqual(ProfileModel.objects.get(user__username='elliot').role, 'employer')

    def test_registration_rejects_mismatched_passwords(self):
        response = self.client.post(reverse('register_candidate'), {
            'username': 'casey', 'password1': 'StrongPass!234', 'password2': 'DifferentPass!234',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='casey').exists())
        self.assertContains(response, 'password')

    def test_login_and_post_logout(self):
        user = User.objects.create_user(username='casey', password='StrongPass!234')
        ProfileModel.objects.create(user=user, role='candidate')
        response = self.client.post(reverse('login'), {
            'username': 'casey', 'password': 'StrongPass!234',
        })
        self.assertRedirects(response, reverse('home'))
        self.assertTrue('_auth_user_id' in self.client.session)
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_invalid_login_does_not_authenticate(self):
        User.objects.create_user(username='casey', password='StrongPass!234')
        response = self.client.post(reverse('login'), {
            'username': 'casey', 'password': 'incorrect',
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_csrf_middleware_rejects_post_without_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse('login'), {
            'username': 'casey', 'password': 'StrongPass!234',
        })
        self.assertEqual(response.status_code, 403)

    def test_profile_requires_login_and_employer_route_checks_role(self):
        response = self.client.get(reverse('profile'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('profile')}")

        candidate = User.objects.create_user(username='candidate', password='StrongPass!234')
        ProfileModel.objects.create(user=candidate, role='candidate')
        self.client.force_login(candidate)
        response = self.client.get(reverse('jobcreate'))
        self.assertRedirects(response, reverse('home'))

    def test_authenticated_user_without_profile_is_denied_employer_routes(self):
        user = User.objects.create_user(username='staff', password='StrongPass!234')
        self.client.force_login(user)
        self.assertRedirects(self.client.get(reverse('jobcreate')), reverse('home'))

    def test_profile_view_and_edit_are_scoped_to_signed_in_user(self):
        user = User.objects.create_user(username='casey', password='StrongPass!234')
        profile = ProfileModel.objects.create(user=user, role='candidate', full_name='Casey')
        other = User.objects.create_user(username='other', password='StrongPass!234')
        other_profile = ProfileModel.objects.create(user=other, role='candidate')
        self.client.force_login(user)

        self.assertContains(self.client.get(reverse('profile')), 'Casey')
        response = self.client.post(reverse('profile_edit'), {
            'full_name': 'Casey Updated', 'phone': '1234567890', 'location': 'Pune',
            'headline': 'Developer', 'skills': 'Django', 'bio': 'Candidate profile',
        })
        self.assertRedirects(response, reverse('profile_detail', args=[profile.pk]))
        profile.refresh_from_db()
        self.assertEqual(profile.full_name, 'Casey Updated')
        self.assertEqual(self.client.get(reverse('profile_detail', args=[other_profile.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('update_profile', args=[other_profile.pk]), {}).status_code, 404)
