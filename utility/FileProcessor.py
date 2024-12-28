import csv
import io
import json
from collections import defaultdict
from importlib.metadata import metadata
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
                max_length = max(len(value) for value in data.values())
                normalized_data = {key: value + [""] * (max_length - len(value)) for key, value in data.items()}
                return [dict(zip(normalized_data.keys(), values)) for values in zip(*normalized_data.values())]
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
                if value is not None:
                    value = value.strip()
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

        if not data:
            raise ValueError("The file is empty")

        return data

    def read_conllu(self, file):
        data = io.StringIO(file.read().decode("utf-8"))
        sentences = []

        for token_list in parse_incr(data):
            words = []
            tokens_data = []
            metadata = token_list.metadata
            sentiment_label = metadata.get("sentiment_label", None)

            for token in token_list:
                token_data = {
                    "id": token.get("id"),
                    "form": token.get("form"),
                    "lemma": token.get("lemma"),
                    "upostag": token.get("upostag"),
                    "xpostag": token.get("xpostag"),
                    "feats": token.get("feats"),
                    "head": token.get("head"),
                    "deprel": token.get("deprel"),
                    "deps": token.get("deps"),
                    "misc": token.get("misc"),
                }
                tokens_data.append(token_data)

                form = token["form"]
                misc = token.get("misc")
                words.append(form)
                if misc is None or misc.get("SpaceAfter") != "No":
                    words.append(" ")

            sentence = "".join(words).strip()
            if sentence:
                text = {"text": sentence,
                        "tokens": tokens_data}
                if sentiment_label:
                    text["label"] = sentiment_label
                sentences.append(text)


        if not sentences:
            raise ValueError("The file is empty")

        return sentences

    # File Generator
    def to_json(self, content):
        if not content:
            raise ValueError("The exported file is empty")

        return json.dumps(content, indent=2).encode('utf-8')

    def to_jsonl(self, content):
        if not content:
            raise ValueError("The exported file is empty")

        return "\n".join(json.dumps(item) for item in content).encode('utf-8')

    def to_csv(self, content, sequential=False):
        print(content)
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

        # For sequence labelling export
        if sequential:
            sentence_count = 1
            # print(content)
            # headers = content[0].keys()
            # flattened_content = content
            for line_number, document in enumerate(content, start=1):
                text = document.get("text", "")
                labels = sorted(document.get("label", None), key=lambda x: (x[0], x[1]))
                tokens = []
                idx = 0

                prev_end = -1

                for label in labels:
                    start, end, label_name = label

                    if start < 0 or end > len(text):
                        raise ValueError(f"Line {line_number} label index out of bounds")

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

                first_token = True
                for token in tokens:
                    flattened_content.append({
                        "Sentence": f"Sentence: {sentence_count}" if first_token else "",
                        "Word": token["form"],
                        "Label": token["upostag"]
                    })
                    first_token = False
                sentence_count += 1

            headers = ["Sentence", "Word", "Label"]

        # Other case
        else:
            flattened_content = [flatten_json(item) for item in content]

            for item in flattened_content:
                for key in item.keys():
                    if key not in headers:
                        headers.append(key)

        if not flattened_content:
            raise ValueError("The exported file is empty")

        output = StringIO()
        csv_writer = csv.DictWriter(output, fieldnames=headers)
        csv_writer.writeheader()
        csv_writer.writerows(flattened_content)

        return output.getvalue().encode('utf-8')


    def to_conllu(self, content):
        serialized_sentences = []

        for line_number, document in enumerate(content, start=1):
            tokens = []
            idx = 1
            metadata = {}

            # Case 1 if token exists
            if "tokens" in document:
                token_data = document.get("tokens", [])
                for token in token_data:
                    if isinstance(token, dict):
                        id = token.get("id", "_")
                        form = token.get("form", "_")
                        lemma = token.get("lemma", "_")
                        upostag = token.get("upostag", "_")
                        xpostag = token.get("xpostag", "_")
                        head = token.get("head", 0)
                        deprel = token.get("deprel", "_")
                        deps = token.get("deps", "_")
                        misc = token.get("misc", "_")

                        idx, token = self.create_token(idx, form, upostag, lemma, xpostag, head, deprel, deps, misc)
                        tokens.append(token)

                    else:
                        raise ValueError(f"Line {line_number} invalid token format")

                if "text" in document:
                    metadata["text"] = document["text"]

                if "label" in document:
                    metadata["sentiment_label"] = document["label"]

            # Case 2: if no token, check text and label
            elif "text" in document:

                text = document.get("text")
                labels = document.get("label", None)

                if text is "" or not isinstance(text, str):
                    continue

                metadata["text"] = text

                if isinstance(labels, str):
                    if labels:
                        metadata["sentiment_label"] = labels
                    for word in text.split():
                        idx, token = self.create_token(idx, word, "_")
                        tokens.append(token)

                elif isinstance(labels, list):

                    labels = sorted(labels, key=lambda x: (x[0], x[1]))
                    prev_end = -1

                    for label in labels:
                        start, end, label_name = label

                        if start < 0 or end > len(text):
                            raise ValueError(f"Line {line_number} label index out of bounds")

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
                else:
                    for word in text.split():
                        idx, token = self.create_token(idx, word, "_")
                        tokens.append(token)

            # Case 3: no token and text, skip it
            else:
                continue
                # raise ValueError(f"Line {line_number} missing required keys 'text' or 'token'")

            sentence = TokenList(tokens, metadata=Metadata(metadata))
            serialized_sentences.append(sentence.serialize())

        if not serialized_sentences:
            raise ValueError("The exported file is empty")

        return "".join(serialized_sentences).encode("utf-8")

    def create_token(self, idx, word, token_label, lemma="_", xpostag="_", feats="_", head=0, deprel="_", deps="_", misc="_"):
        token = {
            "id": idx,
            "form": word,
            "lemma": word.lower() if lemma == "_" else lemma,
            "upostag": token_label,
            "xpostag": xpostag,
            "feats": feats,
            "head": head,
            "deprel": deprel,
            "deps": deps,
            "misc": misc
        }
        idx += 1
        return idx, token

    def add_tokens(self, idx, tokens, segment, token_label="_"):
        for word in segment.split():
            idx, token = self.create_token(idx, word, token_label)
            tokens.append(token)

        return idx, tokens



