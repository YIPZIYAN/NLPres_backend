# Generated by Django 5.1.1 on 2024-10-29 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0002_alter_collaborator_unique_together'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='collaborator',
            table='collaborators',
        ),
    ]
