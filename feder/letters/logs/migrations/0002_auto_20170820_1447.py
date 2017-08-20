# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-20 14:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emaillog',
            name='status',
            field=models.CharField(choices=[(b'open', 'Open'), (b'ok', 'Open'), (b'spambounce', 'Open'), (b'softbounce', 'Open'), (b'hardbounce', 'Open'), (b'dropped', 'Open'), (b'deferred', 'Deferred'), (b'unknown', 'Unknown')], default=b'unknown', max_length=20),
        ),
        migrations.AddField(
            model_name='emaillog',
            name='to',
            field=models.CharField(default='', max_length=255, verbose_name='To'),
            preserve_default=False,
        ),
    ]
