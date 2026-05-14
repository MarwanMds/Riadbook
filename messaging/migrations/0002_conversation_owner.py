import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        # Add owner FK to Conversation
        migrations.AddField(
            model_name="conversation",
            name="owner",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="owner_conversations",
                limit_choices_to={"role": "owner"},
                to=settings.AUTH_USER_MODEL,
                help_text="Owner of the property — auto-set when a property is selected",
            ),
        ),
        # Add unread counter for owner
        migrations.AddField(
            model_name="conversation",
            name="unread_by_owner",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        # Add OWNER sender type to Message
        migrations.AlterField(
            model_name="message",
            name="sender_type",
            field=models.CharField(
                max_length=10,
                choices=[
                    ("traveler", "Voyageur"),
                    ("admin",    "Administrateur"),
                    ("owner",    "Hôtelier"),
                ],
            ),
        ),
    ]