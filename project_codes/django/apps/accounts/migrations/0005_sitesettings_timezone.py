from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_sitesettings_contact_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="timezone",
            field=models.CharField(
                default="Europe/Vilnius",
                help_text="IANA timezone name, e.g. Europe/Vilnius",
                max_length=64,
            ),
        ),
    ]