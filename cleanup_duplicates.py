import os
import django
import sys

# Add the project directory to sys.path
sys.path.append('/Users/rintusam/Desktop/websitebackend/websitebackend')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websitebackend.settings')
django.setup()

from formapp.models import CollectionForm
from django.db.models import Count

def clean_duplicates():
    duplicates = CollectionForm.objects.values('email').annotate(count=Count('id')).filter(count__gt=1)
    if not duplicates:
        print("No duplicates found.")
        return

    print(f"Found {len(duplicates)} emails with duplicates.")
    for dep in duplicates:
        email = dep['email']
        print(f"Processing {email}...")
        entries = list(CollectionForm.objects.filter(email=email).order_by('-created_at'))
        
        # Keep the first one (latest), delete the rest
        if len(entries) > 1:
            for entry in entries[1:]:
                print(f"Deleting duplicate {email} (ID: {entry.id}, Created: {entry.created_at})")
                entry.delete()

if __name__ == '__main__':
    clean_duplicates()
