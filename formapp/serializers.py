from rest_framework import serializers
from .models import CollectionForm, Enquiry, Staff, StaffDocument

class StaffSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    student_count = serializers.ReadOnlyField()

    class Meta:
        model = Staff
        fields = ['id', 'name', 'email', 'login_id', 'password', 'active_status', 'role', 'student_count', 'created_at', 'phone', 'gender', 'dob', 'profile_image', 'official_photo', 'secondary_phone', 'designation', 'department', 'address', 'date_of_joining']

    def create(self, validated_data):
        password = validated_data.pop('password')
        staff = Staff(**validated_data)
        staff.set_password(password)
        staff.save()
        return staff
    
    def update(self, instance, validated_data):
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        return super().update(instance, validated_data)

class StaffDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffDocument
        fields = '__all__'

class CollectionFormSerializer(serializers.ModelSerializer):
    assigned_staff_name = serializers.ReadOnlyField(source='assigned_staff.name')
    
    class Meta:
        model = CollectionForm
        fields = '__all__'
        extra_kwargs = {
            'email': {'validators': []}, 
        }

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
        
        # If extra_data already exists in input, merge it
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

    def validate(self, attrs):
        # If status is being updated and is NOT 'Follow Up', clear the date
        if 'status' in attrs and attrs['status'] != 'Follow Up':
            attrs['follow_up_date'] = None
        return attrs


class EnquirySerializer(serializers.ModelSerializer):
    assigned_staff_name = serializers.ReadOnlyField(source='assigned_staff.name')

    class Meta:
        model = Enquiry
        fields = '__all__'

    def validate(self, attrs):
        # If status is being updated and is NOT 'Follow Up', clear the date
        if 'status' in attrs and attrs['status'] != 'Follow Up':
            attrs['follow_up_date'] = None
        return attrs
