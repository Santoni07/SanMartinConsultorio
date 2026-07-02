from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("caja", "0010_alter_conceptofacturacion_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="conceptofacturacion",
            name="importe_particular",
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                default=0,
                verbose_name="Importe Particular",
            ),
        ),
    ]