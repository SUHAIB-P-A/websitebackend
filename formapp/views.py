from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import CollectionForm
from .serializers import CollectionFormSerializer


@api_view(['GET', 'POST'])
def submit_form(request):
    # 👉 GET: fetch data
    if request.method == 'GET':
        forms = CollectionForm.objects.all().order_by('-created_at')
        serializer = CollectionFormSerializer(forms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # 👉 POST: save data
    if request.method == 'POST':
        serializer = CollectionFormSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
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

    if request.method == 'GET':
        serializer = CollectionFormSerializer(student)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = CollectionFormSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


from .models import Enquiry
from .serializers import EnquirySerializer

@api_view(['GET', 'POST'])
def enquiry_list(request):
    if request.method == 'GET':
        enquiries = Enquiry.objects.all().order_by('-created_at')
        serializer = EnquirySerializer(enquiries, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        serializer = EnquirySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
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
