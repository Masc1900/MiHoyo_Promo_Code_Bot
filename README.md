# MiHoyo_Promo_Code_Bot

## Descrizione

Il MiHoyo Promo Code Bot è uno strumento automatizzato che raccoglie i codici promozionali più recenti per i giochi MiHoyo e li condivide direttamente su Discord. Questo bot semplifica il processo di ricerca dei codici promo aggiornati eliminando la necessità di controllarli manualmente su diversi siti web.

## Caratteristiche

- Raccoglie automaticamente i codici promo da Game8
- Supporta Genshin Impact, Honkai Star Rail e Zenless Zone Zero
- Invia i codici su Discord in tempo reale
- Traccia i log delle operazioni
- Esporta i dati in formato JSON

## Requisiti

- Python 3.8+
- Discord.py
- BeautifulSoup4
- Requests

## Installazione

1. Clona il repository:

   ```bash
   git clone https://github.com/Masc1900/MiHoyo_Promo_Code_Bot.git
   cd MiHoyo_Promo_Code_Bot
   ```

2. Crea un ambiente virtuale:

   ```bash
   python -m venv venv
   ```

3. Attiva l'ambiente virtuale:
   - Su Windows:

   ```bash
   venv\Scripts\activate
   ```

   - Su macOS/Linux:

   ```bash
   source venv/bin/activate
   ```

4. Installa le dipendenze:

   ```bash
   pip install -r requirements.txt
   ```

## Configurazione

1. Crea un'applicazione Discord e ottieni il token del bot:
   - Vai su [Discord Developer Portal](https://discord.com/developers/applications)
   - Crea una nuova applicazione
   - Naviga alla sezione "Bot" e crea un bot
   - Copia il token

2. Configura il bot con le variabili d'ambiente o modifica il file di configurazione

3. Aggiungi il bot ai tuoi server Discord con i permessi necessari

## Utilizzo

Per avviare il bot:

```bash
python src/app.py
```

Il bot inizierà a monitorare i codici promo e li pubblicherà automaticamente sul canale Discord configurato.

## Struttura del progetto

```bash
MiHoyo_Promo_Code_Bot
├─ .gitignore
├─ .env.example
├─ LICENSE
├─ README.md
├─ .vscode
|  └─ settings.json
├─ .github
|  └─ instructions.md
├─ requirements.txt
├─ src
│  ├─ app.py
│  └─ scraper_functions.py
└─ tests
   └─ manual_testing.ipynb

```

## Struttura del Codice

### app.py

File principale che avvia il bot Discord e coordina le operazioni di raccolta dei codici promo.

### scraper_functions.py

Contiene tutte le funzioni di web scraping per raccogliere i codici da Game8.

## Output dei Dati

I codici promo vengono salvati in formato JSON nella cartella `output/`:

```json
{
  "game": "Genshin Impact",
  "codes": [
    {
      "code": "EXAMPLE123",
      "description": "Descrizione del promo",
      "date": "2024-01-15"
    }
  ]
}
```

## Log e Debugging

I log delle operazioni vengono salvati nella cartella `logs/` per tracciare l'attività del bot.

## Licenza

Questo progetto è licenziato sotto la licenza GNU General Public License v3.0 - vedi il file [LICENSE](LICENSE) per i dettagli.

## Risorse Utili

- Tool di scraping: [MiHoyo_Codes_Scraper](https://github.com/Masc1900/MiHoyo_Codes_Scraper)
