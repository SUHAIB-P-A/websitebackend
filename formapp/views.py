from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from django.db.models import Q
from .models import CollectionForm, Staff, Enquiry
from .serializers import CollectionFormSerializer, StaffSerializer, EnquirySerializer
from .utils import allocate_staff, redistribute_work

# --- Staff Authentication & Management ---

@api_view(['POST'])
def staff_login(request):
    login_id = request.data.get('login_id')
    password = request.data.get('password')
    
    try:
        staff = Staff.objects.get(login_id=login_id)
        if staff.check_password(password):
            if not staff.active_status:
                return Response({"error": "Account is inactive"}, status=status.HTTP_403_FORBIDDEN)
            
            # Simple tokenless auth: return user info and role
            return Response({
                "message": "Login successful",
                "role": "staff", 
                "staff_id": staff.id,
                "name": staff.name
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
        staff = Staff.objects.all().order_by('id')
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)
    
    if request.method == 'POST':
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
def staff_detail(request, pk):
    try:
        staff = Staff.objects.get(pk=pk)
    except Staff.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = StaffSerializer(staff)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = StaffSerializer(staff, data=request.data)
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


@api_view(['GET', 'PUT', 'DELETE'])
def submit_detail(request, pk):
    try:
        student = CollectionForm.objects.get(pk=pk)
    except CollectionForm.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    # Security check: frontend handles visibility, backend allows modify if known ID.
    
    if request.method == 'GET':
        serializer = CollectionFormSerializer(student)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CollectionFormSerializer(student, data=request.data)
        if serializer.is_valid():
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


@api_view(['GET', 'DELETE'])
def enquiry_detail(request, pk):
    try:
        enquiry = Enquiry.objects.get(pk=pk)
    except Enquiry.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = EnquirySerializer(enquiry)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        enquiry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
