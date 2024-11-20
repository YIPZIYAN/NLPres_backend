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
    key = serializers.CharField(required=False, allow_null=True)

    def create_document(self, project, lines):
        documents = [Document(project=project, text=line) for line in lines]
        Document.objects.bulk_create(documents)
        return documents

    def process_txt(self, file, project):
        lines = [line.decode('utf-8').strip() for line in file.readlines()]
        return self.create_document(project, lines)

    def process_json(self, file, project, key):

        if key is None:
            raise serializers.ValidationError({"error": ["Please fill in the key of data to be imported."]})

        try:
            data = json.load(file)
        except json.JSONDecodeError as e:
            raise serializers.ValidationError({"error": [f"Invalid JSON file ({file.name}): {str(e)}"]})

        if isinstance(data, list):
            lines = [
                item.get(key) for item in data
                if isinstance(item, dict) and item.get(key) is not None
            ]
        elif isinstance(data, dict):
            lines = [data.get(key)] if data.get(key) is not None else []
        else:
            raise serializers.ValidationError({"error": [f"{file.name}: JSON must be an object or an array of objects."]})

        if not lines:
            raise serializers.ValidationError({"error": [f"No data found for the key '{key}' in the JSON file(s)."]})

        # lines = data if isinstance(data, list) else [data]
        return self.create_document(project, lines)

    def create(self, validated_data):
        files = validated_data['files']
        project = validated_data['project_id']
        key = validated_data['key']
        created_documents = []
        errors = []

        file_formats = {
            '.txt': self.process_txt,
            '.json': partial(self.process_json, key=key)
        }

        for file in files:
            file_name = file.name.lower()

            for extension, method in file_formats.items():
                if file_name.endswith(extension):
                    try:
                        documents = method(file, project)
                        created_documents.extend(documents)
                    except serializers.ValidationError as e:
                        errors.append({file.name: e.detail})
                    break

            else:
                raise serializers.ValidationError("Unsupported file format.")

        if created_documents:
            message = f"{len(created_documents)} data imported successfully from {len(files)} file(s)."
            if errors:
                message += f" File(s) with error have been ignored."
            response = {
                "message": message,
                "created_documents": [
                    {"id": doc.id, "text": doc.text} for doc in created_documents
                ]
            }
        else:
            first_error = next(iter(errors[0].values()))
            error = first_error.get("error")[0]
            raise serializers.ValidationError({"error": [error]})

        return response

    def update(self, instance, validated_data):
        return instance
