import csv
import io
import json
from conllu import parse_incr
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from annotation.serializers import AnnotationSerializer
from document.models import Document, Annotation
from utility.FileProcessor import FileProcessor
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

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance

class ExportDocumentSerializer(serializers.Serializer, FileProcessor):
    export_as = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv'])
    annotated_only = serializers.BooleanField()

    def save(self):
        export_as = self.validated_data['export_as']
        annotated_only = self.validated_data['annotated_only']
        project = get_object_or_404(Project, pk=self.context.get('project_id'))
        user = self.context['request'].user
        documents = Document.objects.filter(project=project)
        if annotated_only:
            documents = documents.filter(annotation__user=user)

        documents_data = [
            {'text': document["text"], 'label': document.pop('annotation__label__name')}
            for document in documents.values("text", "annotation__label__name")
        ]

        return self.convert(documents_data, export_as), 'application/octet-stream'

class ImportDocumentSerializer(serializers.Serializer, FileProcessor):
    files = serializers.ListField(
        child=serializers.FileField(),
    )
    file_format = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv', 'conllu'])
    key = serializers.CharField(required=False, allow_null=True)

    def create(self, validated_data):
        files = validated_data['files']
        file_format = self.validated_data['file_format']
        key = validated_data['key']
        project = get_object_or_404(Project, id=self.context.get('project_id'))

        process_method = getattr(self, f"process_{file_format}", None)
        if not callable(process_method):
            raise serializers.ValidationError(f"No processor available for file format: {file_format}")

        created_documents, file_errors = process_method(files, project, key)

        if created_documents:
            message = f"{len(created_documents)} data imported successfully from {len(files)} file(s)."
            return {
                "message": message,
                "objects": [
                    {"id": doc.id, "text": doc.text} for doc in created_documents
                ],
                "errors": file_errors
            }

        return {"errors": file_errors}

    def update(self, instance, validated_data):
        return instance

    def process_files(self, files, file_reader, key, project):
        created_documents = []
        file_errors = []

        for file in files:
            try:
                lines, errors = self.read_file(file, file_reader, key)
                documents = [Document(project=project, text=line) for line in lines]
                Document.objects.bulk_create(documents)

                created_documents.extend(documents)
                file_errors.extend(errors)

            except serializers.ValidationError as e:
                file_errors.append({file.name: e.detail})

    def read_file(self, file, file_reader, key):
        lines = []
        errors = []
        try:
            data = file_reader(file)
            if not data:
                errors.append({file.name: "The file is empty"})
                return lines, errors

            for line_number, item in enumerate(data, start=1):
                if isinstance(item, dict):
                    value = item.get(key)
                    if value:
                        lines.append(value)
                    else:
                        errors.append({file.name: f"Line {line_number}: No data found for the key '{key}'"})
                else:
                    errors.append({file.name: f"Line {line_number}: Key '{key}' not found"})

        except (json.JSONDecodeError, csv.Error) as e:
            errors.append({file.name: f"{str(e)}"})

        return lines, errors

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

    def process_json(self, files, project, key):
        return self.process_files(files, file_reader=self.read_json, key=key, project=project)

    def process_jsonl(self, files, project, key):
        return self.process_files(files, file_reader=self.read_jsonl, key=key, project=project)

    def process_csv(self, files, project, key):
        return self.process_files(files, file_reader=self.read_csv, key=key, project=project)

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
