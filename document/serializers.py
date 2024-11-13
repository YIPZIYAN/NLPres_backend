import json
from functools import partial

from rest_framework import serializers
from document.models import Document
from project.models import Project


class DocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    text = serializers.CharField()
    is_completed = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    project_id = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    class Meta:
        model = Document
        fields = '__all__'


class ImportDocumentSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
    )
    project_id = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    def create_document(self, project, lines):
        documents = [Document(project=project, text=line) for line in lines]
        Document.objects.bulk_create(documents)
        return documents

    def process_txt(self, file, project):
        lines = [line.decode('utf-8').strip() for line in file.readlines()]
        return self.create_document(project, lines)

    def process_json(self, file, project):
        data = json.load(file)
        lines = data if isinstance(data, list) else [data]
        return self.create_document(project, lines)

    def create(self, validated_data):
        files = validated_data['files']
        project = validated_data['project_id']
        created_documents = []

        for file in files:
            file_name = file.name.lower()
            file_formats = {
                '.txt': partial(self.process_txt),
                '.json': partial(self.process_json),
            }

            for extension, method in file_formats.items():
                if file_name.endswith(extension):
                    documents = method(file, project)
                    created_documents.extend(documents)
                    break

                else:
                    raise serializers.ValidationError("Unsupported file format.")

        message = f"{len(created_documents)} data imported successfully from {len(files)} files."
        response = {
            "message": message,
            "created_documents": [
                {"id": doc.id, "text": doc.text} for doc in created_documents
            ],
        }
        return response



    def update(self, instance, validated_data):
        return instance
