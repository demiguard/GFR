# Generated by Django 2.2.2 on 2019-07-12 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0002_hospital_short_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hospital',
            name='short_name',
            field=models.CharField(max_length=8, null=True),
        ),
    ]
