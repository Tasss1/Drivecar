from rest_framework import serializers
from .models import Banner, BannerImage


class BannerImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BannerImage
        fields = ('id', 'image')


class BannerSerializer(serializers.ModelSerializer):
    images = BannerImageSerializer(many=True, read_only=True)

    class Meta:
        model = Banner
        fields = ('id', 'title', 'description', 'images')


class BannerCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        max_length=10
    )

    class Meta:
        model = Banner
        fields = ('title', 'description', 'images')

    def create(self, validated_data):
        images = validated_data.pop('images')
        banner = Banner.objects.create(**validated_data)
        for img in images:
            BannerImage.objects.create(banner=banner, image=img)
        return banner

