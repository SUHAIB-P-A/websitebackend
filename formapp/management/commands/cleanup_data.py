"""
Django management command to clean up orphaned and duplicate data.

Usage:
    python manage.py cleanup_data --cleanup=duplicates     # Remove duplicate entries
    python manage.py cleanup_data --cleanup=orphaned       # Remove orphaned data
    python manage.py cleanup_data --cleanup=all            # Run all cleanups
"""
from django.core.management.base import BaseCommand, CommandError
from formapp.models import Staff, StaffDocument, CollectionForm, Enquiry
from notifications.models import Notification
from django.conf import settings
from django.db.models import Count
import os


class Command(BaseCommand):
    help = 'Clean up orphaned and duplicate data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup',
            type=str,
            default='all',
            choices=['duplicates', 'orphaned', 'all'],
            help='Type of cleanup to perform'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        cleanup_type = options['cleanup']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be deleted'))

        if cleanup_type in ['duplicates', 'all']:
            self.cleanup_duplicates(dry_run)

        if cleanup_type in ['orphaned', 'all']:
            self.cleanup_orphaned(dry_run)

        self.stdout.write(self.style.SUCCESS('✓ Cleanup complete'))

    def cleanup_duplicates(self, dry_run=False):
        """Remove duplicate CollectionForm entries by email"""
        self.stdout.write('\n--- Cleaning Duplicate Entries ---')

        duplicates = CollectionForm.objects.values('email').annotate(
            count=Count('id')
        ).filter(count__gt=1)

        if not duplicates:
            self.stdout.write(self.style.SUCCESS('  No duplicates found'))
            return

        total_deleted = 0
        for dup in duplicates:
            email = dup['email']
            entries = list(CollectionForm.objects.filter(
                email=email
            ).order_by('-created_at'))

            if len(entries) > 1:
                for entry in entries[1:]:  # Keep first, delete rest
                    self.stdout.write(f"  {self.style.WARNING('DELETE')} {email} (ID: {entry.id})")
                    if not dry_run:
                        entry.delete()
                    total_deleted += 1

        self.stdout.write(self.style.SUCCESS(f'  Total deleted: {total_deleted}'))

    def cleanup_orphaned(self, dry_run=False):
        """Remove orphaned data with NULL assigned_staff"""
        self.stdout.write('\n--- Cleaning Orphaned Data ---')

        # Orphaned students
        orphaned_students = CollectionForm.objects.filter(assigned_staff__isnull=True)
        student_count = orphaned_students.count()
        if student_count > 0:
            self.stdout.write(f"  Found {student_count} orphaned students")
            for student in orphaned_students:
                self.stdout.write(
                    f"    {self.style.WARNING('DELETE')} {student.first_name} {student.last_name} (ID: {student.id})"
                )
                if not dry_run:
                    student.delete()
            self.stdout.write(
                self.style.SUCCESS(f"  Deleted {student_count} students")
            )

        # Orphaned enquiries
        orphaned_enquiries = Enquiry.objects.filter(assigned_staff__isnull=True)
        enquiry_count = orphaned_enquiries.count()
        if enquiry_count > 0:
            self.stdout.write(f"  Found {enquiry_count} orphaned enquiries")
            for enquiry in orphaned_enquiries:
                self.stdout.write(
                    f"    {self.style.WARNING('DELETE')} {enquiry.name} (ID: {enquiry.id})"
                )
                if not dry_run:
                    enquiry.delete()
            self.stdout.write(
                self.style.SUCCESS(f"  Deleted {enquiry_count} enquiries")
            )

        if student_count == 0 and enquiry_count == 0:
            self.stdout.write(self.style.SUCCESS('  No orphaned data found'))
