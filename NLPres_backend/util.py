from document.models import Document


def calculate_progress(user, project):
    documents = Document.objects.filter(project=project)
    total_count = documents.count()
    completed_count = documents.filter(annotation__isnull=False, annotation__user=user).distinct().count()
    pending_count = total_count - completed_count

    return {
        'total': total_count,
        'completed': completed_count,
        'pending': pending_count,
    }

def unflatten(list_of_str):
    return [labels.split(" ") for labels in list_of_str]

def flatten(list_of_list_of_str):
    return [label for label_list in list_of_list_of_str for label in label_list]

def compute_ratings_matrix(categories, data):
    ratings_matrix = []
    for item in data:
        counts = [item.count(category) for category in categories]
        ratings_matrix.append(counts)
    return ratings_matrix