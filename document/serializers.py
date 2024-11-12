import json
from functools import partial

from rest_framework import serializers
from document.models import Document
from project.models import Project


class DocumentSerializer(serializers.Serializer):
    file = serializers.FileField()
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
        file = validated_data['file']
        project = validated_data['project_id']
        file_name = file.name.lower()

        file_formats = {
            '.txt': partial(self.process_txt),
            '.json': partial(self.process_json),
        }

        for extension, method in file_formats.items():
            if file_name.endswith(extension):
                created_documents = method(file, project)
                message = f"{len(created_documents)} data imported from {file_name} successfully."
                response = {
                    "message": message,
                    "created_documents": [
                        {"id": doc.id, "text": doc.text} for doc in created_documents
                    ],
                }
                return response

        raise serializers.ValidationError("Unsupported file format.")

    def update(self, instance, validated_data):
        return instance
