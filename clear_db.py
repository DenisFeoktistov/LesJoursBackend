import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesjours.settings')
django.setup()

from masterclasses.models import MasterClass, Event

def clear_database():
    print("Очистка базы данных...")
    Event.objects.all().delete()
    MasterClass.objects.all().delete()
    print("База данных успешно очищена!")

if __name__ == '__main__':
    clear_database() 