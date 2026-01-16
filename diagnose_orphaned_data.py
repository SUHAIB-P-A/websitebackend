#!/usr/bin/env python
"""
Diagnostic script to identify orphaned data from deleted staff members.
This script checks for:
1. Students (CollectionForm) with assigned_staff = NULL (potentially orphaned)
2. Enquiries with assigned_staff = NULL (potentially orphaned)
3. Notifications with recipient = NULL (orphaned)
4. Staff documents orphaned in filesystem
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from formapp.models import Staff, StaffDocument, CollectionForm, Enquiry
from notifications.models import Notification
from django.conf import settings

def check_orphaned_students():
    """Check for students with NULL assigned_staff"""
    orphaned_students = CollectionForm.objects.filter(assigned_staff__isnull=True)
    count = orphaned_students.count()
    
    print(f"\n{'=' * 60}")
    print(f"ORPHANED STUDENTS (assigned_staff = NULL)")
    print(f"{'=' * 60}")
    print(f"Total: {count}")
    
    if count > 0:
        print("\nSample records (first 5):")
        for student in orphaned_students[:5]:
            print(f"  - ID: {student.id} | Name: {student.first_name} {student.last_name} | Email: {student.email} | Created: {student.created_at}")
    
    return count

def check_orphaned_enquiries():
    """Check for enquiries with NULL assigned_staff"""
    orphaned_enquiries = Enquiry.objects.filter(assigned_staff__isnull=True)
    count = orphaned_enquiries.count()
    
    print(f"\n{'=' * 60}")
    print(f"ORPHANED ENQUIRIES (assigned_staff = NULL)")
    print(f"{'=' * 60}")
    print(f"Total: {count}")
    
    if count > 0:
        print("\nSample records (first 5):")
        for enquiry in orphaned_enquiries[:5]:
            print(f"  - ID: {enquiry.id} | Name: {enquiry.name} | Phone: {enquiry.phone} | Created: {enquiry.created_at}")
    
    return count

def check_orphaned_notifications():
    """Check for notifications with NULL recipient"""
    orphaned_notifications = Notification.objects.filter(recipient__isnull=True)
    count = orphaned_notifications.count()
    
    print(f"\n{'=' * 60}")
    print(f"ORPHANED NOTIFICATIONS (recipient = NULL)")
    print(f"{'=' * 60}")
    print(f"Total: {count}")
    
    if count > 0:
        print("\nSample records (first 5):")
        for notif in orphaned_notifications[:5]:
            print(f"  - ID: {notif.id} | Title: {notif.title} | Created: {notif.created_at}")
    
    return count

def check_orphaned_documents():
    """Check for documents in filesystem that don't have DB records"""
    media_root = settings.MEDIA_ROOT
    docs_path = os.path.join(media_root, 'staff_documents')
    
    print(f"\n{'=' * 60}")
    print(f"ORPHANED DOCUMENT FILES")
    print(f"{'=' * 60}")
    
    if not os.path.exists(docs_path):
        print("No staff_documents directory found.")
        return 0
    
    # Get all files in the directory
    filesystem_files = set()
    for root, dirs, files in os.walk(docs_path):
        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), media_root)
            filesystem_files.add(rel_path)
    
    # Get all files referenced in DB
    db_files = set(StaffDocument.objects.values_list('file', flat=True))
    
    orphaned_files = filesystem_files - db_files
    
    print(f"Total files in filesystem: {len(filesystem_files)}")
    print(f"Total files in database: {len(db_files)}")
    print(f"Orphaned files: {len(orphaned_files)}")
    
    if orphaned_files:
        print("\nOrphaned files (first 10):")
        for file in list(orphaned_files)[:10]:
            print(f"  - {file}")
    
    return len(orphaned_files)

def check_current_staff():
    """Display current staff count"""
    active_staff = Staff.objects.filter(active_status=True).count()
    inactive_staff = Staff.objects.filter(active_status=False).count()
    total_staff = Staff.objects.count()
    
    print(f"\n{'=' * 60}")
    print(f"CURRENT STAFF STATUS")
    print(f"{'=' * 60}")
    print(f"Active Staff: {active_staff}")
    print(f"Inactive Staff: {inactive_staff}")
    print(f"Total Staff: {total_staff}")

def main():
    print("\n" + "=" * 60)
    print("DATABASE ORPHANED DATA DIAGNOSTIC REPORT")
    print("=" * 60)
    print(f"Generated at: {django.utils.timezone.now()}")
    
    check_current_staff()
    
    orphaned_students_count = check_orphaned_students()
    orphaned_enquiries_count = check_orphaned_enquiries()
    orphaned_notifications_count = check_orphaned_notifications()
    orphaned_files_count = check_orphaned_documents()
    
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Orphaned Students: {orphaned_students_count}")
    print(f"Orphaned Enquiries: {orphaned_enquiries_count}")
    print(f"Orphaned Notifications: {orphaned_notifications_count}")
    print(f"Orphaned Document Files: {orphaned_files_count}")
    print(f"{'=' * 60}\n")
    
    if any([orphaned_students_count, orphaned_enquiries_count, orphaned_notifications_count, orphaned_files_count]):
        print("⚠️  Orphaned data found! Run cleanup script to remove.")
    else:
        print("✅ No orphaned data found. Database is clean!")

if __name__ == "__main__":
    main()
