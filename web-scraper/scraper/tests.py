import os
import shutil
from unittest.mock import patch

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from requests.exceptions import InvalidURL
from rest_framework.test import APITestCase

from .api.util import download_images_from_url, scrape_images, scrape_text
from .models import AsyncResults, Image, WebPage


class UtilFunctionsTestCase(APITestCase):
    """Test case class for testing all functions in api/util file"""

    def setUp(self):
        """Defining variables and instances created before each test"""
        # Create url variable
        self.url = 'http://test-url.pl'
        # Read HTML test file
        with open("templates/test1.html") as f:
            self.html_content = f.read()

        # Create new webpage instance we will use for tests
        self.webpage = WebPage.objects.create(url=self.url)

        # Create new instance of object which holds current task status
        self.async_task = AsyncResults.objects.create(task_id="test-123")

    def tearDown(self):
        """Code executed after each test"""
        # Remove images from media folder created during tests
        page_media_directory = f"media/{self.webpage.id}"
        if os.path.exists(page_media_directory):
            shutil.rmtree(page_media_directory)

    @patch('scraper.api.util.requests.get')
    def test_scrape_text(self, mocked_get):
        """
        Testing that scrape_text function:
        1) returns only text from HTML file without tags,
        2) raises ConnectionError if response's status code is 500.
        Requests.get is mocked to return our predefined HTML file and status_code we need for a particular case.
        """
        # 1st case
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = self.html_content

        text = scrape_text(self.url, self.async_task)

        expected = '\n\n\nTest File\n\n\n\n\n\nThis is a simple HTML test file.\n\nWe scrape it for text and ' \
                   'images\n\n\n\nRemoving all the tags\nscript and style tags are decomposed\n\n'

        self.assertEqual(text, expected)

        # 2nd case
        mocked_get.return_value.status_code = 500
        self.assertRaises(ConnectionError, scrape_text, self.url, self.async_task)

    @patch('scraper.api.util.requests.get')
    def test_scrape_images(self, mocked_get):
        """
        Testing that scrape_images function:
        1) returns a list of all images' sources from the <img> tags in a predefined HTML file,
        2) raises ConnectionError if response's status code is 500.
        Requests.get is mocked to return our predefined HTML file and status_code we need for a particular case.
        """
        # 1st case
        mocked_get.return_value.status_code = 200
        mocked_get.return_value.content = self.html_content

        images = scrape_images(self.url, self.async_task)

        expected = ['http://test-url.pl/test-image.jpg', 'http://test-url.pl/test-image2.jpg']
        self.assertEqual(images, expected)

        # 2nd case
        mocked_get.return_value.status_code = 500
        self.assertRaises(ConnectionError, scrape_images, self.url, self.async_task)

    @patch('scraper.api.util.requests.get')
    @patch('scraper.api.util.write_image')
    def test_download_images_from_url(self, write_image, mocked_get):
        """
        Testing that download_images_from_url function:
        1) properly saved images on the hard disk,
        2) returns correct count of images that got successfully downloaded,
        3) returns correct count of images that failed to download due to InvalidUrl exception
        Mocked requests.get to let the code execute without raising exceptions.
        Mocked write_image function from util file to return a SimpleUploadedFile to imitate a real file.
        """
        # 1st case
        mocked_get.return_value = True
        write_image.return_value = SimpleUploadedFile("test-image.jpg", b"file_content",
                                                      content_type="image/jpeg")
        images_urls = ['http://test-url.pl/test-image.jpg', 'http://test-url.pl/test-image2.jpg']
        result = download_images_from_url(self.webpage, images_urls, self.async_task)

        saved_images = self.webpage.images.all()
        self.assertEqual(saved_images[0].image.name, f"{self.webpage.id}/test-image.jpg")
        self.assertEqual(saved_images[1].image.name, f"{self.webpage.id}/test-image2.jpg")

        # 2nd case
        self.assertEqual(result["download_success"], 2)
        self.assertEqual(result["download_failure"], 0)

        # 3rd case
        mocked_get.side_effect = InvalidURL
        result = download_images_from_url(self.webpage, images_urls, self.async_task)
        self.assertEqual(result["download_success"], 0)
        self.assertEqual(result["download_failure"], 2)


