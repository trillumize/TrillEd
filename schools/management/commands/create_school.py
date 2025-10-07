from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from schools.models import Client, Domain
from accounts.models import User


class Command(BaseCommand):
    help = 'Create a new school tenant with admin user'

    def add_arguments(self, parser):
        parser.add_argument('--name', type=str, required=True, help='School name')
        parser.add_argument('--schema', type=str, required=True, help='Schema name')
        parser.add_argument('--domain', type=str, required=True, help='Domain')
        parser.add_argument('--username', type=str, default='schooladmin', help='Admin username')
        parser.add_argument('--password', type=str, required=True, help='Admin password')
        parser.add_argument('--email', type=str, default='', help='Admin email')
        parser.add_argument('--trial', action='store_true', help='Set on trial')

    def handle(self, *args, **options):
        name = options['name']
        schema = options['schema']
        domain = options['domain']
        username = options['username']
        password = options['password']
        email = options['email'] or f"{schema}@school.com"
        on_trial = options['trial']

        try:
            if Client.objects.filter(schema_name=schema).exists():
                self.stdout.write(self.style.ERROR(f'School "{schema}" already exists!'))
                return

            self.stdout.write(f'Creating school: {name}...')
            client = Client.objects.create(
                name=name,
                schema_name=schema,
                admin_username=username,
                admin_email=email,
                admin_password=password,
                on_trial=on_trial
            )
            
            self.stdout.write('Creating database schema...')
            client.create_schema(check_if_exists=True)

            self.stdout.write(f'Creating domain: {domain}...')
            Domain.objects.create(
                domain=domain,
                tenant=client,
                is_primary=True
            )

            self.stdout.write('Creating admin user...')
            with schema_context(schema):
                admin_user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password,
                    first_name='School',
                    last_name='Admin',
                )
                admin_user.role = 'school_admin'
                admin_user.save()

            self.stdout.write(self.style.SUCCESS('\nSchool created successfully!'))
            self.stdout.write(self.style.SUCCESS(f'Name: {name}'))
            self.stdout.write(self.style.SUCCESS(f'Domain: {domain}'))
            self.stdout.write(self.style.SUCCESS(f'Username: {username}'))
            self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
            self.stdout.write(self.style.SUCCESS(f'\nLogin: http://{domain}:8000/admin/'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))