from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.forms import TextInput, PasswordInput

from home_app.models import UserSettings


class AuthForm(forms.Form):
    username = forms.CharField(max_length=25, min_length=5, widget=TextInput(attrs={
        'style': 'background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)',
        "class": "form-input"
    }), label="Имя пользователя")
    password = forms.CharField(max_length=64, min_length=8, widget=PasswordInput(attrs={
        'style': 'background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)',
        "class": "form-input"
    }), label="Пароль")


class UploadAvatarForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ("avatar",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["avatar"].required, self.fields["avatar"].label = False, "Ваш аватар:"
        self.fields["avatar"].widget = forms.ClearableFileInput(attrs={
            'style': 'background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)'
        })


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Имя пользователя должно быть 5<=длина имени<=25, " \
                                            "не может состоять только из чисел"
        self.fields['password1'].help_text = "Пароль должен быть 8<=длина пароля<=64, " \
                                             "быть не простым, состоять не только из чисел."
        self.fields["password2"].help_text = "Повторите пароль."
        self.fields["username"].label = "Имя пользователя"
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Подтверждение пароляв"

        for field, input in {"username": TextInput, "password1": PasswordInput, "password2": PasswordInput}.items():
            self.fields[field].widget = input(attrs={
                'style': 'background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)'
            })

    def clean_username(self):
        username = self.cleaned_data["username"]
        if len(username) > 25 or len(username) < 5:
            raise forms.ValidationError("Имя пользователя должно быть 5<=длина имени<=25.")
        elif username.isnumeric() is True:
            raise forms.ValidationError("Имя пользователя не может состоять только из чисел.")

        return username

    def clean_password1(self):
        password1 = self.cleaned_data["password1"]
        if len(password1) > 64 or len(password1) < 8:
            raise forms.ValidationError("Пароль должен быть 8<=длина пароля<=64.")

        return password1
