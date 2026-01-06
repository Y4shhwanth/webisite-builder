# Generated migration for adding design context fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='websiteproject',
            name='design_context',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='websiteproject',
            name='template_id',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
