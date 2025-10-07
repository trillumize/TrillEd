# academics/forms.py
from django import forms

class StudentUploadForm(forms.Form):
    file = forms.FileField(help_text="Upload CSV or Excel with columns: first_name, last_name")
