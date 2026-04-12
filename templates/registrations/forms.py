from django import forms
from .models import Participant, Registration


class RegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        label='Prénom',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Votre prénom'}),
    )
    last_name = forms.CharField(
        max_length=100,
        label='Nom',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Votre nom'}),
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'votre@email.com'}),
    )
    institution = forms.CharField(
        max_length=200,
        label='Institution / Organisation',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Université, ONG, Entreprise...'}),
    )
    role = forms.CharField(
        max_length=150,
        label='Fonction / Poste',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Chercheur, Étudiant, Manager...'}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label='Téléphone (optionnel)',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+221 77 000 00 00'}),
    )
    motivation = forms.CharField(
        required=False,
        label='Motivation / Message (optionnel)',
        widget=forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3,
                                     'placeholder': 'Pourquoi souhaitez-vous participer ?'}),
    )
    newsletter = forms.BooleanField(
        required=False,
        label='Je souhaite être informé(e) des prochains événements et activités du LASPAD.',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        initial=True,
    )
    rgpd_consent = forms.BooleanField(
        label='J\'accepte que mes données soient utilisées pour la gestion de cet événement.',
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )

    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()