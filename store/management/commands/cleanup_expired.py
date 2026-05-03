"""
Management command to clean up expired products.

Usage:
    python manage.py cleanup_expired          # Delete all expired products
    python manage.py cleanup_expired --dry-run  # Preview what would be deleted
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from store.models import Product


class Command(BaseCommand):
    help = 'Delete products that have expired (past their expires_at date)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview expired products without deleting them',
        )

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Product.objects.filter(expires_at__lte=now)
        count = expired.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired products found. ✅'))
            return

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(f'Found {count} expired products (DRY RUN):'))
            for p in expired:
                days_ago = (now - p.expires_at).days
                self.stdout.write(f'  - {p.name} (expired {days_ago} days ago)')
        else:
            # Delete expired products and their images
            for p in expired:
                if p.image:
                    p.image.delete(save=False)  # Delete the image file
            expired.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} expired products. 🗑️'))
