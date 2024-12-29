import pickle
from django.shortcuts import get_object_or_404
from sklearn.metrics import precision_score, recall_score, f1_score, classification_report
from rest_framework import serializers
from comparison.models import Comparison
from enums.ProjectCategory import ProjectCategory
from project.models import Project
from utility.FileProcessor import FileProcessor


class ComparisonSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(required=True, max_length=100)
    models_name = serializers.JSONField(required=False)
    result = serializers.JSONField(required=False)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Comparison
        fields = ['id', 'name', 'models_name', 'result', 'updated_at']

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance


class CompareSerializer(serializers.Serializer, FileProcessor):
    first_model = serializers.FileField()
    second_model = serializers.FileField()
    category = serializers.CharField()
    file = serializers.FileField()
    file_format = serializers.ChoiceField(choices=['json', 'jsonl', 'csv'])
    x_test_key = serializers.CharField()
    y_test_key = serializers.CharField()

    def create(self, validated_data):
        project = get_object_or_404(Project, id=self.context.get('project_id'))
        first_model = validated_data["first_model"]
        second_model = validated_data["second_model"]
        category = validated_data["category"]
        x_test_key = validated_data["x_test_key"]
        y_test_key = validated_data["y_test_key"]
        file = validated_data["file"]
        file_format = validated_data['file_format']
        models = [first_model, second_model]

        file_reader = getattr(self, f"read_{file_format}", None)
        if not callable(file_reader):
            raise serializers.ValidationError(f"No reader available for file format: {file_format}")

        x_test, y_test, errors = self.process_file(file, file_reader, x_test_key, y_test_key, category)

        if x_test and y_test:
            result = self.compare(models, x_test, y_test)
            print(result)
            name = f"Model Comparison of {first_model.name} and {second_model.name}"
            models_name = [first_model.name, second_model.name]
            Comparison.objects.create(project=project, name=name, models_name=models_name, result=result)
            return {
                "message": "Model evaluation report has generated.",
            }

        return {"errors": errors}

    def compare(self, models, x_test, y_test):

        result = []
        for model_file in models:
            try:
                model = pickle.load(model_file)
                y_pred = model.predict(x_test)

                report = classification_report(y_test, y_pred, output_dict=True)

                precision_micro = precision_score(y_test, y_pred, average='micro')
                recall_micro = recall_score(y_test, y_pred, average='micro')
                f1_micro = f1_score(y_test, y_pred, average='micro')

                report["micro avg"] = {
                    "precision": precision_micro,
                    "recall": recall_micro,
                    "f1-score": f1_micro,
                    "support": float(len(y_test))
                }

                sorted_report = {k: report[k] for k in sorted(report.keys())}

                result.append(sorted_report)
            except Exception as e:
                raise serializers.ValidationError({"errors": f"Model {model_file.name} cannot be processed: {str(e)}"})

        return {"objects": result}


    def process_file(self, file, file_reader, x_test_key, y_test_key, category):
        x_test = []
        y_test = []
        x_data = []
        y_data = []
        errors = []

        try:
            dataset = file_reader(file)
            print(dataset)
            if not dataset:
                errors.append({file.name: "The file is empty"})
                return x_test, y_test, errors

            match category:
                case ProjectCategory.CLASSIFICATION.value:
                    for line_number, data in enumerate(dataset, start=1):
                        x_test_value = data.get(x_test_key, None)
                        y_test_value = data.get(y_test_key, None)

                        if not x_test_value or not y_test_value:
                            errors.append({file.name: f"Line {line_number}: No data found for the key '{x_test_key}' and '{y_test_key}'"})
                            return x_test, y_test, errors

                        if isinstance(x_test_value, str) and isinstance(y_test_value, str):
                            x_test.append(x_test_value)
                            y_test.append(y_test_value)

                        else:
                            errors.append({file.name: f"Line {line_number}: The key '{x_test_key}' or '{y_test_key}' format is unsupported"})

                case ProjectCategory.SEQUENTIAL.value:
                    for line_number, data in enumerate(dataset, start=1):
                        x_test_value = data.get(x_test_key, None)
                        y_test_value = data.get(y_test_key, None)

                        if not x_test_value or not y_test_value:
                            errors.append(
                                {file.name: f"Line {line_number}: No data found for the key '{x_test_key}' and '{y_test_key}'"})
                            return x_test, y_test, errors

                        if isinstance(x_test_value, list) and isinstance(y_test_value, list):
                            x_data.append(x_test_value)
                            y_data.append(y_test_value)

                        else:
                            errors.append({file.name: f"Line {line_number}: The key '{x_test_key}' or '{y_test_key}' format is unsupported"})

                    x_test = [token for tokens in x_data for token in tokens]
                    y_test = [label for labels in y_data for label in labels]


        except Exception as e:
            errors.append({file.name: f"{str(e)}"})

        return x_test, y_test, errors

