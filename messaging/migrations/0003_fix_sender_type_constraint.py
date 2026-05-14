from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("messaging", "0002_conversation_owner"),
    ]

    operations = [
        # 1. Drop the old CHECK constraint that only allows traveler/admin
        migrations.RunSQL(
            sql="""
                ALTER TABLE messages
                DROP CONSTRAINT IF EXISTS messages_sender_type_check;
            """,
            reverse_sql="""
                ALTER TABLE messages
                ADD CONSTRAINT messages_sender_type_check
                CHECK (sender_type IN ('traveler', 'admin'));
            """,
        ),

        # 2. Add the new CHECK constraint that also allows owner
        migrations.RunSQL(
            sql="""
                ALTER TABLE messages
                ADD CONSTRAINT messages_sender_type_check
                CHECK (sender_type IN ('traveler', 'admin', 'owner'));
            """,
            reverse_sql="""
                ALTER TABLE messages
                DROP CONSTRAINT IF EXISTS messages_sender_type_check;
            """,
        ),
    ]
