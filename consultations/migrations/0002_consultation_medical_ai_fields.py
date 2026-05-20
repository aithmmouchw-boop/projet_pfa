from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("consultations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="consultation",
            name="symptomes",
            field=models.TextField(blank=True, verbose_name="symptomes"),
        ),
        migrations.AddField(
            model_name="consultation",
            name="maladies_chroniques",
            field=models.TextField(blank=True, verbose_name="maladies chroniques"),
        ),
        migrations.AddField(
            model_name="consultation",
            name="traitement",
            field=models.TextField(blank=True, verbose_name="traitement"),
        ),
        migrations.AddField(
            model_name="consultation",
            name="risk_score",
            field=models.PositiveSmallIntegerField(default=0, verbose_name="score de risque IA"),
        ),
        migrations.AddField(
            model_name="consultation",
            name="risk_level",
            field=models.CharField(
                choices=[
                    ("faible", "Faible risque"),
                    ("moyen", "Risque moyen"),
                    ("eleve", "Risque eleve"),
                ],
                default="faible",
                max_length=20,
                verbose_name="niveau de risque",
            ),
        ),
        migrations.AddField(
            model_name="consultation",
            name="risk_analyzed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="analyse IA le"),
        ),
    ]
