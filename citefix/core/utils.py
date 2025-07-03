import os
from django.conf import settings
from django.utils.crypto import get_random_string


def save_file(file, dir):
    if True:
        nom = os.path.splitext(file.name)[0]
        ext = os.path.splitext(file.name)[1]
        filename = f"{nom}_{get_random_string(8)}{ext}"
        path = os.path.join(settings.MEDIA_ROOT, dir, filename)

        # Crée le dossier s'il n'existe pas
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)
                
        return f"/media/{dir}/{filename}"
