from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import CertificateSerializer
from ..models import Certificate


class CertificateViewSet(viewsets.ModelViewSet):
    serializer_class = CertificateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Certificate.objects.none()
        return Certificate.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="List all certificates for the current user",
        responses={
            200: openapi.Response(
                description="List of certificates",
                schema=CertificateSerializer(many=True)
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new certificate",
        request_body=CertificateSerializer,
        responses={
            201: openapi.Response(
                description="Certificate created successfully",
                schema=CertificateSerializer
            ),
            400: "Bad Request"
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Get a specific certificate",
        responses={
            200: openapi.Response(
                description="Certificate details",
                schema=CertificateSerializer
            ),
            404: "Not Found"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a certificate",
        request_body=CertificateSerializer,
        responses={
            200: openapi.Response(
                description="Certificate updated successfully",
                schema=CertificateSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Partially update a certificate",
        request_body=CertificateSerializer,
        responses={
            200: openapi.Response(
                description="Certificate partially updated successfully",
                schema=CertificateSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a certificate",
        responses={
            204: "No Content",
            404: "Not Found"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Apply a certificate to an order",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['order_id'],
            properties={
                'order_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the order to apply the certificate to"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Certificate applied successfully",
                schema=CertificateSerializer
            ),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        certificate = self.get_object()
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response(
                {'error': 'order_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            if certificate.apply_to_order(order_id):
                serializer = self.get_serializer(certificate)
                return Response(serializer.data)
            return Response(
                {'error': 'Failed to apply certificate'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        certificate = self.get_object()
        if certificate.is_used:
            return Response(
                {'error': 'Certificate has already been used'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if certificate.use_certificate():
            return Response({'status': 'certificate used successfully'})
        return Response(
            {'error': 'Failed to use certificate'},
            status=status.HTTP_400_BAD_REQUEST
        ) 