class TextScrapeViewTestCase(APITestCase):
    """Test case class to test api endpoints in TextScrapeView class"""
    def setUp(self):
        """Defining variables and instances created before each test"""
        # Create url variable
        self.url = 'http://test-url.pl'

    @patch('scraper.api.views.download_text')
    def test_post(self, download_text):
        """
        Testing that post method:
        1) returns correct response,
        2) returns correct status code.
        Mocked download_text function from api/tasks.py to return our predefined task_id.
        """
        # 1st case
        task_id = 'test-1234'
        download_text.delay.return_value.task_id = task_id
        response = self.client.post(reverse('scrape-text'), data={'url': self.url})

        expected = {
            'url': self.url,
            'task_id': task_id,
            'task_url': f'http://testserver/api/task/{task_id}/',
            'status_message': 'download request received for processing'
        }

        self.assertEqual(response.data, expected)

        # 2nd case
        self.assertEqual(response.status_code, 202)


class ImageScrapeViewTestCase(APITestCase):
    """Test case class to test api endpoints in ImageScrapeView class"""
    def setUp(self):
        """Defining variables and instances created before each test"""
        # Create url variable
        self.url = 'http://test-url.pl'

    @patch('scraper.api.views.download_images')
    def test_post(self, download_text):
        """
        Testing that post method:
        1) returns correct response,
        2) returns correct status code.
        Mocked download_text function from api/tasks.py to return our predefined task_id.
        """
        # 1st case
        task_id = 'test-1234'
        download_text.delay.return_value.task_id = task_id
        response = self.client.post(reverse('scrape-images'), data={'url': self.url})

        expected = {
            'url': self.url,
            'task_id': task_id,
            'task_url': f'http://testserver/api/task/{task_id}/',
            'status_message': 'download request received for processing'
        }

        self.assertEqual(response.data, expected)

        # 2nd case
        self.assertEqual(response.status_code, 202)


class WebPageDetailViewTestCase(APITestCase):
    """Test case class to test api endpoints in WebPageDetailView class"""
    def setUp(self):
        """Defining variables and instances created before each test"""
        # Create webpage instance in our database
        self.webpage = WebPage.objects.create(
            url='http://test-url.pl',
            text='\n\n\nTest File\n\n\n\n\n\nThis is a simple HTML test file.\n\nWe scrape it for text and ' \
                 'images\n\n\n\nRemoving all the tags\nscript and style tags are decomposed\n\n'
        )

        # Create image instance in our database
        image1 = open('static/python.jpg', 'rb')

        img = Image(webpage=self.webpage)
        img.image.save("python.jpg", File(image1), save=True)

    def tearDown(self):
        """Code executed after each test"""
        # Remove images from media folder created during tests
        page_media_directory = f"media/{self.webpage.id}"
        if os.path.exists(page_media_directory):
            shutil.rmtree(page_media_directory)

    def test_get(self):
        """
        Testing that get method:
        1) returns correct data from database,
        2) responses with 404 status code if couldn't find resource with specified id.
        """
        # 1st case
        response = self.client.get(reverse('webpage-detail', kwargs={'pk': self.webpage.id}))

        expected = {
            'id': 1,
            'url': self.webpage.url,
            'text': self.webpage.text,
            'images': [{'image_url': 'http://testserver/media/1/python.jpg'}]
        }

        self.assertEqual(response.data, expected)

        # 2nd case
        response = self.client.get(reverse('webpage-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, 404)


class TaskStatusDetailViewTestCase(APITestCase):
    """Test case class to test api endpoints in TaskStatusDetailView class"""

    def setUp(self):
        """Defining variables and instances created before each test"""
        self.async_task_result = AsyncResults.objects.create(
            task_id='test-1234',
            result={"status_code": 200, "status_message": "Download complete"})

    def test_get(self):
        """
        Testing that get method:
        1) returns correct data from database,
        2) responses with 404 status code if couldn't find resource with specified id.
        """
        # 1st case
        response = self.client.get(reverse('task-detail', kwargs={'task_id': 'test-1234'}))

        expected = {
            'id': 1,
            'task_id': self.async_task_result.task_id,
            'result': self.async_task_result.result
        }

        self.assertEqual(response.data, expected)

        # 2nd case
        response = self.client.get(reverse('task-detail', kwargs={'task_id': 'non-existing-task'}))
        self.assertEqual(response.status_code, 404)
