from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from sessions_app.models import Session

class Command(BaseCommand):
    help = 'Seeds initial demo creator user and mentorship sessions if database is empty.'

    def handle(self, *args, **kwargs):
        if Session.objects.count() > 0:
            self.stdout.write(self.style.SUCCESS(f'Database already contains {Session.objects.count()} sessions. Skipping seed.'))
            return

        creator, _ = User.objects.get_or_create(
            email='creator@example.com',
            defaults={
                'name': 'Sarah Connor (Senior System Architect)',
                'role': User.Role.CREATOR
            }
        )

        test_user, _ = User.objects.get_or_create(
            email='user@example.com',
            defaults={
                'name': 'Alex Mercer',
                'role': User.Role.USER
            }
        )

        s1 = Session.objects.create(
            creator=creator,
            title='System Architecture & High-Concurrency Systems Masterclass',
            description='Learn how to design scalable, fault-tolerant microservices and high-concurrency database locking mechanisms using Django, PostgreSQL, and Redis.',
            start_time=timezone.now() + timedelta(days=2),
            duration=90,
            capacity=5
        )

        s2 = Session.objects.create(
            creator=creator,
            title='React 18 & TypeScript Production Patterns',
            description='Deep dive into React state management, custom hooks, Axios interceptors, and strict TypeScript patterns for enterprise web applications.',
            start_time=timezone.now() + timedelta(days=5),
            duration=60,
            capacity=1
        )

        s3 = Session.objects.create(
            creator=creator,
            title='DevOps & Production Docker Orchestration',
            description='Containerizing multi-tier applications with Nginx reverse proxying, PostgreSQL volume persistence, and optimized multi-stage Docker builds.',
            start_time=timezone.now() + timedelta(days=7),
            duration=120,
            capacity=10
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully seeded {Session.objects.count()} demo sessions and accounts.'))
