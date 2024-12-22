from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from document.models import Annotation, Document
from label.models import Label
from label.serializers import LabelSerializer
from userprofile.serializers import UserSerializer


class AnnotationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    user = UserSerializer(read_only=True)
    label = LabelSerializer(read_only=True)
    start = serializers.IntegerField(allow_null=True, required=False)
    end = serializers.IntegerField(allow_null=True, required=False)
    label_id = serializers.IntegerField(write_only=True, required=True)
    document_id = serializers.IntegerField(write_only=True, required=False,allow_null=True)
    document = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Annotation
        fields = '__all__'

    def create(self, validated_data):
        label = get_object_or_404(Label, pk=validated_data['label_id'])
        document = get_object_or_404(Document, pk=validated_data['document_id'])
        return Annotation.objects.create(label=label, document=document, user=self.context['request'].user,
                                     **validated_data)

    def update(self, instance, validated_data):

        try:
            label = Label.objects.get(id=validated_data['label_id'])
        except Label.DoesNotExist:
            raise serializers.ValidationError({'label_id': 'Invalid label ID'})

        instance.label = label
        instance.save()
        return instance
