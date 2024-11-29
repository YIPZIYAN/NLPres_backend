import json

from rest_framework import serializers


class ConverterSerializer(serializers.Serializer):
    file = serializers.FileField()
    output_format = serializers.ChoiceField(choices=['json', 'jsonl', 'csv', 'conllu'])

    def process_file(self, file, output_format):
        try:
            content = file.read().decode('utf-8')
            if output_format == 'json':
                return json.dumps({"content": content.splitlines()}, indent=4), 'application/json'

        except Exception as e:
            raise serializers.ValidationError(f"Error during conversion: {str(e)}")

    def save(self):
        file = self.validated_data['file']
        output_format = self.validated_data['output_format']
        return self.process_file(file, output_format)