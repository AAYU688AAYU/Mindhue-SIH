from django.core.management.base import BaseCommand
from api.seed_helper import seed_clinical_cases

class Command(BaseCommand):
    help = 'Seeds initial clinical benchmark retinal cases for ICDR validation.'

    def handle(self, *args, **options):
        self.stdout.write("Generating and analyzing clinical benchmark retinal cases...")
        count = seed_clinical_cases()
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded and analyzed {count} clinical benchmark cases!"))
