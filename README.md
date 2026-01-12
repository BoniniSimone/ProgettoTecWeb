# Cinepiù – Progetto Django

Progetto univesitario che consiste nella realizzazione di un'applicazione web utlizzando il framwork "Django", che segue il paradigma "Model-Template-View".

L'applicazione da me realizzata si occupa della gestione di un cinema.
L'applicazione è pensata per essere usata da 5 tipologie di utenti:

Utenti esterni (clienti):
- Utente non registrato, che può solo consultare la programmazione e le informazioni sui film.
- Utente registrato, che oltre alle funzionalità dell'utente non registrato può prenotare il biglietto per la proiezione di un film e può lasciare una recensione.

Ogni utente esterno, anche il non registrato, può iscriversi alla newsletter del cinema (aggiornamenti prossimi film, comunicazioni ecc).
I film con annesse recensioni rimangono presenti nell'applicazione web per un periodo di tempo limitato dopo l'ultima programmazione.

Utenti dipendenti del cinema (staff):
- Utente "segretario", prenota i posti a sedere per le persone che prenotano/acquistano i biglietti telefonicamente o presentandosi di persona.
- Utente "gestore_film", oltre alle funzionalità dell'utente "segretario" può gestire i film con le rispettive informazioni (aggiungere film, eliminarli, modificarli).
- Utente admin, oltre a poter effettuare tutte le operazioni del "gestore_film" e del "segretario", può visualizzare statistiche relative ai film (biglietti venduti per film, biglietti venduti online sui totali ecc).


## Requisiti
- Python 3.10+
- pip
- Virtual environment 

## Setup rapido
```bash
#clona il porgetto e entra della cartella
git clone URL_REPO
cd ProgettoTecWeb/

#installa l'ambiente virtuale ed entra nell'ambiente
pipenv install
pipenv shell

#creiamo il database
python manage.py migrate

#eseguiamo il seed_data che popola il database
python manage.py seed_data --reset

#avvia il server
python manage.py runserver

