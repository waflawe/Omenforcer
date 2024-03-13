from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from django.forms import TextInput, PasswordInput

from services.schemora.settings import get_user_settings_model
from forum.settings import MEDIA_ROOT, CUSTOM_USER_AVATARS_DIR, BASE_DIR

import os
from typing import Literal

UserSettings = get_user_settings_model()


def clean_custom_user_avatars_dir(user: User) -> Literal[None]:
    """ Функция для очищения папки с кастомными аватарками пользователя. Используется при обновлении аватарки. """

    path_to_avatar_dir = f"{MEDIA_ROOT}{CUSTOM_USER_AVATARS_DIR}/{user.pk}/"
    try:
        for file in os.listdir(BASE_DIR / path_to_avatar_dir):
            os.remove(os.path.join(BASE_DIR, path_to_avatar_dir, file))
    except FileNotFoundError:
        pass


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

    def save(self, commit=True):
        instance = super().save(commit=False)
        clean_custom_user_avatars_dir(instance.user)
        if commit:
            instance.save()
        return instance


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Имя пользователя должно быть 5<=длина имени<=25, " \
                                            "не может состоять только из чисел."
        self.fields['password1'].help_text = "Пароль должен быть 8<=длина пароля<=64, " \
                                             "быть не простым, состоять не только из чисел."
        self.fields["password2"].help_text = "Повторите пароль."
        self.fields["username"].label = "Имя пользователя"
        self.fields["password1"].label = "Пароль"
        self.fields["password2"].label = "Подтверждение пароля"

        for field, input_ in {"username": TextInput, "password1": PasswordInput, "password2": PasswordInput}.items():
            self.fields[field].widget = input_(attrs={
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


class ChangeSignatureForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ("signature",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["signature"].label = "Ваша подпись:"
        self.fields["signature"].widget = forms.TextInput(attrs={"placeholder": "Подпись"})
        self.fields["signature"].required = False

    def __call__(self, *args, **kwargs):
        return ChangeSignatureForm(*args, **kwargs)
