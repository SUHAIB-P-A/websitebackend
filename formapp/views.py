from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db.models import Q
from django.utils import timezone
# ... (existing imports, add ModelViewSet)
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CollectionForm, Staff, Enquiry, StaffDocument
from .serializers import CollectionFormSerializer, StaffSerializer, EnquirySerializer, StaffDocumentSerializer
from .utils import allocate_staff, redistribute_work

# --- Staff Authentication & Management ---

# ... (existing code up to staff_detail)

class StaffDocumentViewSet(viewsets.ModelViewSet):
    """
    Handles Staff Document uploads and listing.
    Filter by ?staff_id=X
    """
    queryset = StaffDocument.objects.all()
    serializer_class = StaffDocumentSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        qs = super().get_queryset()
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            qs = qs.filter(staff_id=staff_id)
        return qs.order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        # Allow passing staff_id manually if needed, but usually it's in the form data
        return super().create(request, *args, **kwargs)

# --- Students / Collection Forms ---

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@api_view(['POST'])
def staff_login(request):
    login_id = request.data.get('login_id', '').strip()
    password = request.data.get('password', '').strip()
    
    try:
        # Case-insensitive lookup
        staff = Staff.objects.get(login_id__iexact=login_id)
        if staff.check_password(password):
            # We allow login even if active_status is False (Offline for leads)
            # if not staff.active_status:
            #     return Response({"error": "Account is inactive"}, status=status.HTTP_403_FORBIDDEN)
            
            # Determine role
            role = 'admin' if staff.login_id.lower() == 'admin' else 'staff'

            return Response({
                "message": "Login successful",
                "role": role, 
                "staff_id": staff.id,
                "name": staff.name,
                "email": staff.email,
                "login_id": staff.login_id,
                "dob": staff.dob,
                "gender": staff.gender,
                "phone": staff.phone,
                "image": staff.profile_image
            })
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    except Staff.DoesNotExist:
        # Check if it's a hardcoded admin for bootstrapping?
        if login_id == 'admin' and password == 'admin123': # TEMPORARY BOOTSTRAP
             return Response({"message": "Admin Login", "role": "admin", "staff_id": None})
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET', 'POST'])
def staff_list(request):
    # Only Admin should access this
    if request.method == 'GET':
        staff = Staff.objects.filter(~Q(role='admin') & ~Q(login_id__iexact='admin')).order_by('id')
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def staff_detail(request, pk):
    try:
        staff = Staff.objects.get(pk=pk)
    except Staff.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = StaffSerializer(staff)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        serializer = StaffSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        # Redistribute work before deleting
        redistribute_work(staff.id)
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Students / Collection Forms ---

