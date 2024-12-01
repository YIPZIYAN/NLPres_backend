import csv
import json
import zipfile
from io import BytesIO, TextIOWrapper, StringIO

from rest_framework import serializers


class ConverterSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
    )
    file_format = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv'])
    export_as = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv'])

    def save(self):
        files = self.validated_data['files']
        file_format = self.validated_data['file_format']
        export_as = self.validated_data['export_as']

        process_method = getattr(self, f"process_{file_format}", None)
        if not callable(process_method):
            raise serializers.ValidationError(f"No processor available for file format: {file_format}")

        return process_method(files, export_as)

    # File Processors
    def process_txt(self, files, export_as):
        return self.process_files(files, export_as, file_reader=self.read_txt)

    def process_json(self, files, export_as):
        return self.process_files(files, export_as, file_reader=self.read_json)

    def process_jsonl(self, files, export_as):
        return self.process_files(files, export_as, file_reader=self.read_jsonl)

    def process_csv(self, files, export_as):
        return self.process_files(files, export_as, file_reader=self.read_csv)

    def process_files(self, files, export_as, file_reader):
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            for file in files:
                try:
                    content = file_reader(file)
                    converted_content = self.convert(content, export_as)
                    filename = f"{file.name.split('.')[0]}.{export_as}"
                    zip_file.writestr(filename, converted_content)
                except Exception as e:
                    raise serializers.ValidationError(f"{file.name}: {str(e)}")
        zip_buffer.seek(0)
        return zip_buffer, 'application/zip'

    def convert(self, content, export_as):
        convert_method = getattr(self, f"to_{export_as}", None)
        if not callable(convert_method):
            raise ValueError(f"Unsupported export format: {export_as}")

        return convert_method(content)

    # File Readers
    def read_txt(self, file):
        content = file.read().decode('utf-8')
        return [{"text": line.strip()} for line in content.splitlines() if line.strip()]

    def read_json(self, file):
        return json.load(file)

    def read_jsonl(self, file):
        return [json.loads(line) for line in file.read().decode('utf-8').splitlines()]

    def read_csv(self, file):
        return list(csv.DictReader(file.read().decode('utf-8').splitlines()))

    # File Exporters
    def to_json(self, content):
        return json.dumps(content, indent=2).encode('utf-8')

    def to_jsonl(self, content):
        return "\n".join(json.dumps(item) for item in content).encode('utf-8')

    def to_csv(self, content):
        flattened_content = []
        for item in content:
            flattened_item = {}
            for key, value in item.items():
                if isinstance(value, list):
                    flattened_item[key] = ", ".join(value)
                else:
                    flattened_item[key] = value
            flattened_content.append(flattened_item)

        output = StringIO()
        fieldnames = flattened_content[0].keys() if flattened_content else []
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flattened_content)

        return output.getvalue().encode('utf-8')
