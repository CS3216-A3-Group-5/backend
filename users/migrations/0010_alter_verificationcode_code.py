# Generated by Django 4.1.1 on 2022-09-21 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_merge_20220921_1935'),
    ]

    operations = [
        migrations.AlterField(
            model_name='verificationcode',
            name='code',
            field=models.CharField(max_length=6),
        ),
    ]