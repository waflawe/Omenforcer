from django import forms
from django.core.validators import MaxLengthValidator, MinLengthValidator

from forum_app.models import Comment, Topic


class AddTopicForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["upload"].required = False
        self.fields["section"].required = False

    class Meta:
        model = Topic
        fields = ("title", "question", "upload", "section")

        labels = {
            "title": "Название",
            "question": "Вопрос",
            "section": "Раздел",
            "upload": "Вложение"
        }

        widgets = {
            "title": forms.TextInput(attrs={
                "style": "background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)",
                "class": "indent"
            }),
            "question": forms.Textarea(attrs={
                "style": "background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)",
                "rows": "10",
                "cols": "60",
                "class": "indent"
            }),
            "section": forms.Select(attrs={
                'style': 'width: 30%',
                "class": "form-select indent",
            }),
            "upload": forms.ClearableFileInput(attrs={
                'style': 'background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)',
                "class": "indent"
            })
        }

        validators = {
            "title": [MinLengthValidator(8), MaxLengthValidator(100)],
            "question": [MinLengthValidator(5), MaxLengthValidator(2048)]
        }


class AddCommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["upload"].required = False

    class Meta:
        model = Comment
        fields = ("comment", "upload")

        labels = {
            "comment": "Комментарий",
            "upload": "Вложение"
        }

        widgets = {
            "comment": forms.Textarea(attrs={
                "style": "background-color: rgb(20, 20, 20);"
                "color: rgb(204, 204, 204)",
                "rows": "10",
                "cols": "60"
            }),
            "upload": forms.ClearableFileInput(attrs={
                'style': 'background-color: rgb(20, 20, 20); color: rgb(204, 204, 204)'
            })
        }

        validators = {
            "comment": [MinLengthValidator(5), MaxLengthValidator(2048)]
        }
