# Generated by Django 5.0.3 on 2024-03-21 04:35

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0007_products_cropped_image_paths"),
    ]

    operations = [
        migrations.AlterField(
            model_name="products",
            name="orginal_price",
            field=models.IntegerField(),
        ),
    ]
