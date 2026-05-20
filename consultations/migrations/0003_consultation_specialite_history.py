import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0002_consultation_medical_ai_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="consultation",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
                verbose_name="modifie le",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="consultation",
            name="specialite_snapshot",
            field=models.CharField(
                blank=True,
                max_length=100,
                verbose_name="specialite formulaire",
            ),
        ),
        migrations.AddField(
            model_name="consultation",
            name="reponses_specialite",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="reponses specialisees",
            ),
        ),
        migrations.AlterModelOptions(
            name="consultation",
            options={
                "ordering": ["-updated_at", "-date"],
                "verbose_name": "consultation",
                "verbose_name_plural": "consultations",
            },
        ),
    ]
