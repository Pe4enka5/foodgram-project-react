from rest_framework import status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404


class CreateDeleteModelMixin:
    """Миксин с методами создания и удаления объектов."""
    @staticmethod
    def create_obj(data, request, serializer_name):
        serializer = serializer_name(
            data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_obj(model_name, **kwargs):
        obj = get_object_or_404(model_name, **kwargs)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
