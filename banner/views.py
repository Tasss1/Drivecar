from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Banner
from .serializers import BannerSerializer, BannerCreateSerializer


class BannerViewSet(ModelViewSet):
    queryset = Banner.objects.prefetch_related('images')
    parser_classes = (MultiPartParser, FormParser)

    def get_serializer_class(self):
        if getattr(self, 'swagger_fake_view', False):
            return BannerSerializer
        if self.action == 'create':
            return BannerCreateSerializer
        return BannerSerializer

    @swagger_auto_schema(
        operation_description="Create banner with up to 10 images",
        manual_parameters=[
            openapi.Parameter(
                'title',
                openapi.IN_FORM,
                description='Title',
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'description',
                openapi.IN_FORM,
                description='Description',
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'images',
                openapi.IN_FORM,
                description='Images (max 10)',
                type=openapi.TYPE_FILE,
                required=True
            ),
        ],
        responses={201: BannerSerializer}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

