#!/usr/bin/env python
"""
Cleanup script to remove orphaned data from deleted staff members.
This script can:
1. Delete students/enquiries with NULL assigned_staff
2. Delete notifications with NULL recipient
3. Remove orphaned document files from filesystem
4. Optionally reassign orphaned students/enquiries to another staff member

Usage:
    python3 cleanup_orphaned_data.py --dry-run        # See what would be deleted
    python3 cleanup_orphaned_data.py --execute        # Actually delete the data
    python3 cleanup_orphaned_data.py --reassign=STAFF_ID  # Reassign to specific staff
"""
import os
import sys
import django
import argparse

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from formapp.models import Staff, StaffDocument, CollectionForm, Enquiry
from notifications.models import Notification
from django.conf import settings

class DatabaseCleaner:
    def __init__(self, dry_run=True, reassign_to=None):
        self.dry_run = dry_run
        self.reassign_to_id = reassign_to
        self.reassign_staff = None
        
        if reassign_to:
            try:
                self.reassign_staff = Staff.objects.get(id=reassign_to)
                print(f"✓ Will reassign to: {self.reassign_staff.name} (ID: {self.reassign_staff.id})")
            except Staff.DoesNotExist:
                print(f"✗ Error: Staff with ID {reassign_to} not found!")
                sys.exit(1)
    
    def cleanup_students(self):
        """Clean up or reassign students with NULL assigned_staff"""
        orphaned = CollectionForm.objects.filter(assigned_staff__isnull=True)
        count = orphaned.count()
        
        print(f"\n{'=' * 60}")
        print(f"ORPHANED STUDENTS: {count}")
        print(f"{'=' * 60}")
        
        if count == 0:
            print("✓ No orphaned students found.")
            return 0
        
        if self.reassign_staff:
            print(f"Action: Reassign to {self.reassign_staff.name}")
            if not self.dry_run:
                orphaned.update(assigned_staff=self.reassign_staff)
                print(f"✓ Reassigned {count} students")
        else:
            print(f"Action: Delete {count} students")
            if self.dry_run:
                print("Sample records to be deleted (first 5):")
                for student in orphaned[:5]:
                    print(f"  - ID: {student.id} | {student.first_name} {student.last_name} | {student.email}")
            else:
                deleted_count = orphaned.delete()[0]
                print(f"✓ Deleted {deleted_count} students")
        
        return count
    
    def cleanup_enquiries(self):
        """Clean up or reassign enquiries with NULL assigned_staff"""
        orphaned = Enquiry.objects.filter(assigned_staff__isnull=True)
        count = orphaned.count()
        
        print(f"\n{'=' * 60}")
        print(f"ORPHANED ENQUIRIES: {count}")
        print(f"{'=' * 60}")
        
        if count == 0:
            print("✓ No orphaned enquiries found.")
            return 0
        
        if self.reassign_staff:
            print(f"Action: Reassign to {self.reassign_staff.name}")
            if not self.dry_run:
                orphaned.update(assigned_staff=self.reassign_staff)
                print(f"✓ Reassigned {count} enquiries")
        else:
            print(f"Action: Delete {count} enquiries")
            if self.dry_run:
                print("Sample records to be deleted (first 5):")
                for enquiry in orphaned[:5]:
                    print(f"  - ID: {enquiry.id} | {enquiry.name} | {enquiry.phone}")
            else:
                deleted_count = orphaned.delete()[0]
                print(f"✓ Deleted {deleted_count} enquiries")
        
        return count
    
    def cleanup_notifications(self):
        """Delete notifications with NULL recipient"""
        orphaned = Notification.objects.filter(recipient__isnull=True)
        count = orphaned.count()
        
        print(f"\n{'=' * 60}")
        print(f"ORPHANED NOTIFICATIONS: {count}")
        print(f"{'=' * 60}")
        
        if count == 0:
            print("✓ No orphaned notifications found.")
            return 0
        
        print(f"Action: Delete {count} notifications")
        if self.dry_run:
            print("Sample records to be deleted (first 5):")
            for notif in orphaned[:5]:
                print(f"  - ID: {notif.id} | {notif.title} | {notif.created_at}")
        else:
            deleted_count = orphaned.delete()[0]
            print(f"✓ Deleted {deleted_count} notifications")
        
        return count
    
    def cleanup_document_files(self):
        """Remove orphaned document files from filesystem"""
        media_root = settings.MEDIA_ROOT
        docs_path = os.path.join(media_root, 'staff_documents')
        
        print(f"\n{'=' * 60}")
        print(f"ORPHANED DOCUMENT FILES")
        print(f"{'=' * 60}")
        
        if not os.path.exists(docs_path):
            print("✓ No staff_documents directory found.")
            return 0
        
        # Get all files in the directory
        filesystem_files = {}
        for root, dirs, files in os.walk(docs_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, media_root)
                filesystem_files[rel_path] = full_path
        
        # Get all files referenced in DB
        db_files = set(StaffDocument.objects.values_list('file', flat=True))
        
        orphaned_files = set(filesystem_files.keys()) - db_files
        
        print(f"Total files in filesystem: {len(filesystem_files)}")
        print(f"Total files in database: {len(db_files)}")
        print(f"Orphaned files: {len(orphaned_files)}")
        
        if len(orphaned_files) == 0:
            print("✓ No orphaned files found.")
            return 0
        
        print(f"Action: Delete {len(orphaned_files)} orphaned files")
        if self.dry_run:
            print("Files to be deleted (first 10):")
            for file in list(orphaned_files)[:10]:
                print(f"  - {file}")
        else:
            deleted_count = 0
            for rel_path in orphaned_files:
                try:
                    full_path = filesystem_files[rel_path]
                    os.remove(full_path)
                    deleted_count += 1
                except Exception as e:
                    print(f"✗ Error deleting {rel_path}: {e}")
            print(f"✓ Deleted {deleted_count} files")
        
        return len(orphaned_files)
    
    def run(self):
        """Run the cleanup process"""
        mode = "DRY RUN" if self.dry_run else "EXECUTION"
        
        print(f"\n{'=' * 60}")
        print(f"DATABASE CLEANUP - {mode} MODE")
        print(f"{'=' * 60}")
        
        if self.dry_run:
            print("⚠️  DRY RUN MODE - No changes will be made")
        else:
            print("⚠️  EXECUTION MODE - Changes will be permanent!")
            response = input("\nAre you sure you want to proceed? (yes/no): ")
            if response.lower() != 'yes':
                print("Cleanup cancelled.")
                return
        
        students_count = self.cleanup_students()
        enquiries_count = self.cleanup_enquiries()
        notifications_count = self.cleanup_notifications()
        files_count = self.cleanup_document_files()
        
        print(f"\n{'=' * 60}")
        print("CLEANUP SUMMARY")
        print(f"{'=' * 60}")
        print(f"Students: {students_count}")
        print(f"Enquiries: {enquiries_count}")
        print(f"Notifications: {notifications_count}")
        print(f"Document Files: {files_count}")
        print(f"{'=' * 60}")
        
        if self.dry_run:
            print("\n💡 Run with --execute to actually perform cleanup")
        else:
            print("\n✅ Cleanup completed successfully!")

def main():
    parser = argparse.ArgumentParser(description='Clean up orphaned data from database')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='Show what would be deleted without making changes')
    group.add_argument('--execute', action='store_true', help='Actually delete the orphaned data')
    parser.add_argument('--reassign', type=int, metavar='STAFF_ID', help='Reassign orphaned students/enquiries to this staff ID instead of deleting')
    
    args = parser.parse_args()
    
    cleaner = DatabaseCleaner(
        dry_run=args.dry_run,
        reassign_to=args.reassign
    )
    cleaner.run()

if __name__ == "__main__":
    main()
