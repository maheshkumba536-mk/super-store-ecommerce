from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0003_category_remove_cartitem_cart_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='click_count',
            field=models.PositiveIntegerField(default=0, help_text='Product link clicks'),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_link',
            field=models.URLField(blank=True, help_text='Product buying link (Amazon, Flipkart, etc.)', max_length=500, null=True),
        ),
    ]