@api_view(['GET', 'POST'])
def submit_form(request):
    # Check for staff_id in headers or query params to filter
    staff_id = request.headers.get('X-Staff-ID') or request.GET.get('staff_id')
    
    # 👉 GET: fetch data
    if request.method == 'GET':
        if staff_id and staff_id != 'null' and staff_id != 'undefined':
            # Staff View: Filter by assigned_staff
            forms = CollectionForm.objects.filter(assigned_staff_id=staff_id).order_by('-created_at')
        else:
            # Admin View: Show all
            forms = CollectionForm.objects.all().order_by('-created_at')
            
        serializer = CollectionFormSerializer(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 👉 POST: save data
    if request.method == 'POST':
        serializer = CollectionFormSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            # AUTO ALLOCATION
            allocate_staff(instance)
            return Response(
                {"message": "Form saved successfully!"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def submit_detail(request, pk):
    try:
        student = CollectionForm.objects.get(pk=pk)
    except CollectionForm.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Security check: frontend handles visibility, backend allows modify if known ID.
    
    if request.method == 'GET':
        serializer = CollectionFormSerializer(student)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = CollectionFormSerializer(student, data=request.data, partial=partial)
        if serializer.is_valid():
            # Set viewed_at if not set and is_read is True
            if serializer.validated_data.get('is_read') and not student.viewed_at:
                 instance = serializer.save(viewed_at=timezone.now())
            else:
                 instance = serializer.save()
            
            # Check for explicit Auto Allocation request
            if request.data.get('auto_allocate'):
                allocate_staff(instance)
                # Refresh from DB to return updated assigned_staff
                instance.refresh_from_db()
                return Response(CollectionFormSerializer(instance).data)

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Enquiries ---

@api_view(['GET', 'POST'])
def enquiry_list(request):
    staff_id = request.headers.get('X-Staff-ID') or request.GET.get('staff_id')

    if request.method == 'GET':
        if staff_id and staff_id != 'null' and staff_id != 'undefined':
             enquiries = Enquiry.objects.filter(assigned_staff_id=staff_id).order_by('-created_at')
        else:
             enquiries = Enquiry.objects.all().order_by('-created_at')
        serializer = EnquirySerializer(enquiries, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = EnquirySerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            # AUTO ALLOCATION
            allocate_staff(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def enquiry_detail(request, pk):
    try:
        enquiry = Enquiry.objects.get(pk=pk)
    except Enquiry.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EnquirySerializer(enquiry)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = EnquirySerializer(enquiry, data=request.data)
        if serializer.is_valid():
            # Set viewed_at if not set and is_read is True
            if serializer.validated_data.get('is_read') and not enquiry.viewed_at:
                 instance = serializer.save(viewed_at=timezone.now())
            else:
                 instance = serializer.save()
            
            # Check for explicit Auto Allocation request
            if request.data.get('auto_allocate'):
                allocate_staff(instance)
                instance.refresh_from_db()
                return Response(EnquirySerializer(instance).data)

            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        enquiry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

@csrf_exempt
@api_view(['POST'])
def reallocate_leads(request):
    """
    Reallocates leads from one staff to another based on criteria.
    Inputs:
        source_staff_id: int or 'all'
        target_staff_id: int
        criteria: 'unread', 'pending', 'all'
        count: int (optional, default 50)
        type: 'student', 'enquiry'
    """
    source_id = request.data.get('source_staff_id')
    target_id = request.data.get('target_staff_id')
    criteria = request.data.get('criteria', 'unread').lower().strip()
    count = int(request.data.get('count', 50))
    lead_type = request.data.get('type', 'student')

    if not target_id:
        return Response({"error": "Target staff is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate IDs
    try:
        target_staff = Staff.objects.get(pk=target_id)
        if str(source_id) != 'all' and source_id:
            Staff.objects.get(pk=source_id) # Check existence
    except Staff.DoesNotExist:
        return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

    # Select Model
    Model = CollectionForm if lead_type == 'student' else Enquiry

    # Build Query
    query = Q()
    if str(source_id) != 'all':
        query &= Q(assigned_staff_id=source_id)
    
    if criteria == 'unread':
        query &= Q(is_read=False) & Q(status='Pending')
    elif criteria == 'pending':
        query &= Q(status='Pending')
    elif criteria == 'all':
        pass # Explicitly allow all
    else:
        # Unknown criteria? Default to Unread logic for safety, or return empty?
        # Let's return NO results to be safe if criteria is weird.
        return Response({"error": "Invalid criteria"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Fetch Leads (IDs only for optimization)
    ids_to_update = list(Model.objects.filter(query).order_by('created_at').values_list('id', flat=True)[:count])
    
    if ids_to_update:
        updated_count = Model.objects.filter(id__in=ids_to_update).update(assigned_staff=target_staff)

    return Response({
        "message": f"Successfully reallocated {updated_count} {lead_type}s to {target_staff.name}",
        "count": updated_count
    })


@api_view(['GET'])
def dashboard_stats(request):
    """
    Returns aggregated statistics for the dashboard.
    Support filtering by staff_id for robust role-based data.
    """
    staff_id = request.headers.get('X-Staff-ID') or request.GET.get('staff_id')
    role = request.GET.get('role', 'staff') # 'admin' or 'staff'
    
    # Base QuerySets
    enq_qs = Enquiry.objects.all()
    form_qs = CollectionForm.objects.all()
    
    # Appply Filters for Non-Admin
    if role.lower() != 'admin' and staff_id and staff_id != 'null':
        enq_qs = enq_qs.filter(assigned_staff_id=staff_id)
        form_qs = form_qs.filter(assigned_staff_id=staff_id)

    # Calculate Stats
    stats = {
        'total_enquiries': enq_qs.count(),
        'pending_enquiries': enq_qs.filter(is_read=False).count(),
        'total_students': form_qs.count(),
        'pending_students': form_qs.filter(is_read=False).count(),
    }

    # Fetch Recent Activity (Limit 5)
    recent_enquiries = EnquirySerializer(enq_qs.order_by('-created_at')[:5], many=True).data
    recent_students = CollectionFormSerializer(form_qs.order_by('-created_at')[:5], many=True).data

    return Response({
        'stats': stats,
        'recent_enquiries': recent_enquiries,
        'recent_students': recent_students
    })
