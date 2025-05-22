import os
import django
from django.utils.text import slugify

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lesjours.settings')
django.setup()

from masterclasses.models import MasterClass

try:
    from transliterate import translit
except ImportError:
    translit = None

def fix_slugs():
    for m in MasterClass.objects.all():
        name = m.name
        if translit:
            name_latin = translit(name, 'ru', reversed=True)
        else:
            name_latin = name
        correct_slug = slugify(name_latin)
        if MasterClass.objects.exclude(id=m.id).filter(slug=correct_slug).exists():
            correct_slug = f'{correct_slug}-{m.id}'
        if m.slug != correct_slug:
            print(f'Изменяю слаг: {m.slug} -> {correct_slug}')
            m.slug = correct_slug
            m.save(update_fields=['slug'])
    print('Слаги успешно исправлены!')

if __name__ == '__main__':
    fix_slugs() 