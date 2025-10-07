from django.core.management.base import BaseCommand
from schools.models import Client, Domain

class Command(BaseCommand):
    help = 'Setup public tenant if it does not exist'

    def handle(self, *args, **options):
        # Check if public tenant exists
        if Client.objects.filter(schema_name='public').exists():
            self.stdout.write(self.style.SUCCESS('Public tenant already exists'))
            return

        # Create public tenant
        public_tenant = Client.objects.create(
            schema_name='public',
            name='Public',
            admin_username='public',
            admin_email='public@example.com'
        )
        public_tenant.set_admin_password('temp123')
        public_tenant.save()

        # Create domain
        Domain.objects.create(
            domain='trilled.onrender.com',
            tenant=public_tenant,
            is_primary=True
        )

        self.stdout.write(self.style.SUCCESS('✅ Public tenant created successfully!'))
