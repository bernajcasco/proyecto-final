# Generated by Django 4.2.2 on 2023-07-14 10:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0006_alter_articulo_autor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='link',
            name='key',
        ),
    ]
