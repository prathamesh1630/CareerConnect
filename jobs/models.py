from django.db import models
from accounts.models import ProfileModel

# Create your models here.
class JobModel(models.Model):
    employer = models.ForeignKey(ProfileModel,on_delete=models.CASCADE,limit_choices_to={'role':'employer'})
    title = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    job_type = models.CharField(max_length=100,choices=[('Full-time','Full-time'),('Part-time','Part-time'),('Internship','Internship'),('Contract','Contract'),('Freelance','Freelance')])
    work_mode = models.CharField(max_length=100,choices=[('On-site','On-site') ,('Hybrid','Hybrid'), ('Remote','Remote')])
    description = models.TextField(max_length=500)
    requirements = models.TextField(max_length=500)
    salary_min = models.DecimalField(max_digits=10,decimal_places=2,)
    salary_max = models.DecimalField(max_digits=10,decimal_places=2)
    salary_currency = models.CharField(max_length=3,default='INR',choices=[
            ('USD', 'US Dollar ($)'),
            ('EUR', 'Euro (€)'),
            ('GBP', 'British Pound (£)'),
            ('INR', 'Indian Rupee (₹)'),
            ('CAD', 'Canadian Dollar (C$)'),
            ('AUD', 'Australian Dollar (A$)'),
        ]
    )
    experience_level = models.CharField(max_length=100,choices=[('Fresher','Fresher'), ('Entry','Entry'),('Mid', 'Mid'), ('Senior','Senior') ])
    vacancies = models.IntegerField(default=1)
    application_deadline = models.DateTimeField(null=True,blank=True)
    status = models.CharField(max_length=100,choices=[ ('Draft','Draft'), ('Published','Published'), ('Closed','Closed'), ('Archived','Archived')],default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title