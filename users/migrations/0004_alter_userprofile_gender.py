from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_userprofile_is_mailing_list_userprofile_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(max_length=6, choices=[('male', 'Male'), ('female', 'Female')]),
        ),
    ] 