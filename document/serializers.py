import csv
import io
import json
from functools import partial
from conllu import parse_incr
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from annotation.serializers import AnnotationSerializer
from document.models import Document
from project.models import Project

class DocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    text = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    project_id = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    annotations = AnnotationSerializer(many=True,read_only=True,source='annotation_set')

    class Meta:
        model = Document
        fields = '__all__'


class ImportDocumentSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
    )
    file_format = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv', 'conllu'])
    key = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        files = validated_data['files']
        file_format = self.validated_data['file_format']
        project_id = self.context.get('project_id')
        key = validated_data['key']

        process_methods = {
            'txt': self.process_txt,
            'json': partial(self.process_json, key=key),
            'jsonl': partial(self.process_jsonl, key=key),
            'csv': partial(self.process_csv, key=key),
            'conllu': self.process_conllu,
        }

        if not project_id:
            raise serializers.ValidationError({"project_id": "This field is required."})

        project = get_object_or_404(Project, id=project_id)
        process_method = process_methods[file_format]
        created_documents = []
        errors = []

        for file in files:
            try:
                documents, file_errors = process_method(file, project)
                created_documents.extend(documents)
                errors.extend(file_errors)
            except serializers.ValidationError as e:
                errors.append({file.name: e.detail})

        if created_documents:
            message = f"{len(created_documents)} data imported successfully from {len(files)} file(s)."
            response = {
                "message": message,
                "objects": [
                    {"id": doc.id, "text": doc.text} for doc in created_documents
                ],
                "errors": errors
            }
        else:
            response = {
                "errors": errors
            }

        return response

    def update(self, instance, validated_data):
        return instance

    def process_txt(self, file, project):

        lines = []
        errors = []

        try:
            for line_number, line in enumerate(file, start=1):
                decoded_line = line.decode('utf-8').strip()
                if decoded_line:
                    lines.append(decoded_line)

            if not lines:
                errors.append({file.name: "No data found"})

        except UnicodeDecodeError as e:
            errors.append({file.name: f"{str(e)}"})

        return self.create_document(project, lines), errors

    def process_json(self, file, project, key):

        errors = []
        lines = []

        try:
            data = json.load(file)
            if isinstance(data, list):
                for line_number, item in enumerate(data, start=1):
                    if isinstance(item, dict) and item.get(key) is not None:
                        lines.append(item.get(key))
                    else:
                        errors.append({file.name: f"Line {line_number}: No data found for the key '{key}'"})
            elif isinstance(data, dict):
                value = data.get(key)
                if value is not None:
                    lines.append(value)
                else:
                    errors.append({file.name: f"No data found for the key '{key}'"})

            else:
                errors.append({file.name: "JSON must be an object or an array of objects"})

        except json.JSONDecodeError as e:
            errors.append({file.name: f"{str(e)}"})

        return self.create_document(project, lines), errors

    def process_jsonl(self, file, project, key):

        lines = []
        errors = []

        for line_number, line in enumerate(file, start=1):
            try:
                data = json.loads(line.decode('utf-8'))
                if isinstance(data, dict):
                    value = data.get(key)
                    if value is not None:
                        lines.append(value)
                    else:
                        errors.append({file.name: f"Line {line_number}: No data found for the key '{key}'"})

                else:
                    errors.append({file.name: f"Line {line_number}: Invalid JSON object"})

            except json.JSONDecodeError as e:
                errors.append({file.name: f"Line {line_number}: {str(e)}"})

        return self.create_document(project, lines), errors

    def process_csv(self, file, project, key):

        lines = []
        errors = []

        try:
            data = file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(data)

            if key not in reader.fieldnames:
                errors.append({file.name: f"Key '{key}' not found in CSV header"})
                return [], errors

            for line_number, row in enumerate(reader, start=2):
                value = row.get(key)
                if value:
                    lines.append(value)
                else:
                    errors.append({file.name: f"Line {line_number}: Invalid data"})

        except csv.Error as e:
            errors.append({file.name: f"{str(e)}"})

        return self.create_document(project, lines), errors

    def process_conllu(self, file, project):

        sentences = []
        errors = []

        try:
            data = io.StringIO(file.read().decode("utf-8"))
            for sentence_number, tokenlist in enumerate(parse_incr(data), start=1):
                sentence = " ".join([token["form"] for token in tokenlist if token.get("form")])
                if sentence:
                    sentences.append(sentence)
                else:
                    errors.append({file.name: f"Line {sentence_number}: Invalid data"})

        except Exception as e:
            errors.append({file.name: str(e)})

        return self.create_document(project, sentences), errors

    def create_document(self, project, lines):
        documents = [Document(project=project, text=line) for line in lines]
        Document.objects.bulk_create(documents)
        return documents
