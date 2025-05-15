from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from masterclasses.models import MasterClass
from masterclasses.api.serializers import MasterClassSerializer

User = get_user_model()

class WishlistView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, id):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        user = get_object_or_404(User, id=id)
        if request.user.id != user.id:
            return Response(
                {'error': 'You can only view your own wishlist'},
                status=status.HTTP_403_FORBIDDEN
            )
        wishlist = user.profile.favorite_masterclasses.all()
        serializer = MasterClassSerializer(wishlist, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, id, product_id):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        user = get_object_or_404(User, id=id)
        if request.user.id != user.id:
            return Response(
                {'error': 'You can only modify your own wishlist'},
                status=status.HTTP_403_FORBIDDEN
            )
        masterclass = get_object_or_404(MasterClass, id=product_id)
        user.profile.favorite_masterclasses.add(masterclass)
        return Response({'message': 'Masterclass added to wishlist'})

    def delete(self, request, id, product_id):
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication credentials were not provided.'}, status=status.HTTP_401_UNAUTHORIZED)
        user = get_object_or_404(User, id=id)
        if request.user.id != user.id:
            return Response(
                {'error': 'You can only modify your own wishlist'},
                status=status.HTTP_403_FORBIDDEN
            )
        masterclass = get_object_or_404(MasterClass, id=product_id)
        user.profile.favorite_masterclasses.remove(masterclass)
        return Response({'message': 'Masterclass removed from wishlist'}) 