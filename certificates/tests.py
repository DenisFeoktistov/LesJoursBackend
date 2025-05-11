from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import Certificate
from .api.serializers import CertificateSerializer
from decimal import Decimal

User = get_user_model()

class CertificateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='certuser',
            email='certuser@example.com',
            password='testpass123'
        )
        self.certificate = Certificate.objects.create(
            user=self.user,
            amount=Decimal('1000'),
            code='ABC12345',
            is_used=False
        )

    def test_str(self):
        self.assertIn('Certificate', str(self.certificate))
        self.assertIn(self.certificate.code, str(self.certificate))

    def test_use_certificate(self):
        result = self.certificate.use_certificate()
        self.assertTrue(result)
        self.certificate.refresh_from_db()
        self.assertTrue(self.certificate.is_used)
        # Using again returns False
        result2 = self.certificate.use_certificate()
        self.assertFalse(result2)

class CertificateSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='certseruser',
            email='certseruser@example.com',
            password='testpass123'
        )

    def test_create_generates_code(self):
        data = {'amount': Decimal('1000.00'), 'is_used': False}
        serializer = CertificateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        cert = serializer.save(user=self.user)
        self.assertTrue(cert.code)
        self.assertEqual(len(cert.code), 8)

class CertificateAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='certapiuser',
            email='certapiuser@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.certificate = Certificate.objects.create(
            user=self.user,
            amount=Decimal('1000'),
            code='API12345',
            is_used=False
        )
        self.url = reverse('certificate-list')

    def test_list_certificates(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results'] if 'results' in response.data else response.data), 1)

    def test_create_certificate(self):
        response = self.client.post(self.url, {'amount': '2000.00'}, format='json')
        print('DEBUG RESPONSE:', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue('code' in response.data)

    def test_retrieve_certificate(self):
        url = reverse('certificate-detail', args=[self.certificate.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.certificate.id)

    def test_update_certificate(self):
        url = reverse('certificate-detail', args=[self.certificate.id])
        response = self.client.patch(url, {'amount': '3000.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.certificate.refresh_from_db()
        self.assertEqual(int(self.certificate.amount), 3000)

    def test_delete_certificate(self):
        url = reverse('certificate-detail', args=[self.certificate.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Certificate.objects.filter(id=self.certificate.id).exists())

    def test_use_action(self):
        url = reverse('certificate-use', args=[self.certificate.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.certificate.refresh_from_db()
        self.assertTrue(self.certificate.is_used)
        # Try using again
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response2.data)
