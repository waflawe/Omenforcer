# Generated by Django 4.2.2 on 2023-12-02 20:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum_app', '0003_alter_comments_comment_alter_topic_author_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='question',
            field=models.TextField(max_length=2048, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(32)]),
        ),
        migrations.AlterField(
            model_name='topic',
            name='title',
            field=models.CharField(max_length=100, null=True, unique=True, validators=[django.core.validators.MinLengthValidator(5)]),
        ),
    ]
