# Generated by Django 3.0.4 on 2021-09-29 20:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Genre',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField()),
                ('is_approved', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Paint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('paint', models.ImageField(upload_to='paints')),
                ('is_approved', models.BooleanField(default=False)),
                ('genre', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='paints', to='NeuralPainter.Genre')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Painter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('photo', models.ImageField(upload_to='painter_photos')),
                ('biography', models.TextField()),
                ('death_date', models.DateField()),
                ('birth_date', models.DateField()),
                ('is_approved', models.BooleanField(default=False)),
                ('genres', models.ManyToManyField(blank=True, related_name='painters', to='NeuralPainter.Genre')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('photo', models.ImageField(upload_to='user_photos')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StylizedPhoto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stylized_photo', models.ImageField(null=True, upload_to='stylized_photo')),
                ('is_stylized', models.BooleanField(default=False)),
                ('based_photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stylized_version', to='NeuralPainter.Photo')),
                ('paint', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='NeuralPainter.Paint')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('avatar', models.ImageField(null=True, upload_to='avatars')),
                ('verified', models.BooleanField(default=False)),
                ('favorite_painters', models.ManyToManyField(blank=True, to='NeuralPainter.Painter')),
                ('favorite_paints', models.ManyToManyField(blank=True, to='NeuralPainter.Paint')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='photo',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='NeuralPainter.Profile'),
        ),
        migrations.AddField(
            model_name='paint',
            name='painter',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='paints', to='NeuralPainter.Painter'),
        ),
    ]
