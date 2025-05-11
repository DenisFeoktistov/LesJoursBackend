from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import MasterClass, Event
from .serializers import MasterClassSerializer, EventSerializer


class MasterClassViewSet(viewsets.ModelViewSet):
    queryset = MasterClass.objects.all()
    serializer_class = MasterClassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['start_price', 'final_price', 'age_restriction', 'duration']
    search_fields = ['title', 'description']
    ordering_fields = ['start_price', 'final_price', 'created_at', 'title']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MasterClass.objects.none()
        return super().get_queryset()

    @swagger_auto_schema(
        operation_description="List all masterclasses",
        responses={
            200: openapi.Response(
                description="List of masterclasses",
                schema=MasterClassSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new masterclass",
        request_body=MasterClassSerializer,
        responses={
            201: openapi.Response(
                description="Masterclass created successfully",
                schema=MasterClassSerializer
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get a specific masterclass",
        responses={
            200: openapi.Response(
                description="Masterclass details",
                schema=MasterClassSerializer
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a masterclass",
        request_body=MasterClassSerializer,
        responses={
            200: openapi.Response(
                description="Masterclass updated successfully",
                schema=MasterClassSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a masterclass",
        request_body=MasterClassSerializer,
        responses={
            200: openapi.Response(
                description="Masterclass partially updated successfully",
                schema=MasterClassSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a masterclass",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="List all events for a masterclass",
        responses={
            200: openapi.Response(
                description="List of events",
                schema=EventSerializer(many=True)
            ),
            404: "Not Found"
        }
    )
    @action(detail=True, methods=['get'])
    def events(self, request, pk=None):
        masterclass = self.get_object()
        events = masterclass.events.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['masterclass', 'start_datetime', 'end_datetime', 'available_seats']
    ordering_fields = ['start_datetime', 'end_datetime', 'available_seats']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Event.objects.none()
        return super().get_queryset()

    @swagger_auto_schema(
        operation_description="List all events",
        responses={
            200: openapi.Response(
                description="List of events",
                schema=EventSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new event",
        request_body=EventSerializer,
        responses={
            201: openapi.Response(
                description="Event created successfully",
                schema=EventSerializer
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Get a specific event",
        responses={
            200: openapi.Response(
                description="Event details",
                schema=EventSerializer
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update an event",
        request_body=EventSerializer,
        responses={
            200: openapi.Response(
                description="Event updated successfully",
                schema=EventSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update an event",
        request_body=EventSerializer,
        responses={
            200: openapi.Response(
                description="Event partially updated successfully",
                schema=EventSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete an event",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs) 