from django.core.management.base import BaseCommand
from products.models import Product, Category


class Command(BaseCommand):
    help = 'Clear all sample data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all sample data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL products and categories. '
                    'Use --confirm to proceed.'
                )
            )
            return

        # Count items before deletion
        product_count = Product.objects.count()
        category_count = Category.objects.count()

        # Delete all products and categories
        Product.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Deleted {product_count} products and {category_count} categories.'
            )
        ) 