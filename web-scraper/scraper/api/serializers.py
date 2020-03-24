from ..models import AsyncResults, Image, WebPage
from rest_framework import serializers


class ImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ["image_url"]

    def get_image_url(self, image):
        request = self.context.get("request")
        image_url = image.image.url
        return request.build_absolute_uri(image_url)


class WebPageSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, required=False)

    class Meta:
        model = WebPage
        fields = ["id", "url", "text", "images"]


class AsyncResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsyncResults
        fields = "__all__"
