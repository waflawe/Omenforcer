from typing import Type, Union

from django import forms
from django.db import models
from rest_framework import serializers

Instance = models.Model
ValidationClass = Union[Type[serializers.ModelSerializer] | Type[forms.ModelForm]]
E = int
ErrorMessage = str
