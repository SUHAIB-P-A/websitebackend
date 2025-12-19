from rest_framework import serializers
from .models import CollectionForm


class CollectionFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionForm
        fields = '__all__'
