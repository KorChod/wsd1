from tempfile import NamedTemporaryFile

import requests
from bs4 import BeautifulSoup
from django.core.files import File

from ..models import Image


def scrape_text(url, status_object):
    """
    Function used to retrieve text from an HTML content and remove all the tags.
    :param url: website's url as a string,
    :param status_object: an AsyncResult instance which holds current task state,
    :return: website's text as a string.
    """
    results = requests.get(url)
    if results.status_code != 200:
        raise ConnectionError

    status_object.result = {"status_message": "Processing HTML file"}
    status_object.save()
    soup = BeautifulSoup(results.content, 'lxml')

    for not_allowed_tag in soup(["script", "style"]):
        not_allowed_tag.decompose()

    return soup.text


def scrape_images(url, status_object):
    """
    Function used to retrieve images' urls from a website.
    :param url: website's url as a string,
    :param status_object: an AsyncResult instance which holds current task state,
    :return: list of urls as strings.
    """
    results = requests.get(url)

    if results.status_code != 200:
        raise ConnectionError

    status_object.result = {"status_message": "Processing HTML file"}
    status_object.save()
    soup = BeautifulSoup(results.content, 'lxml')

    images = soup.find_all('img')

    images_urls = []

    for image in images:
        if image.get('src') or image.get('data-original'):
            url = image.get('src') if image.get('src') else image.get('data-original')
            if not url.startswith("http"):
                url = "https:" + url
            images_urls.append(url)
    return images_urls


def download_images_from_url(webpage, images_urls, status_object):
    """

    :param webpage: instance of WebPage class,
    :param images_urls: list of urls as strings,
    :param status_object: an AsyncResult instance which holds current task state,
    :return: dictionary holding counts of successful and failed image downloads.
    """
    result = {"download_success": 0, "download_failure": 0}
    images_number = len(images_urls)
    current_number = 1
    for url in images_urls:
        status_object.result = {"status_message": f"Downloaded {current_number} / {images_number} images"}
        status_object.save()
        current_number += 1

        file_name = url.split('/')[-1]
        try:
            response = requests.get(url, stream=True)
        except requests.exceptions.InvalidURL:
            result["download_failure"] += 1
            continue
        else:
            temp_file = write_image(response)

            image = Image(webpage=webpage)
            image.image.save(file_name, File(temp_file))
            image.save()
            result["download_success"] += 1
    return result


def write_image(response):
    """
    Function to save response data into a temporary file.
    :param response: response from image resource url,
    :return: temporary image file to be saved as an Image instance.
    """
    temp_file = NamedTemporaryFile(delete=True)

    for block in response.iter_content(1024 * 8):
        if not block:
            break
        temp_file.write(block)
    return temp_file
