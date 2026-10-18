from django.db import migrations


def create_other(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    Product = apps.get_model("inventory", "Product")
    if Product.objects.filter(category__isnull=True).exists():
        other, _ = Category.objects.get_or_create(name="Other")
        Product.objects.filter(category__isnull=True).update(category=other)


class Migration(migrations.Migration):

    dependencies = [("inventory", "0008_shop_fields")]

    operations = [migrations.RunPython(create_other, migrations.RunPython.noop)]
