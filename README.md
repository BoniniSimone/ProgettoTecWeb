# Cinepiù – Progetto Django

Applicazione web per la gestione di film, proiezioni e prenotazioni di biglietti.

## Requisiti
- Python 3.10+
- pip
- Virtual environment 

## Setup rapido
```bash
python -m venv venv
source venv/bin/activate     
pip install -r requirements.txt

python manage.py makemigrations
python manage.py migrate

python manage.py seed_data --reset

python manage.py runserver

