# Generated by Django 5.0.3 on 2024-03-20 12:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0006_alter_products_quantity"),
    ]

    operations = [
        migrations.AddField(
            model_name="products",
            name="cropped_image_paths",
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]