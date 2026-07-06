from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0005_accounttype_alter_account_account_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="account",
            name="_old_type",
        ),
        migrations.AlterField(
            model_name="account",
            name="account_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="accounts",
                to="finance.accounttype",
                verbose_name="账户类型",
            ),
        ),
    ]
