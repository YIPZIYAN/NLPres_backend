import json
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from label.models import Label
from project.models import Project
from utility.FileProcessor import FileProcessor


class LabelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=100)
    color = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = Label
        fields = ['id', 'name', 'color']

    def create(self, validated_data):
        project_id = self.context.get('project_id')
        if not project_id:
            raise serializers.ValidationError({"project_id": "This field is required."})

        project = get_object_or_404(Project, id=project_id)
        return Label.objects.create(project=project, **validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.color = validated_data.get('color', instance.color)
        instance.save()
        return instance

class ExportLabelSerializer(serializers.Serializer, FileProcessor):

    def save(self):
        project = get_object_or_404(Project, pk=self.context.get('project_id'))
        labels = Label.objects.filter(project=project)

        labels_data = [
            {'name': label["name"], 'color': label["color"]}
            for label in labels.values("name", "color")
        ]

        return self.convert(labels_data, "json"), 'application/octet-stream'

class ImportLabelSerializer(serializers.Serializer, FileProcessor):
    files = serializers.ListField(child=serializers.FileField())

    def create(self, validated_data):
        files = validated_data['files']
        project = get_object_or_404(Project, id=self.context.get('project_id'))

        created_labels, file_errors = self.process_files(files, project)

        if created_labels:
            message = f"{len(created_labels)} label(s) imported successfully from {len(files)} file(s)."
            return {
                "message": message,
                "objects": [
                    {"name": label.name, "color": label.color} for label in created_labels
                ],
                "errors": file_errors
            }

        return {"errors": file_errors}

    def process_files(self, files, project):
        created_labels = []
        file_errors = []

        for file in files:
            try:
                lines, errors = self.validate_file_content(file)
                labels = [Label(project=project, name=line["name"], color=line["color"]) for line in lines]
                Label.objects.bulk_create(labels)

                created_labels.extend(labels)
                file_errors.extend(errors)

            except serializers.ValidationError as e:
                file_errors.append({file.name: e.detail})

        return created_labels, file_errors

    def validate_file_content(self, file):
        lines = []
        errors = []
        try:
            data = self.read_json(file)
            if not data:
                errors.append({file.name: "The file is empty"})
                return lines, errors

            for line_number, item in enumerate(data, start=1):
                if isinstance(item, dict):
                    name = item.get("name")
                    color = item.get("color")
                    if name and color:
                        lines.append({"name": name, "color": color})
                    else:
                        errors.append({file.name: f"Line {line_number}: No label name and color found"})
                else:
                    errors.append({file.name: f"Line {line_number}:No data found"})

        except json.JSONDecodeError as e:
            errors.append({file.name: f"{str(e)}"})

        return lines, errors