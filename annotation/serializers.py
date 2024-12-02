from rest_framework import serializers

from document.models import Annotation
from label.serializers import LabelSerializer
from userprofile.serializers import UserSerializer


class AnnotationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = UserSerializer(read_only=True)
    label = LabelSerializer(read_only=True)
    start = serializers.IntegerField(allow_null=True, required=False)
    end = serializers.IntegerField(allow_null=True, required=False)

    class Meta:
        model = Annotation
        fields = '__all__'