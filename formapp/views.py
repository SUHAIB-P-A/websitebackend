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
