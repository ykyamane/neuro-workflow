from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0002_flowproject_visibility"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE flow_projects
                    ADD COLUMN IF NOT EXISTS reference text NOT NULL DEFAULT '';
                    ALTER TABLE flow_projects
                    ALTER COLUMN reference DROP DEFAULT;
                    """,
                    reverse_sql="""
                    ALTER TABLE flow_projects
                    DROP COLUMN IF EXISTS reference;
                    """,
                ),
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE flow_projects
                    ADD COLUMN IF NOT EXISTS hpc_target varchar(32) NOT NULL DEFAULT '';
                    ALTER TABLE flow_projects
                    ALTER COLUMN hpc_target DROP DEFAULT;
                    """,
                    reverse_sql="""
                    ALTER TABLE flow_projects
                    DROP COLUMN IF EXISTS hpc_target;
                    """,
                ),
            ],
            state_operations=[
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
            ],
        ),
    ]
