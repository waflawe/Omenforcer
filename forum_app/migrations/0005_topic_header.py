# Generated by Django 4.2.2 on 2023-12-06 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum_app', '0004_alter_topic_question_alter_topic_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='header',
            field=models.CharField(choices=[('GENERAL', 'Общий'), ('TEMPLATES', 'Шаблоны'), ('ORM', 'Django ORM'), ('TESTING', 'Тестирование'), ('DRF', 'DRF'), ('CELERY', 'Celery'), ('CHANNELS', 'Django Channels'), ('DEPLOY', 'Deploy')], default='GENERAL', max_length=30),
        ),
    ]
