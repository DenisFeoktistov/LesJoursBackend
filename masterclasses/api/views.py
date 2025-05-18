from rest_framework import viewsets, filters, permissions
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from ..models import MasterClass, Event
from .serializers import MasterClassSerializer, EventSerializer
from .filters import MasterClassFilter
from rest_framework import status


class MasterClassViewSet(viewsets.ModelViewSet):
    queryset = MasterClass.objects.all()
    serializer_class = MasterClassSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MasterClassFilter
    search_fields = ['name', 'short_description', 'long_description']
    ordering_fields = [
        'final_price',  # For price sorting
        'age_restriction',  # For age sorting
        'score_product_page',  # For popularity sorting
        'created_at',  # For sorting by creation date
        'name'  # Keep existing name sorting
    ]
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return MasterClass.objects.none()
        return super().get_queryset()

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(), slug=self.kwargs["slug"])
        self.check_object_permissions(self.request, obj)
        return obj

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
    def events(self, request, slug=None):
        masterclass = self.get_object()
        events = masterclass.events.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Toggle masterclass in wishlist",
        responses={
            200: openapi.Response(
                description="Masterclass wishlist status updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'in_wishlist': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        'message': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            401: "Unauthorized",
            404: "Not Found"
        }
    )
    @action(detail=True, methods=['post'])
    def toggle_wishlist(self, request, slug=None):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        masterclass = self.get_object()
        profile = request.user.profile

        if masterclass in profile.favorite_masterclasses.all():
            profile.favorite_masterclasses.remove(masterclass)
            message = 'Masterclass removed from wishlist'
            in_wishlist = False
        else:
            profile.favorite_masterclasses.add(masterclass)
            message = 'Masterclass added to wishlist'
            in_wishlist = True

        return Response({
            'in_wishlist': in_wishlist,
            'message': message
        })

    @swagger_auto_schema(
        operation_description="Get masterclasses by their IDs",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'products': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_STRING),
                    description="List of masterclass IDs"
                )
            },
            required=['products']
        ),
        responses={
            200: openapi.Response(
                description="List of masterclasses",
                schema=MasterClassSerializer(many=True)
            ),
            400: "Bad Request"
        }
    )
    @action(detail=False, methods=['post'])
    def list_masterclasses(self, request):
        product_ids = request.data.get('products', [])
        if not product_ids:
            return Response(
                {'error': 'No product IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        masterclasses = MasterClass.objects.filter(id__in=product_ids)
        serializer = self.get_serializer(masterclasses, many=True)
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