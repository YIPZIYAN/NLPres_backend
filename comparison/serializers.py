import pickle
from sklearn.metrics import accuracy_score
from rest_framework import serializers
from utility.FileProcessor import FileProcessor


class ComparisonSerializer(serializers.Serializer, FileProcessor):
    first_model = serializers.FileField()
    second_model = serializers.FileField()
    file = serializers.FileField()
    file_format = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv', 'conllu'])
    x_test_key = serializers.CharField()
    y_test_key = serializers.CharField()

    def save(self):
        first_model = self.validated_data["first_model"]
        second_model = self.validated_data["second_model"]
        x_test_key = self.validated_data["x_test_key"]
        y_test_key = self.validated_data["y_test_key"]
        file = self.validated_data["file"]
        file_format = self.validated_data['file_format']
        models = [first_model, second_model]

        file_reader = getattr(self, f"read_{file_format}", None)
        if not callable(file_reader):
            raise serializers.ValidationError(f"No reader available for file format: {file_format}")

        x_test, y_test = self.process_file(file, file_reader, x_test_key, y_test_key)

        return self.compare(models, x_test, y_test)

    def compare(self, models, x_test, y_test):
        result = []
        for model_file in models:
            model = pickle.load(model_file)
            y_pred = model.predict(x_test)
            accuracy = accuracy_score(y_test, y_pred)
            result.append({"testing": accuracy})
            print(f"Accuracy: {accuracy}")

        return {"objects": result}

    def process_file(self, file, file_reader, x_test_key, y_test_key):
        x_test = []
        y_test = []
        try:
            dataset = file_reader(file)

            for line_number, data in enumerate(dataset, start=1):
                x_data = data.get(x_test_key)
                y_data = data.get(y_test_key)
                if x_data and y_data:
                    x_test.append(x_data)
                    y_test.append(y_data)

        except Exception as e:
            raise ValueError("hi")

        return x_test, y_test

