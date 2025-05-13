from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = "Create or reinstate a superuser."

    def handle(self, *args, **options):
        username = input("Username: ")
        existing_user = User.objects.filter(username=username).first()

        if existing_user:
            if existing_user.is_superuser:
                self.stdout.write(self.style.SUCCESS(f"User '{username}' already exists as a superuser."))
            else:
                existing_user.is_superuser = True
                existing_user.is_active = True
                existing_user.access_revoked = False
                existing_user.role="SuperUser"
                existing_user.save()
                self.stdout.write(self.style.SUCCESS(f"User '{username}' reinstated as a superuser."))
        else:
            self.stdout.write(self.style.ERROR(f"User '{username}' does not exist. Use 'createsuperuser' instead."))
