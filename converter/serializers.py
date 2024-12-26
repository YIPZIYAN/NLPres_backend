import zipfile
from io import BytesIO
from rest_framework import serializers
from utility.FileProcessor import FileProcessor


class ConverterSerializer(serializers.Serializer, FileProcessor):
    files = serializers.ListField(
        child=serializers.FileField(),
    )
    file_format = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv', 'conllu'])
    export_as = serializers.ChoiceField(choices=['txt', 'json', 'jsonl', 'csv', 'conllu'])

    def save(self):
        files = self.validated_data['files']
        file_format = self.validated_data['file_format']
        export_as = self.validated_data['export_as']

        file_reader = getattr(self, f"read_{file_format}", None)
        if not callable(file_reader):
            raise serializers.ValidationError(f"No reader available for file format: {file_format}")

        return self.process_files(files, export_as, file_reader)


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






