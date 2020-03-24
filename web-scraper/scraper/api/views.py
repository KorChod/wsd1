from django.shortcuts import get_object_or_404
from django.urls import reverse
from rest_framework import status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AsyncResultSerializer, WebPageSerializer
from .tasks import download_images, download_text
from ..models import AsyncResults, WebPage


class TextScrapeView(APIView):

    def post(self, request):
        url = request.data["url"]
        task = download_text.delay(url)
        response = {
            "url": url,
            "task_id": task.task_id,
            "task_url": request.build_absolute_uri(reverse("task-detail", args=[task.task_id])),
            "status_message": "download request received for processing"
        }
        return Response(response, status=status.HTTP_202_ACCEPTED)


class ImageScrapeView(APIView):

    def post(self, request):
        url = request.data["url"]
        task = download_images.delay(url)
        response = {
            "url": url,
            "task_id": task.task_id,
            "task_url": request.build_absolute_uri(reverse("task-detail", args=[task.task_id])),
            "status_message": "download request received for processing"
        }
        return Response(response, status=status.HTTP_202_ACCEPTED)


class WebPageListView(APIView, LimitOffsetPagination):
    page_size = 2

    def get_queryset(self, request):
        webpages = WebPage.objects.all()
        return self.paginate_queryset(webpages, self.request)

    def get(self, request):
        webpages = self.get_queryset(request=request)
        serializer = WebPageSerializer(webpages, context={"request": request}, many=True)

        return self.get_paginated_response(serializer.data)


class WebPageDetailView(APIView):

    def get(self, request, pk):
        webpage = get_object_or_404(WebPage, pk=pk)
        serializer = WebPageSerializer(webpage, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TaskStatusDetailView(APIView):

    def get(self, request, task_id):
        task = get_object_or_404(AsyncResults, task_id=task_id)
        serializer = AsyncResultSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)
