# Generated by Django 4.2.10 on 2025-05-15 22:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('masterclasses', '0007_masterclass_score_product_page'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_seen_masterclasses',
            field=models.ManyToManyField(blank=True, related_name='last_seen_by', to='masterclasses.masterclass'),
        ),
    ]
