from django.db import models
from jsonfield import JSONField


class WebPage(models.Model):
    url = models.CharField(max_length=2083, unique=True)
    text = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Web Page"
        verbose_name_plural = "Web Pages"

    def __str__(self):
        return self.url


def upload_location(instance, filename):
    return f"{instance.webpage.id}/{filename}"


class Image(models.Model):
    image = models.ImageField(upload_to=upload_location)
    webpage = models.ForeignKey("WebPage", on_delete=models.CASCADE, related_name="images", null=False, blank=False)

    def __str__(self):
        return self.image.name


class AsyncResults(models.Model):
    task_id = models.CharField(
        blank=False,
        max_length=255,
        null=False,
        verbose_name="task_id",
        db_index=True)

    result = JSONField(default=dict, verbose_name="task_result")

    def __str__(self):
        return self.task_id
