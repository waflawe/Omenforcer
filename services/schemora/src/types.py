from django import forms
from rest_framework import serializers
from django.db import models

from typing import Union, Type

Instance = models.Model
ValidationClass = Union[Type[serializers.ModelSerializer] | Type[forms.ModelForm]]
E = int
ErrorMessage = str
