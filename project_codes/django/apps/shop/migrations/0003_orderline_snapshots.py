from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0002_add_contactmessage"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderline",
            name="barcode_snapshot",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="orderline",
            name="expiration_date_snapshot",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="orderline",
            name="sales_description_snapshot",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
