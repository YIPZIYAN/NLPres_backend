import csv
import json
from lib2to3.fixes.fix_input import context

from django.shortcuts import get_object_or_404
from rest_framework import serializers
from document.models import Document, Annotation
from enums.ProjectCategory import ProjectCategory
from label.serializers import LabelSerializer
from utility.FileProcessor import FileProcessor
from project.models import Project

class DocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    text = serializers.CharField(required=True)
    annotations = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Document
        fields = '__all__'


    def create(self, validated_data):
        return Document.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.text = validated_data.get('text', instance.text)
        instance.save()
        return instance

    def get_annotations(self, obj):
        request = self.context.get('request')
        if not request or not request.user:
            return None

        user_annotations = obj.annotation_set.filter(user_id=request.user.id)
        if user_annotations:
            return MyAnnotationSerializer(user_annotations, many=True).data
        return None

class MyAnnotationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    label = LabelSerializer(read_only=True)
    start = serializers.IntegerField(read_only=True)
    end = serializers.IntegerField(read_only=True)

    class Meta:
        model = Annotation
        fields = ['id', 'label', 'start', 'end']

class ExportDocumentSerializer(serializers.Serializer, FileProcessor):
    export_as = serializers.ChoiceField(choices=['json', 'jsonl', 'csv', 'conllu'])
    annotated_only = serializers.BooleanField()

    def save(self):
        export_as = self.validated_data['export_as']
        annotated_only = self.validated_data['annotated_only']
        project = get_object_or_404(Project, pk=self.context.get('project_id'))
        user = self.context['request'].user
        documents = Document.objects.filter(project=project)
        if annotated_only:
            documents = documents.filter(annotation__user=user).distinct()

        documents_data = []
        match project.category:
            case ProjectCategory.CLASSIFICATION.value:
                documents_data = [
                    {'text': document["text"], 'label': document.pop('annotation__label__name')}
                    for document in documents.values("text", "annotation__label__name")
                ]

            case ProjectCategory.SEQUENTIAL.value:
                documents_data = []
                print(documents)
                for document in documents:
                    annotations = Annotation.objects.filter(document=document, user=user)
                    annotations = sorted(annotations, key=lambda x: (x.start, x.end))
                    all_label = [
                        [annotation.start, annotation.end, annotation.label.name] for annotation in annotations
                    ]

                    text = document.text
                    labels = all_label
                    tokens = []
                    idx = 0

                    prev_end = -1

                    for label in labels:
                        start, end, label_name = label

                        if start != (prev_end + 1):
                            segment = text[prev_end + 1: start]
                            prev_end = start - 1
                            idx, tokens = self.add_tokens(idx, tokens, segment)

                        word = text[start:end + 1] if (start == end) else text[start:end]
                        prev_end = end
                        idx, token = self.create_token(idx, word, label_name)
                        tokens.append(token)

                    if prev_end != len(text) - 1:
                        segment = text[prev_end + 1: len(text)]
                        idx, tokens = self.add_tokens(idx, tokens, segment)

                    documents_data.append({
                        "text": document.text,
                        "label": all_label,
                        "token": [token["form"] for token in tokens],
                        "labels": [token["upostag"] for token in tokens]
                    })


        if export_as == 'csv' and project.is_category(ProjectCategory.SEQUENTIAL):
            return self.convert(documents_data, export_as, sequential=True), 'application/octet-stream'

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

        file_reader = getattr(self, f"read_{file_format}", None)
        if not callable(file_reader):
            raise serializers.ValidationError(f"No reader available for file format: {file_format}")

        created_documents, file_errors = self.process_files(files, file_reader, key, project)

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
                lines, errors = self.validate_file_content(file, file_reader, key)
                documents = [Document(project=project, text=line) for line in lines]
                Document.objects.bulk_create(documents)

                created_documents.extend(documents)
                file_errors.extend(errors)

            except serializers.ValidationError as e:
                file_errors.append({file.name: e.detail})

        return created_documents, file_errors

    def validate_file_content(self, file, file_reader, key):
        lines = []
        errors = []
        try:
            data = file_reader(file)
            if not data:
                errors.append({file.name: "The file is empty"})
                return lines, errors

            for line_number, item in enumerate(data, start=1):
                if isinstance(item, dict): # txt, json, jsonl, csv
                    value = item.get(key)
                    if value:
                        lines.append(value)
                    else:
                        errors.append({file.name: f"Line {line_number}: No data found for the key '{key}'"})

                elif isinstance(item, str): # conllu
                    if item:
                        lines.append(item)
                    else:
                        errors.append({file.name: f"Line {line_number}: Invalid data"})

                else:
                    errors.append({file.name: f"Line {line_number}: Key '{key}' not found"})

        except (json.JSONDecodeError, csv.Error, Exception) as e:
            errors.append({file.name: f"{str(e)}"})

        return lines, errors

