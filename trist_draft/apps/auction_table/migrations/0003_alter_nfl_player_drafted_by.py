# Generated by Django 3.2.11 on 2022-07-05 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auction_table', '0002_auction_manager_auction_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nfl_player',
            name='drafted_by',
            field=models.CharField(default='Undrafted', max_length=50),
        ),
    ]
