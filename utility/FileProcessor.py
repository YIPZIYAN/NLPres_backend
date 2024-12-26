import csv
import io
import json
from collections import defaultdict
from io import StringIO
from conllu import parse_incr, TokenList, Token, Metadata


class FileProcessor:

    def convert(self, content, export_as, sequential=False):
        convert_method = getattr(self, f"to_{export_as}", None)
        if not callable(convert_method):
            raise ValueError(f"Unsupported export format: {export_as}")

        if export_as == "csv":
            return convert_method(content, sequential)

        return convert_method(content)

    # File Readers
    def read_txt(self, file):
        content = file.read().decode('utf-8')
        return [{"text": line.strip()} for line in content.splitlines() if line.strip()]

    def read_jsonl(self, file):
        return [json.loads(line) for line in file.read().decode('utf-8').splitlines()]

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

    def read_csv(self, file):
        content = file.read().decode('utf-8')
        delimiter = csv.Sniffer().sniff(content.splitlines()[0]).delimiter
        csv_reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
        data = []

        for row in csv_reader:
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

    def read_conllu(self, file):
        data = io.StringIO(file.read().decode("utf-8"))
        sentences = []

        for token_list in parse_incr(data):
            words = []
            for token in token_list:
                form = token["form"]
                misc = token.get("misc")
                words.append(form)
                if misc is None or misc.get("SpaceAfter") != "No":
                    words.append(" ")
            sentence = "".join(words).strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    # File Generator
    def to_json(self, content):
        return json.dumps(content, indent=2).encode('utf-8')

    def to_jsonl(self, content):
        return "\n".join(json.dumps(item) for item in content).encode('utf-8')

    def to_csv(self, content, sequential=False):

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

        headers = []
        flattened_content = []
        if sequential:
            headers = content[0].keys()
            flattened_content = content

        else:
            flattened_content = [flatten_json(item) for item in content]

            for item in flattened_content:
                for key in item.keys():
                    if key not in headers:
                        headers.append(key)


        output = StringIO()
        csv_writer = csv.DictWriter(output, fieldnames=headers)
        csv_writer.writeheader()
        csv_writer.writerows(flattened_content)

        return output.getvalue().encode('utf-8')


    def to_conllu(self, content):

        def create_token(word, token_label):
            nonlocal idx
            token = {
                "id": idx,
                "form": word,
                "lemma": word.lower(),
                "upostag": token_label,
                "xpostag": "_",
                "feats": "_",
                "head": 0,
                "deprel": "_",
                "deps": "_",
                "misc": "_"
            }
            idx += 1
            return token

        def add_tokens(segment, token_label="O"):
            for word in segment.split():
                tokens.append(create_token(word, token_label))

        serialized_sentences = []

        for document in content:
            text = document.get("text", "")
            labels = sorted(document.get("label", []), key=lambda x: (x[0], x[1]))
            tokens = []
            prev_end = -1
            idx = 1

            for label in labels:
                start, end, label_name = label
                if start != (prev_end + 1):
                    segment = text[prev_end + 1: start]
                    prev_end = start - 1
                    add_tokens(segment)

                word = text[start:end + 1] if (start == end) else text[start:end]
                prev_end = end
                tokens.append(create_token(word, label_name))

            if prev_end != len(text) - 1:
                segment = text[prev_end + 1: len(text)]
                add_tokens(segment)

            metadata = Metadata({"text": text})
            sentence = TokenList(tokens, metadata=metadata)
            serialized_sentences.append(sentence.serialize())

        return "".join(serialized_sentences).encode("utf-8")



