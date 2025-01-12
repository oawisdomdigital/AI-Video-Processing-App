from rest_framework import serializers
from .models import UploadedVideo

class UploadedVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedVideo
        fields = '__all__'  # Ensure all fields in the model are included
