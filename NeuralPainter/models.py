import logging

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.core.files import File
from django.utils.text import slugify

from NeuralPainter.utils import NoPhotoException
from NeuralPainter.style_transferring import stylize_image

logger = logging.getLogger('django')


class SluggedModel(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(SluggedModel, self).save(*args, **kwargs)


class Genre(SluggedModel):
    class Meta:
        ordering = ['name']
    description = models.TextField()
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return 'Genre {}'.format(self.name)


class Painter(SluggedModel):
    class Meta:
        ordering = ['name']
    photo = models.ImageField(upload_to='painter_photos')
    biography = models.TextField()
    genres = models.ManyToManyField(Genre, blank=True, related_name='painters')
    death_date = models.DateField()
    birth_date = models.DateField()
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return 'Painter {}'.format(self.name)


class Paint(SluggedModel):
    class Meta:
        ordering = ['name']

    paint = models.ImageField(upload_to='paints')
    painter = models.ForeignKey(Painter, on_delete=models.CASCADE, related_name='paints')
    genre = models.ForeignKey(Genre, null=True, on_delete=models.SET_NULL, blank=True, related_name='paints')
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return 'Paint {}'.format(self.name)


class Photo(SluggedModel):
    class Meta:
        ordering = ['name']

    user = models.ForeignKey(
        'Profile',
        related_name='photos',
        on_delete=models.CASCADE
    )
    photo = models.ImageField(
        upload_to='user_photos'
    )

    def __str__(self):
        return 'Photo {}'.format(self.name, )


class StylizedPhoto(models.Model):
    based_photo = models.ForeignKey(
        'Photo',
        related_name='stylized_version',
        on_delete=models.CASCADE
    )
    stylized_photo = models.ImageField(
        null=True,
        upload_to='stylized_photo',
        default="stylized_photo/image_in_processing.png"
    )
    paint = models.ForeignKey('Paint', null=True, on_delete=models.SET_NULL)
    is_stylized = models.BooleanField(default=False)

    def __str__(self):
        return 'Stylized {} by {}'.format(self.based_photo.name, self.paint.name)

    def schedule_photo_stylization(self):
        logger.info('Stylizing image')

        stylize_image(
            self.based_photo.photo.path,
            self.paint.paint.path,
            self.pk
        )

    def save_photo_stylization(self, stylized_photo_io):
        image_name = f"{self.based_photo.name}_{self.paint.name}_{self.pk}.jpeg"
        self.stylized_photo.save(
            image_name,
            File(stylized_photo_io)
        )


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(null=True, upload_to='avatars')
    favorite_painters = models.ManyToManyField('Painter', blank=True)
    favorite_paints = models.ManyToManyField('Paint', blank=True)

    verified = models.BooleanField(default=False)

    def add_to_favorite_paint(self, paint_id):
        paint = Paint.objects.get(pk=paint_id)
        self.favorite_paints.add(paint)
        self.save()
        logger.info('Paint added to favorite')

    def remove_from_favorite_paint(self, paint_id):
        paint = Paint.objects.get(pk=paint_id)
        self.favorite_paints.remove(paint)
        self.save()
        logger.info('Paint removed from favorite')

    def add_to_favorite_painter(self, painter_id):
        painter = Painter.objects.get(pk=painter_id)
        self.favorite_painters.add(painter)
        self.save()
        logger.info('Painter added to favorite')

    def remove_from_favorite_painter(self, painter_id):
        painter = Painter.objects.get(pk=painter_id)
        self.favorite_painters.remove(painter)
        self.save()
        logger.info('Painter removed from favorite')

    def delete_stylized_photo(self, stylized_photo_id):
        stylized_photo = StylizedPhoto.objects.get(pk=stylized_photo_id)

        if not self.photos.filter(stylized_version=stylized_photo).exists():
            logger.error('Stylized photo not found')
            raise NoPhotoException
        else:
            stylized_photo.delete()
            logger.info('Stylized photo deleted')

    def delete_photo(self, photo_id):
        photo = Photo.objects.get(pk=photo_id)

        if not self.photos.filter(pk=photo_id).exists():
            logger.error('Photo not found')
            raise NoPhotoException
        else:
            photo.delete()
            logger.info('Photo deleted')

    def __str__(self):
        return 'User {} {}'.format(self.user.first_name, self.user.last_name)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        logger.info('Profile created')


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
    logger.info('Profile saved')

