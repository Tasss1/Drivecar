from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Review
from .serializers import ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_serializer_context(self):
        return {'request': self.request}

    @swagger_auto_schema(
        operation_summary="Список всех отзывов",
        tags=['reviews']
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Оставить/обновить отзыв",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'text': openapi.Schema(type=openapi.TYPE_STRING, description='Текст отзыва (необязательно)', nullable=True),
                'rating': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, maximum=5),
            },
            required=['rating']
        ),
        responses={201: ReviewSerializer, 400: "Ошибки валидации"},
        tags=['reviews']
    )
    def create(self, request, *args, **kwargs):
        # create теперь использует валидацию из сериализатора
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()  # user уже подставлен в сериализаторе

    # update и partial_update (PUT/PATCH) будут работать автоматически
    def update(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user != request.user:
            return Response({'detail': 'Вы можете редактировать только свой отзыв.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        review = self.get_object()
        if review.user != request.user:
            return Response({'detail': 'Вы можете удалять только свой отзыв.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Получить свой отзыв",
        tags=['reviews']
    )
    @action(detail=False, methods=['get'], url_path='my')
    def my_review(self, request):
        try:
            review = Review.objects.get(user=request.user)
            serializer = self.get_serializer(review)
            return Response(serializer.data)
        except Review.DoesNotExist:
            return Response({'detail': 'Вы ещё не оставили отзыв.'}, status=status.HTTP_404_NOT_FOUND)
