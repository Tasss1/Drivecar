from django.db import models

class Banner(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.title


class BannerImage(models.Model):
    banner = models.ForeignKey(
        Banner,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to='banners/')

