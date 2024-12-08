import csv
import json
import zipfile
from collections import defaultdict, OrderedDict
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
        data = json.load(file)

        # Case 1: If the data is column-oriented JSON (keys are arrays)
        if isinstance(data, dict):
            # Check if the values of the dictionary are lists (column-oriented format)
            if all(isinstance(value, list) for value in data.values()):
                return [dict(zip(data.keys(), values)) for values in zip(*data.values())]
            # If not a column-oriented JSON, it's just a simple dictionary that needs no transformation
            return [data]

        # Case 2: If the data has a top-level "data" key, extract the list
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    return value

        if isinstance(data, list):
            return data

        raise ValueError("Unsupported JSON format")

    def read_jsonl(self, file):
        return [json.loads(line) for line in file.read().decode('utf-8').splitlines()]

    def read_csv(self, file):
        content = csv.DictReader(file.read().decode('utf-8').splitlines())
        data = []

        for row in content:
            reconstructed_row = defaultdict(dict)

            for key, value in row.items():
                if value.isdigit():
                    value = int(value)
                elif value.replace('.', '', 1).isdigit():
                    value = float(value)

                # Reconstruct nested structures
                keys = key.split('/')
                temp = reconstructed_row
                for part in keys[:-1]:
                    temp = temp.setdefault(part, {})
                temp[keys[-1]] = value

            def process_lists(obj):
                if isinstance(obj, dict):
                    keys = list(obj.keys())
                    if all(k.isdigit() for k in keys):
                        return [process_lists(obj[k]) for k in sorted(obj, key=int)]
                    else:
                        return {k: process_lists(v) for k, v in obj.items()}
                return obj

            data.append(process_lists(reconstructed_row))

        return data

    # File Exporters
    def to_json(self, content):
        return json.dumps(content, indent=2).encode('utf-8')

    def to_jsonl(self, content):
        return "\n".join(json.dumps(item) for item in content).encode('utf-8')

    def to_csv(self, content):

        def flatten_json(json_obj, parent_key='', sep='/'):
            items = []
            if isinstance(json_obj, list):
                # if all (isinstance(value, dict) for value in json_obj):
                #     for value in json_obj:
                #         items.extend(flatten_json(value, parent_key).items())
                # else:
                if len(json_obj) == 0:  # Handle empty lists
                    items.append((parent_key, ''))
                else:
                    for i, value in enumerate(json_obj):
                        items.extend(flatten_json(value, f"{parent_key}{sep}{i}").items())
            elif isinstance(json_obj, dict):
                for key, value in json_obj.items():
                    new_key = f"{parent_key}{sep}{key}" if parent_key else key
                    if isinstance(value, (dict, list)):
                        items.extend(flatten_json(value, new_key, sep=sep).items())
                    else:
                        items.append((new_key, value if value is not None else ''))
            else:
                items.append((parent_key, json_obj if json_obj is not None else ''))
            return dict(items)

        flattened_content = [flatten_json(item) for item in content]

        headers = []
        for item in flattened_content:
            for key in item.keys():
                if key not in headers:
                    headers.append(key)

        output = StringIO()
        csv_writer = csv.DictWriter(output, fieldnames=headers)
        csv_writer.writeheader()
        csv_writer.writerows(flattened_content)

        return output.getvalue().encode('utf-8')


