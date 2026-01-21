from django.db.models import Count, Q, F, Value
from django.db.models import ExpressionWrapper, IntegerField, QuerySet
from .models import Staff, CollectionForm, Enquiry

def allocate_staff(instance):
    """
    Assigns the instance (Student or Enquiry) to the staff member with the lowest workload.
    Workload = count(assigned_students) + count(assigned_enquiries)
    
    Optimized: Uses Django ORM annotations to avoid N+1 query problem.
    """
    active_staff = Staff.objects.filter(active_status=True, role='staff')
    
    if not active_staff.exists():
        return None

    # Use annotations to calculate workload in a single query
    # Use values_list to get only the ID and workload, avoiding setting properties
    staff_data = active_staff.annotate(
        student_count=Count('assigned_students'),
        enquiry_count=Count('assigned_enquiries'),
        total_workload=ExpressionWrapper(
            F('student_count') + F('enquiry_count'),
            output_field=IntegerField()
        )
    ).values_list('id', 'total_workload').order_by('total_workload', 'id')
    
    if not staff_data:
        return None
    
    # Get the staff with minimum workload
    min_staff_id = staff_data.first()[0]
    selected_staff = Staff.objects.get(id=min_staff_id)
    
    if selected_staff:
        instance.assigned_staff = selected_staff
        # Save with all fields if it's new, otherwise just update assigned_staff
        if instance.pk is None:
            instance.save()
        else:
            instance.save(update_fields=['assigned_staff'])
        return selected_staff
    
    return None

def redistribute_work(staff_id):
    """
    Re-distributes all work from a deleted/removed staff member to remaining active staff.
    """
    try:
        # We assume the staff member might already be deleted or we are about to delete.
        # If calling BEFORE delete (recommended):
        staff = Staff.objects.get(id=staff_id)
        
        # CRITICAL: Mark as inactive so they are excluded from the allocation pool
        # during the subsequent allocate_staff calls.
        staff.active_status = False
        staff.save()

        students = list(staff.assigned_students.all())
        enquiries = list(staff.assigned_enquiries.all())
        
        for student in students:
            # Disassociate first to update counts correctly if needed, 
            # though allocate_staff will overwrite.
            student.assigned_staff = None 
            allocate_staff(student)
            
        for enquiry in enquiries:
            enquiry.assigned_staff = None
            allocate_staff(enquiry)
            
    except Staff.DoesNotExist:
        pass
            
    except Staff.DoesNotExist:
        pass
            
    except Staff.DoesNotExist:
        pass
            
    except Staff.DoesNotExist:
        pass
