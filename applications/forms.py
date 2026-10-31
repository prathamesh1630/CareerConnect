from django import forms
from .models import Application
import os
import zipfile


class ApplicationForm(forms.ModelForm):

    class Meta:
        model = Application
        fields = ['resume', 'cover_letter']

    def clean_resume(self):
        resume = self.cleaned_data.get('resume')

        if resume:
            ext = os.path.splitext(resume.name)[1].lower()

            if ext not in ['.pdf', '.docx']:
                raise forms.ValidationError(
                    'Only PDF and DOCX files are allowed.'
                )

            if resume.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    'Resume size must not exceed 5 MB.'
                )

            resume.seek(0)
            if ext == '.pdf':
                valid_file = resume.read(1024).lstrip().startswith(b'%PDF-')
            else:
                try:
                    with zipfile.ZipFile(resume) as document:
                        names = set(document.namelist())
                    valid_file = {
                        '[Content_Types].xml', 'word/document.xml'
                    }.issubset(names)
                except (zipfile.BadZipFile, OSError):
                    valid_file = False
            resume.seek(0)

            if not valid_file:
                raise forms.ValidationError(
                    'The uploaded file does not appear to be a valid PDF or DOCX document.'
                )

        return resume


class ApplicationStatusForm(forms.ModelForm):

    class Meta:
        model = Application
        fields = ['status', 'employer_note']
