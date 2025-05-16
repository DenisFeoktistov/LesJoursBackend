from django.core.management.base import BaseCommand
from masterclasses.models import MasterClass


class Command(BaseCommand):
    help = 'Updates existing slugs to include IDs'

    def handle(self, *args, **options):
        masterclasses = MasterClass.objects.all()
        updated_count = 0

        for masterclass in masterclasses:
            if not masterclass.slug.endswith(f"-{masterclass.id}"):
                base_slug = masterclass.slug
                masterclass.slug = f"{base_slug}-{masterclass.id}"
                masterclass.save(update_fields=['slug'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated slug for "{masterclass.name}": {base_slug} -> {masterclass.slug}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} masterclass slugs'
            )
        ) 