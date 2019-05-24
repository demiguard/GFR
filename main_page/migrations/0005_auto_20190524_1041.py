# Generated by Django 2.1.5 on 2019-05-24 08:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_page', '0004_auto_20190306_1336'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('department_id', models.AutoField(primary_key=True, serialize=False)),
                ('thining_factor', models.FloatField(default=0.0, null=True)),
                ('department', models.CharField(default='', max_length=200, null=True)),
                ('hospital_Name', models.CharField(default='', max_length=200, null=True)),
                ('address', models.CharField(default='', max_length=200, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='user',
            name='config',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main_page.Config'),
        ),
        migrations.AlterField(
            model_name='user',
            name='hospital',
            field=models.CharField(choices=[('RH', 'Rigshospitalet'), ('HEH', 'Herlev hospital'), ('HI', 'Hillerød hospital'), ('FH', 'Frederiksberg hospital'), ('BH', 'Bispebjerg hospital'), ('GLO', 'Glostrup hospital'), ('HVH', 'Hvidovre hospital')], max_length=3),
        ),
    ]