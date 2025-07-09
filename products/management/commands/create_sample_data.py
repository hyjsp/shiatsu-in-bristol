from django.core.management.base import BaseCommand
from django.conf import settings
from products.models import Category, Product


class Command(BaseCommand):
    help = 'Create sample categories and products for shiatsu sessions'

    def handle(self, *args, **options):
        # Skip loading sample data during tests
        if settings.TESTING:
            self.stdout.write(
                self.style.WARNING('Skipping sample data creation during tests.')
            )
            return

        # Create categories
        sessions_category, created = Category.objects.get_or_create(
            name='Shiatsu Sessions',
            defaults={'description': 'Professional shiatsu massage sessions'}
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created category: {sessions_category.name}')
            )

        vouchers_category, created = Category.objects.get_or_create(
            name='Gift Vouchers',
            defaults={'description': 'Gift vouchers for shiatsu sessions'}
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created category: {vouchers_category.name}')
            )

        # Create sample products
        products_data = [
            {
                'name': '30-Minute Shiatsu Session',
                'description': 'A relaxing 30-minute shiatsu session perfect for stress relief and tension release.',
                'price': 35.00,
                'duration_minutes': 30,
                'category': sessions_category,
            },
            {
                'name': '60-Minute Shiatsu Session',
                'description': 'A comprehensive 60-minute shiatsu session for deep relaxation and full body treatment.',
                'price': 65.00,
                'duration_minutes': 60,
                'category': sessions_category,
            },
            {
                'name': '90-Minute Extended Session',
                'description': 'An extended 90-minute session for maximum relaxation and therapeutic benefits.',
                'price': 95.00,
                'duration_minutes': 90,
                'category': sessions_category,
            },
            {
                'name': '£50 Gift Voucher',
                'description': 'A gift voucher worth £50 that can be used towards any shiatsu session.',
                'price': 50.00,
                'duration_minutes': None,
                'category': vouchers_category,
            },
            {
                'name': '£100 Gift Voucher',
                'description': 'A gift voucher worth £100 that can be used towards any shiatsu session.',
                'price': 100.00,
                'duration_minutes': None,
                'category': vouchers_category,
            },
        ]

        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created product: {product.name} - £{product.price}')
                )

        self.stdout.write(
            self.style.SUCCESS('Sample data created successfully!')
        ) 