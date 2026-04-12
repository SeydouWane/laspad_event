from django import forms
from .models import Event, Location, EventDay, Session


class LocationForm(forms.ModelForm):
    class Meta:
        model  = Location
        fields = ['mode', 'platform', 'online_link', 'address', 'city', 'country', 'google_maps_url']
        widgets = {
            'mode':           forms.Select(attrs={'class': 'form-select', 'id': 'id_mode'}),
            'platform':       forms.Select(attrs={'class': 'form-select'}),
            'online_link':    forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://meet.google.com/...'}),
            'address':        forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Adresse complète'}),
            'city':           forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Dakar'}),
            'country':        forms.TextInput(attrs={'class': 'form-input'}),
            'google_maps_url': forms.URLInput(attrs={'class': 'form-input'}),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model  = Event
        fields = [
            'title', 'description', 'event_type', 'status',
            'start_datetime', 'end_datetime',
            # Hybride
            'participation_mode',
            'max_onsite', 'access_onsite', 'auto_accept_onsite',
            'max_online', 'access_online', 'auto_accept_online',
            # Legacy
            'is_capacity_limited', 'max_participants', 'access_mode',
            'speakers', 'banner',
        ]
        widgets = {
            'title':              forms.TextInput(attrs={'class': 'form-input', 'placeholder': "Titre de l'événement"}),
            'description':        forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'event_type':         forms.Select(attrs={'class': 'form-select'}),
            'status':             forms.Select(attrs={'class': 'form-select'}),
            'start_datetime':     forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'end_datetime':       forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'participation_mode': forms.Select(attrs={'class': 'form-select', 'id': 'id_participation_mode'}),
            'access_onsite':      forms.Select(attrs={'class': 'form-select'}),
            'access_online':      forms.Select(attrs={'class': 'form-select'}),
            'max_onsite':         forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Illimité si vide'}),
            'max_online':         forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Illimité si vide'}),
            'auto_accept_onsite': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Ex: 50'}),
            'auto_accept_online': forms.NumberInput(attrs={'class': 'form-input', 'min': 1, 'placeholder': 'Ex: 200'}),
            'is_capacity_limited': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'max_participants':   forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'access_mode':        forms.Select(attrs={'class': 'form-select'}),
            'speakers':           forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_datetime')
        end   = cleaned.get('end_datetime')
        if start and end and end <= start:
            raise forms.ValidationError("La date de fin doit être après la date de début.")
        if cleaned.get('is_capacity_limited') and not cleaned.get('max_participants'):
            raise forms.ValidationError("Veuillez indiquer le nombre maximum de participants.")
        return cleaned


class EventDayForm(forms.ModelForm):
    class Meta:
        model  = EventDay
        fields = ['date', 'title', 'description', 'order']
        widgets = {
            'date':        forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'title':       forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Ex: Jour 1 — Ouverture'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
            'order':       forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
        }


class SessionForm(forms.ModelForm):
    class Meta:
        model  = Session
        fields = ['start_time', 'end_time', 'title', 'description', 'speaker', 'location_note', 'mode', 'order']
        widgets = {
            'start_time':    forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'end_time':      forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'title':         forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Titre de la session'}),
            'description':   forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
            'speaker':       forms.Select(attrs={'class': 'form-select'}),
            'location_note': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Salle A, Zoom Room 2...'}),
            'mode':          forms.Select(attrs={'class': 'form-select'}),
            'order':         forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
        }