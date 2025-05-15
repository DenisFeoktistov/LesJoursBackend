from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from masterclasses.models import MasterClass
from decimal import Decimal

User = get_user_model()

class WishlistAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test masterclass
        self.masterclass = MasterClass.objects.create(
            name='Test Masterclass',
            short_description='Test Description',
            start_price=Decimal('1000.00'),
            final_price=Decimal('1000.00'),
            bucket_link='test.jpg',
            age_restriction=18,
            duration=120
        )
        
        # Create another user
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

    def test_get_wishlist_authenticated(self):
        """Test getting wishlist for authenticated user"""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Initially empty

    def test_get_wishlist_unauthenticated(self):
        """Test getting wishlist for unauthenticated user"""
        url = reverse('wishlist', args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_other_user_wishlist(self):
        """Test getting another user's wishlist"""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist', args=[self.other_user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_to_wishlist(self):
        """Test adding masterclass to wishlist"""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', args=[self.user.id, self.masterclass.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify masterclass was added
        self.assertTrue(self.masterclass in self.user.profile.favorite_masterclasses.all())

    def test_remove_from_wishlist(self):
        """Test removing masterclass from wishlist"""
        # First add to wishlist
        self.user.profile.favorite_masterclasses.add(self.masterclass)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', args=[self.user.id, self.masterclass.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify masterclass was removed
        self.assertFalse(self.masterclass in self.user.profile.favorite_masterclasses.all())

    def test_add_to_wishlist_unauthenticated(self):
        """Test adding to wishlist while unauthenticated"""
        url = reverse('wishlist-item', args=[self.user.id, self.masterclass.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_from_wishlist_unauthenticated(self):
        """Test removing from wishlist while unauthenticated"""
        url = reverse('wishlist-item', args=[self.user.id, self.masterclass.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_to_other_user_wishlist(self):
        """Test adding to another user's wishlist"""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', args=[self.other_user.id, self.masterclass.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_remove_from_other_user_wishlist(self):
        """Test removing from another user's wishlist"""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', args=[self.other_user.id, self.masterclass.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_nonexistent_masterclass(self):
        """Test adding non-existent masterclass to wishlist"""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', args=[self.user.id, 99999])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_nonexistent_masterclass(self):
        """Test removing non-existent masterclass from wishlist"""
        self.client.force_authenticate(user=self.user)
        url = reverse('wishlist-item', args=[self.user.id, 99999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) 