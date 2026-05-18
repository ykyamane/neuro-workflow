# Generated during production/GitHub merge on 2026-05-18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0002_flowproject_visibility"),
    ]

    operations = [
        migrations.AddField(
            model_name="flowproject",
            name="reference",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="flowproject",
            name="hpc_target",
            field=models.CharField(
                blank=True,
                choices=[("riken", "Riken"), ("fugaku", "Fugaku")],
                default="",
                max_length=32,
            ),
        ),
    ]
