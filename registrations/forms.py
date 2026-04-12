from django import forms
from .models import Registration


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
        widget=forms.Textarea(attrs={
            'class': 'form-textarea', 'rows': 3,
            'placeholder': 'Pourquoi souhaitez-vous participer ?',
        }),
    )

    # ── Mode de participation (injecté dynamiquement selon l'événement) ──
    participation_type = forms.ChoiceField(
        label='Mode de participation',
        choices=[],  # rempli dans __init__
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        required=True,
    )

    rgpd_consent = forms.BooleanField(
        label="J'accepte que mes données soient utilisées pour la gestion de cet événement.",
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

        if event is None:
            return

        mode = getattr(event, 'participation_mode', 'online_only')

        if mode == 'onsite_only':
            self.fields['participation_type'].choices = [
                (Registration.PARTICIPATION_ONSITE, 'Présentiel'),
            ]
            self.fields['participation_type'].initial = Registration.PARTICIPATION_ONSITE

        elif mode == 'online_only':
            self.fields['participation_type'].choices = [
                (Registration.PARTICIPATION_ONLINE, 'En ligne'),
            ]
            self.fields['participation_type'].initial = Registration.PARTICIPATION_ONLINE

        else:  # hybrid
            choices = []
            if not event.is_full_onsite:
                choices.append((Registration.PARTICIPATION_ONSITE, 'Présentiel'))
            if not event.is_full_online:
                choices.append((Registration.PARTICIPATION_ONLINE, 'En ligne'))
            # "Les deux" seulement si les deux sont disponibles
            if not event.is_full_onsite and not event.is_full_online:
                choices.append((Registration.PARTICIPATION_BOTH, 'Les deux (présentiel + en ligne)'))
            self.fields['participation_type'].choices = choices

    def clean_email(self):
        return self.cleaned_data['email'].lower().strip()

    def clean(self):
        cleaned = super().clean()
        ptype = cleaned.get('participation_type')
        event = self.event

        if event and ptype and hasattr(event, 'participation_mode'):
            if ptype in [Registration.PARTICIPATION_ONSITE, Registration.PARTICIPATION_BOTH]:
                if event.is_full_onsite:
                    self.add_error(
                        'participation_type',
                        "Désolé, les places en présentiel sont complètes."
                    )
            if ptype in [Registration.PARTICIPATION_ONLINE, Registration.PARTICIPATION_BOTH]:
                if event.is_full_online:
                    self.add_error(
                        'participation_type',
                        "Désolé, les places en ligne sont complètes."
                    )
        return cleaned