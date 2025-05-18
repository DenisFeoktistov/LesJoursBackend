from django.db import migrations

def update_gender_values(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    for profile in UserProfile.objects.all():
        if profile.gender == 'M':
            profile.gender = 'male'
        elif profile.gender == 'F':
            profile.gender = 'female'
        profile.save()

def reverse_gender_values(apps, schema_editor):
    UserProfile = apps.get_model('users', 'UserProfile')
    for profile in UserProfile.objects.all():
        if profile.gender == 'male':
            profile.gender = 'M'
        elif profile.gender == 'female':
            profile.gender = 'F'
        profile.save()

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0004_alter_userprofile_gender'),
    ]

    operations = [
        migrations.RunPython(update_gender_values, reverse_gender_values),
    ] 