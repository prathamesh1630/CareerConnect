from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ProfileModel

class CandidateRegistrationForm(UserCreationForm):
    #username, email, password, password confirmation, optional full_name
    class Meta :
        model = User
        fields = ['first_name','last_name','email','username','password1','password2']

class EmployerRegistrationForm(UserCreationForm):
    #username, email, password, password confirmation, optional full_name,company name
    class Meta :
        model = User
        fields = ['first_name','last_name','email','username','password1','password2']

class CandidateProfileForm(forms.ModelForm):
    class Meta :
        model = ProfileModel
        fields = ['full_name', 'phone', 'location', 'headline', 'skills', 'bio']

class EmployerProfileForm(forms.ModelForm):
    class Meta :
        model = ProfileModel
        fields = ['full_name', 'phone', 'company_name', 'location', 'bio']
