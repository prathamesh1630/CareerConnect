from django.db import models
from accounts.models import ProfileModel
from jobs.models import JobModel


class Application(models.Model):

    STATUS_CHOICES = [
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Rejected', 'Rejected'),
        ('Hired', 'Hired'),
        ('Withdrawn', 'Withdrawn'),
    ]

    candidate = models.ForeignKey(
        ProfileModel,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'candidate'}
    )

    job = models.ForeignKey(
        JobModel,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    resume = models.FileField(upload_to='resumes/')
    cover_letter = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Submitted'
    )

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    employer_note = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['candidate', 'job'],
                name='unique_candidate_job_application'
            )
        ]

    def __str__(self):
        return f"{self.candidate.full_name} - {self.job.title}"