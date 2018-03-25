# Generated by Django 2.0.3 on 2018-03-25 22:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('letters', '0020_remove_letter_way'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='attachment',
            field=models.FileField(upload_to='letters/%Y/%m/%d', verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='letter',
            name='eml',
            field=models.FileField(blank=True, null=True, upload_to='messages/%Y/%m/%d', verbose_name='File'),
        ),
        migrations.AlterField(
            model_name='letter',
            name='mark_spam_by',
            field=models.ForeignKey(blank=True, help_text='The person who marked it as spam', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='letter_mark_spam_by', to=settings.AUTH_USER_MODEL, verbose_name='Spam marker'),
        ),
    ]
