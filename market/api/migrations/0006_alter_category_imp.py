# Generated by Django 4.0.5 on 2022-06-25 09:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_category_imp_alter_offer_imp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='imp',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.import'),
        ),
    ]
