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
- Utente admin, oltre a poter effettuare tutte le operazioni del "gestore_film" e del "segretario", può eliminare gli untenti "gestore_film".

*Clicca qui per la sezione più specifica sui dettagli del progetto:*
[Struttura del progetto](#Struttura-del-progetto-app-Django)

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
```
---
# Struttura del progetto (app Django)

Il progetto è organizzato in 4 app principali:

- **cinepiu**: pagine base (home/info) e creazione utente “cliente”
- **accounts**: gestione utenti, ruoli/gruppi, profilo prenotazioni, newsletter
- **cinema**: catalogo film, sale/posti, programmazione (proiezioni), recensioni
- **sales**: prenotazioni/biglietti e logiche di acquisto/prenotazione

## Ruoli e permessi (accounts/permissions.py)

Il sistema distingue utenti “clienti” e “staff”.

**Gruppi principali:**
- `segretario`
- `gestore_film`

**Concetti:**
- **cliente**: utente autenticato che NON è staff (`is_operational_staff = False`)
- **staff operativo**: superuser **oppure** `is_staff` **oppure** membro di `segretario`/`gestore_film`

**Regole di gestione utenti:**
- possono accedere alla gestione utenti: `segretario`, `gestore_film`, `admin`
- eliminazione utenti:
  - segretario → può eliminare **solo clienti**
  - gestore_film → può eliminare **clienti e segretari**
  - admin (superuser) → può eliminare **clienti, segretari, gestori e staff**
  - nessuno può eliminare **se stesso** o un **superuser**
  - nessuno può eliminare un utente che ha **prenotazioni** (biglietti associati)

---

## App: accounts

### Modelli (accounts/models.py)

**User (custom user)**
- estende `AbstractUser`
- campi extra:
  - `email` (unico)
  - `phone_number` (opzionale)
  - `socio` (boolean, default `False`)

**NewsletterSubscription**
- `email` (unico)
- `user` (FK opzionale a User)
- `is_active` (boolean)
- `consent_at` (data consenso)
- `source` (string opzionale: es. "checkout", "footer", ...)

### Funzionalità principali (accounts/views.py)

**Lista utenti (UserListView)**
- visibile a `segretario`, `gestore_film` e admin
- nel template mostra due elenchi:
  - `staff_users`: utenti in gruppi staff (`segretario`, `gestore_film`)
  - `client_users`: tutti gli altri (utenti “comuni”)

**Toggle Socio**
- lo staff può impostare/togliere il flag `socio` su utenti comuni (clienti)

**Prenotazioni utente**
- lo staff può vedere le prenotazioni dei clienti
- template riutilizzato: `accounts/mie_prenotazioni.html`

**Mie prenotazioni (cliente)**
- mostra tutte le prenotazioni dell’utente loggato
- annullamento consentito fino a **1 ora prima** della proiezione

---

## App: cinema

### Modelli (cinema/models.py)

**Film**
- info: `titolo`, `descrizione`, `genere`, `regista`, `cast_principale`
- date: `data_uscita`, `uscita_locale` (default = data_uscita), `in_programmazione` (default = uscita_locale)
- media: `locandina_url`, `trailer_url` (opzionale)
- flag: `rassegna` (boolean)

**Regole/validazioni Film**
- `uscita_locale` **non può** essere < `data_uscita`
- `in_programmazione` **non può** essere > `uscita_locale`
- `save()` esegue `full_clean()` (quindi valida sempre i vincoli)
- `trailer_embed_url`: converte link YouTube in formato embed quando possibile

**Sala**
- `nome`

**Posto**
- FK `sala`
- `fila`, `numero_posto`
- vincolo univocità: (`sala`, `fila`, `numero_posto`)

**Proiezione**
- FK `film` (PROTECT), FK `sala` (PROTECT), `data_ora`
- vincolo univocità: (`sala`, `data_ora`)

**Regole/validazioni Proiezione**
- una proiezione non può essere precedente all’**uscita locale** del film
- in una stessa sala non possono esistere sovrapposizioni:
  - calcolo “fine film” = durata film + **BUFFER 15 minuti**
  - blocca proiezioni che iniziano durante l’intervallo occupato
  - blocca anche se la proiezione precedente finisce dopo l’inizio della nuova

**Recensione**
- FK `film`
- FK `autore` (User)
- `contenuto`, `valutazione`

### Endpoints AJAX utili (cinema/views.py)
- `film_suggestions`: suggerimenti ricerca (titolo/regista) con min 2 caratteri, max 5 risultati (JSON)
- `sala_impegni`: restituisce i prossimi impegni di una sala (JSON)

---

## App: sales

### Modelli (sales/models.py)

**Biglietto**
- FK `proiezione` (CASCADE)
- FK `posto` (PROTECT)
- `prezzo` (Decimal, default 8.00)
- canali:
  - online: FK `utente` (opzionale)
  - segreteria: `nome_cliente`, `telefono_cliente` (opzionali)
- `stato`: PRENOTATO / PAGATO / ANNULLATO (default PRENOTATO)
- vincolo univocità: (`proiezione`, `posto`) → lo stesso posto non può essere prenotato 2 volte

### Regole di prenotazione (sales/views.py)

**Prenota (online vs segreteria)**
- richiede utente autenticato
- determina `staff_mode` se l’utente è staff operativo
- prezzo:
  - default **8.00**
  - se **utente cliente** ed è `socio=True` → **6.00**
- se `staff_mode=True` allora è obbligatorio inserire almeno un dato cliente (`nome_cliente` o `telefono_cliente`)
- limite prenotazioni online:
  - un cliente può prenotare **max 2 biglietti** per la stessa proiezione (stato PRENOTATO)
- concorrenza/anti-doppia prenotazione:
  - lock DB (`select_for_update`) + vincolo univoco (`proiezione`, `posto`)
  - in caso di conflitto → messaggio “posti appena prenotati da un altro utente”

**Annulla biglietto (cliente)**
- accetta solo `POST`
- consentito solo fino a **1 ora prima** della proiezione
- elimina il record e libera il posto

**Eliminazione biglietto (staff)**
- vista dedicata per staff (`BigliettoStaffDeleteView`)
- `GET` non valido (evita eliminazioni tramite link)

