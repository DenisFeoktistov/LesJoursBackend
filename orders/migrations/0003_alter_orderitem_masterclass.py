# Generated by Django 4.2.10 on 2025-05-18 11:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('masterclasses', '0007_masterclass_score_product_page'),
        ('orders', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderitem',
            name='masterclass',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='masterclasses.masterclass'),
        ),
    ]
