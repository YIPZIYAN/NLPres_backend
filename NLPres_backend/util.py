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
