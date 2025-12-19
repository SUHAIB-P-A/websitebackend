from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import CollectionForm
from .serializers import CollectionFormSerializer


@api_view(['POST'])
def submit_form(request):
    serializer = CollectionFormSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Form saved successfully!"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
