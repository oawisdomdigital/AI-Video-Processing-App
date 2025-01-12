# Generated by Django 5.1.4 on 2025-01-08 12:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('video_processing', '0002_alter_uploadedvideo_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedvideo',
            name='estimated_time_remaining',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='uploadedvideo',
            name='processing_progress',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='uploadedvideo',
            name='processing_status',
            field=models.CharField(choices=[('in_progress', 'In Progress'), ('completed', 'Completed'), ('failed', 'Failed')], default='in_progress', max_length=20),
        ),
    ]