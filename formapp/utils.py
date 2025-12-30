from django.db.models import Count, Q
from .models import Staff, CollectionForm, Enquiry

def allocate_staff(instance):
    """
    Assigns the instance (Student or Enquiry) to the staff member with the lowest workload.
    Workload = count(assigned_students) + count(assigned_enquiries)
    """
    active_staff = Staff.objects.filter(active_status=True)
    
    if not active_staff.exists():
        return None

    # Calculate workload for each staff
    # We need to annotate with the sum of both relations.
    # Since Django annotations can be tricky with multiple Count on different relations (producing cross product),
    # we'll do it in python for simplicity if the staff count is low (which it likely is).
    # Or use subqueries. Given typical staff size < 50, Python sorting is fine and reliable.
    
    staff_workloads = []
    for staff in active_staff:
        load = staff.assigned_students.count() + staff.assigned_enquiries.count()
        staff_workloads.append((staff, load))
    
    # Sort by load (ascending), then by ID (for stability)
    staff_workloads.sort(key=lambda x: (x[1], x[0].id))
    
    selected_staff = staff_workloads[0][0]
    
    instance.assigned_staff = selected_staff
    instance.save(update_fields=['assigned_staff'])
    return selected_staff

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
