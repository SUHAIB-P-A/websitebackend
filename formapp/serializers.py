from rest_framework import serializers
from .models import CollectionForm, Enquiry


class CollectionFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionForm
        fields = '__all__'

    def to_internal_value(self, data):
        """
        Move any fields not in the model definition into 'extra_data'.
        """
        # Get standard fields from the model
        model_fields = set([f.name for f in CollectionForm._meta.get_fields()])
        
        # mutable copy of data
        data = data.copy()
        extra_data = {}

        # Identify extra fields
        for key in list(data.keys()):
            if key not in model_fields and key != 'extra_data':
                extra_data[key] = data.pop(key)
        
        # If extra_data already exists in input, merge it (though usually it won't)
        if 'extra_data' in data:
            if isinstance(data['extra_data'], dict):
                extra_data.update(data['extra_data'])
        
        data['extra_data'] = extra_data
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """
        Unpack 'extra_data' back into the top-level dictionary.
        """
        ret = super().to_representation(instance)
        extra_data = ret.pop('extra_data', {})
        if extra_data:
            ret.update(extra_data)
        return ret


class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = '__all__'
