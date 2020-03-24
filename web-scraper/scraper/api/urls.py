from django.urls import path

from .views import TaskStatusDetailView, ImageScrapeView, TextScrapeView, WebPageDetailView, WebPageListView

urlpatterns = [
    path("scrape/text/", TextScrapeView.as_view(), name="scrape-text"),

    path("scrape/images/", ImageScrapeView.as_view(), name="scrape-images"),

    path("webpages/", WebPageListView.as_view(), name="webpage-list"),

    path("webpages/<int:pk>/", WebPageDetailView.as_view(), name="webpage-detail"),

    path("task/<str:task_id>/", TaskStatusDetailView.as_view(), name="task-detail"),

]
