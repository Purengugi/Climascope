from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.contrib.auth.models import User
from .models import UserProfile, FavoriteCity

class SignUpForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
        
    def save(self, commit=True):
        # BUG FIX: Ensure first_name, last_name, and email are saved to the User model
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # ADDED: Ensure UserProfile is created immediately
            UserProfile.objects.get_or_create(user=user)
        return user

# FIXED: UserProfileForm - removed temperature_unit field
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['location', 'avatar']  # Removed temperature_unit
        widgets = {
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City, Country'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

# Custom PasswordChangeForm (wraps the validation logic from the snippet)
class PasswordChangeForm(DjangoPasswordChangeForm):
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        # Apply Bootstrap classes/placeholders
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Current Password'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'New Password'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirm New Password'})

    # The clean_new_password1/2 methods from the original snippet are correctly implemented here.
    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('The new passwords do not match.')
        return password2
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        
        if len(password) < 8:
            raise forms.ValidationError('Password must be at least 8 characters long.')
        
        if password.isdigit():
            raise forms.ValidationError('Password cannot be entirely numeric.')
        
        if not any(c.isalpha() for c in password):
            raise forms.ValidationError('Password must contain at least one letter.')
            
        if not any(c.isdigit() for c in password):
            raise forms.ValidationError('Password must contain at least one number.')
        
        # Check if password is too similar to username or email
        user = getattr(self, 'user', None)
        if user and (password.lower() in user.username.lower() or user.username.lower() in password.lower()):
            raise forms.ValidationError('Password cannot be too similar to your username.')
        
        return password

class FavoriteCityAlertForm(forms.ModelForm):
    """Form for managing alert settings for favorite cities"""
    
    class Meta:
        model = FavoriteCity
        fields = ('temperature_threshold_high', 'temperature_threshold_low', 
                 'notify_rain', 'notify_extreme_weather')
        widgets = {
            'temperature_threshold_high': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 35',
                'step': '0.1',
                'min': '-50',
                'max': '60'
            }),
            'temperature_threshold_low': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 5',
                'step': '0.1',
                'min': '-50',
                'max': '60'
            }),
            'notify_rain': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notify_extreme_weather': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['temperature_threshold_high'].help_text = "Get alert when temperature goes above this value (°C)"
        self.fields['temperature_threshold_low'].help_text = "Get alert when temperature goes below this value (°C)"
        self.fields['notify_rain'].help_text = "Get notified when rain is expected"
        self.fields['notify_extreme_weather'].help_text = "Get urgent alerts for storms, severe weather"
    
    def clean(self):
        cleaned_data = super().clean()
        temp_high = cleaned_data.get('temperature_threshold_high')
        temp_low = cleaned_data.get('temperature_threshold_low')
        
        if temp_high is not None and temp_low is not None:
            if temp_high <= temp_low:
                raise forms.ValidationError(
                    "High temperature threshold must be greater than low temperature threshold."
                )
        
        return cleaned_data

class AccountDeactivationForm(forms.Form):
    """Form for account deactivation confirmation"""
    confirm_deactivation = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I understand that deactivating my account will:"
    )
    
    reason = forms.ChoiceField(
        choices=[
            ('temporary_break', 'Taking a temporary break'),
            ('privacy_concerns', 'Privacy concerns'),
            ('not_useful', 'App not useful anymore'),
            ('technical_issues', 'Technical issues'),
            ('other', 'Other reason')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label="Reason for deactivation (optional)"
    )
    
    additional_feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional feedback to help us improve...'
        }),
        required=False,
        label="Additional feedback (optional)"
    )

class AccountDeletionForm(forms.Form):
    """Form for permanent account deletion confirmation"""
    confirm_deletion = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="I understand this action cannot be undone"
    )
    
    type_delete = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Type DELETE to confirm'
        }),
        label='Type "DELETE" to confirm permanent deletion'
    )
    
    def clean_type_delete(self):
        value = self.cleaned_data['type_delete']
        if value != 'DELETE':
            raise forms.ValidationError('You must type "DELETE" exactly to confirm.')
        return value