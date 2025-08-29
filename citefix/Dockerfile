# Utilise une image Python légère
FROM python:3.12-slim

# Ne pas créer de fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Crée le dossier de travail dans le conteneur
WORKDIR /app

# Copie et installe les dépendances
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copie tout le code du projet
COPY . .

RUN python manage.py collectstatic --noinput


# Commande de démarrage
CMD ["gunicorn", "citefix.wsgi:application", "--bind", "0.0.0.0:8000"]
