# Istruzioni per sviluppo MiHoyo_Promo_Code_Bot

## Requisiti

- python 3.13.0 o superiore
- discord.py

## Documentazione

Il codice, nomi di variabili e tutto cio che è codice dovrebbe essere in inglese, mentre la documentazione, commenti, docstring, etc... deve essere in italiano.

Link alla documentazione di discord.py: https://discordpy.readthedocs.io tutto ciò che riguarda discord.py deve essere documentato e creato usando questa documentazione.

## Obiettivo

Creare un bot discord che basandosi sui dati di input dai Json estratti usando [il code scraper](../scraper/Mihoyo_Code_Scraper.exe) che sono nella cartella [output](../scraper/output/"nome gioco".json).

### Esempio di Json

```bash
[
    {
        "Codice": "ALETTERFORYOU",
        "Link": "https://hsr.hoyoverse.com/gift?code=ALETTERFORYOU",
        "Ricompense": [
            {
                "Nome": " Adventure Log",
                "Quantita'": 6,
                "Immagine": "https://img.game8.co/3656095/54eed904294437c7e5e6d92315ca3e02.png/show"
            },
            {
                "Nome": " Dreamlight - Mixed Sweets",
                "Quantita'": 2,
                "Immagine": "https://img.game8.co/3837201/bb231adea728f988f634e82a29586167.png/show"
            }
        ]
    }
]
```

## Comandi

### /setup

Comando per configurare il bot, che permette di specificare le varie opzioni (come il canale dove mandare i messaggi, l'intervallo di tempo per controllare i codici, etc...):

- Tempo di intervallo per controllare i codici configurabile tramite /setup.
- Un canale specificato dall'utente che se non è stato specificato, il bot manda i messaggi nel canale dove è stato richiamato.

### /show_codes *"nome gioco"*/all

Comando che mostra tutti i codici attivi per un gioco specifico o per tutti i giochi.

## Input

Comandi da Discord e i file Json estratti usando [il code scraper](../scraper/Mihoyo_Code_Scraper.exe) che sono nella cartella [output](../scraper/output/"nome gioco".json).

## Output

Un messaggio Discord di un embed con il codice promozionale (insieme al link di redeem, ricompense e immagine) più recente (se cambiato) per ogni gioco.

## Logging

Il bot deve loggare tutte le operazioni in un file di log, con data e ora, e il tipo di operazione (info, warning, error).
Si può usare la libreria logging di python per questo scopo con integrazione in discord.py.
Il file di log deve essere conservato in una cartella /logs.
