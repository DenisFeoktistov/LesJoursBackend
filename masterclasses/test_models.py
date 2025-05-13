from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import MasterClass, Event


class MasterClassModelTest(TestCase):
    def setUp(self):
        self.masterclass_data = {
            'name': 'Test Masterclass',
            'short_description': 'Test Description',
            'start_price': 100.00,
            'final_price': 90.00,
            'bucket_link': ['image1.jpg', 'image2.jpg'],
            'age_restriction': 18,
            'duration': 120
        }
        self.masterclass = MasterClass.objects.create(**self.masterclass_data)

    def test_masterclass_creation(self):
        self.assertEqual(self.masterclass.name, 'Test Masterclass')
        self.assertEqual(self.masterclass.slug, 'test-masterclass')
        self.assertEqual(self.masterclass.short_description, 'Test Description')
        self.assertEqual(self.masterclass.start_price, 100.00)
        self.assertEqual(self.masterclass.final_price, 90.00)
        self.assertEqual(self.masterclass.bucket_link, ['image1.jpg', 'image2.jpg'])
        self.assertEqual(self.masterclass.age_restriction, 18)
        self.assertEqual(self.masterclass.duration, 120)

    def test_masterclass_str(self):
        self.assertEqual(str(self.masterclass), 'Test Masterclass')

    def test_masterclass_slug_auto_generation(self):
        masterclass2 = MasterClass.objects.create(
            name='Another Test Masterclass',
            short_description='Another Description',
            start_price=200.00,
            final_price=180.00
        )
        self.assertEqual(masterclass2.slug, 'another-test-masterclass')


class EventModelTest(TestCase):
    def setUp(self):
        self.masterclass = MasterClass.objects.create(
            name='Test Masterclass',
            short_description='Test Description',
            start_price=100.00,
            final_price=90.00,
            duration=120
        )
        self.start_time = timezone.now()
        self.event_data = {
            'masterclass': self.masterclass,
            'start_datetime': self.start_time,
            'available_seats': 10
        }
        self.event = Event.objects.create(**self.event_data)

    def test_event_creation(self):
        self.assertEqual(self.event.masterclass, self.masterclass)
        self.assertEqual(self.event.start_datetime, self.start_time)
        self.assertEqual(self.event.available_seats, 10)
        self.assertEqual(self.event.end_datetime, self.start_time + timedelta(minutes=120))

    def test_event_str(self):
        expected_str = f"Test Masterclass - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.event), expected_str)

    def test_event_is_full(self):
        self.assertFalse(self.event.is_full())
        self.event.available_seats = 0
        self.event.save()
        self.assertTrue(self.event.is_full())

    def test_event_reserve_seat(self):
        initial_occupied = self.event.occupied_seats
        self.assertTrue(self.event.reserve_seat())
        self.event.refresh_from_db()
        self.assertEqual(self.event.occupied_seats, initial_occupied + 1)

        # Test reserving when full
        self.event.available_seats = 0
        self.event.save()
        self.assertFalse(self.event.reserve_seat())


class EventStrTest(TestCase):
    def setUp(self):
        self.masterclass = MasterClass.objects.create(
            name='EventStr Masterclass',
            short_description='EventStr Description',
            start_price=100.00,
            final_price=90.00,
            duration=120
        )
        self.start_time = timezone.now()
        self.event = Event.objects.create(
            masterclass=self.masterclass,
            start_datetime=self.start_time,
            available_seats=10
        )

    def test_event_str(self):
        expected_str = f"EventStr Masterclass - {self.start_time.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(self.event), expected_str) 