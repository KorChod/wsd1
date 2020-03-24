import json

from celery import shared_task

from .util import download_images_from_url, scrape_images, scrape_text
from ..models import AsyncResults, WebPage


@shared_task(bind=True)
def download_text(self, url):
    """
    Asynchronous task handled with Celery to download and save HTML text content in the database.
    To hold current task status an AsyncResults instance is created and modified.
    :param url - website url as a string.
    """
    task_id = self.request.id
    task_status = AsyncResults.objects.create(
        task_id=task_id,
        result={"status_message": "Requesting url"})
    try:
        text = scrape_text(url, task_status)
    except Exception as e:
        result = {"status_code": 500,
                  "status_message": "Failed to download text",
                  "error_message": str(e)}
        task_status.result = result
        task_status.save()

    else:
        task_status.result = {"status_message": "Saving text in database"}
        task_status.save()
        WebPage.objects.update_or_create(url=url, defaults={"url": url, "text": text})

        result = {"status_code": 200,
                  "status_message": "Download complete"}
        task_status.result = result
        task_status.save()


@shared_task(bind=True)
def download_images(self, url):
    """
    Asynchronous task handled with Celery to download and save images from HTML content.
    To hold current task status an AsyncResults instance is created and modified.
    :param url - website url as a string.
    """
    task_id = self.request.id
    task_status = AsyncResults.objects.create(
        task_id=task_id,
        result={"status_message": "Requesting url"})
    try:
        images_urls = scrape_images(url, task_status)
    except Exception as e:
        result = {"status_code": 500,
                  "status_message": "Failed to download images",
                  "error_message": str(e)}

        task_status.result = result
        task_status.save()

    else:
        task_status.result = json.dumps({"status_message": "Downloading images"})
        task_status.save()
        webpage = WebPage.objects.get_or_create(url=url)[0]

        image_count = download_images_from_url(webpage, images_urls, task_status)

        task_status.result = {
            "status_code": 200,
            "status_message": "Download complete",
            "images_downloaded": image_count["download_success"],
            "images_failed_to_download": image_count["download_failure"]
        }
        task_status.save()
