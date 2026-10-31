# Create your models here.

from django.db import models
from django.contrib.auth.models import User


class ProfileModel(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    role = models.CharField(max_length=10,choices=[
        ('candidate', 'Candidate'),
        ('employer', 'Employer')
    ])
    full_name = models.CharField(max_length=100,blank=True)
    phone = models.CharField(max_length=20,blank=True)
    location = models.CharField(max_length=100,blank=True)
    headline = models.CharField(max_length=100,blank=True)
    skills = models.TextField(blank=True)
    bio = models.TextField(blank=True )
    company_name = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name or self.user.username} ({self.role})"
