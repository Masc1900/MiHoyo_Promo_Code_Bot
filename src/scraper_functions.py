import logging
import os
import requests
import json
from bs4 import BeautifulSoup
from sys import argv
from time import strftime

# Copiato da https://github.com/Masc1900/MiHoyo_Codes_Scraper/blob/main/src/functions.py


def logconfig():
    """
    Configura il sistema di logging per l'applicazione.

    Inizializza il logging con handler per file e console e
    opzionalmente per un widget GUI.
    Crea la cartella 'logs' se non esiste.
    Il livello di logging può essere DEBUG (con flag -d)
    o INFO (default).

    Args:
        log_widget (tkinter.Text, optional):
        Widget di testo Tkinter dove visualizzare i log in GUI.
        Se None (default), i log vengono scritti solo su file e console.

    Returns:
        None

    Behavior:
        - Crea la cartella 'logs' nella directory corrente se non esiste.
        - Imposta il livello di logging a DEBUG se il flag '-d' è presente in sys.argv.
        - Imposta il livello di logging a INFO altrimenti.
        - Configura tre handler:
            1. FileHandler: scrive i log in un file con timestamp nel nome.
            2. StreamHandler: scrive i log su console/stdout.
            3. TextWidgetHandler:
            (opzionale) scrive i log nel widget GUI fornito.
        - Formato log: "{asctime} - {levelname} - {message}" con data/ora in formato ISO.

    Logs:
        Registra tramite il sistema di logging appena configurato.
    """

    if not (os.path.exists(os.path.join(os.getcwd(), "logs"))):
        os.mkdir("logs")

    if "-d" in argv:
        level = logging.DEBUG
    else:
        level = logging.INFO

    handlers = [
        logging.FileHandler(
            filename=f"logs/{strftime("%Y-%m-%d_%H-%M-%S")}.log",
            encoding="utf-8",
            mode="a",
        ),
        logging.StreamHandler(),
    ]

    # Add GUI text widget handler if provided

    logging.basicConfig(
        format="{asctime} - {levelname} - {message}",
        style="{",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=level,
        handlers=handlers,
    )


def format_rewards(names, amounts, imgs):
    """
    Formatta le ricompense in un elenco di dizionari.

    Args:
        names (list): Lista dei nomi delle ricompense.
        amounts (list): Lista delle quantità delle ricompense.
        imgs (list): Lista degli URL delle immagini delle ricompense.

    Returns:
        list: Lista di dizionari con chiavi "Nome", "Quantità", "Immagine".
    """
    rewards_list = []
    for name, amount, img in zip(names, amounts, imgs):
        reward_dict = {
            "Nome": name,
            "Quantita'": amount,
            "Immagine": img
        }
        rewards_list.append(reward_dict)
    return rewards_list


def extract_code_and_link(column_codes):
    """
    Estrae il codice promo e il link di riscatto dalla colonna.

    Args:
        column_codes (BeautifulSoup.Tag): Elemento HTML della colonna codici.

    Returns:
        tuple: (code, link) dove code e link possono essere None se non trovati.
    """
    code = None
    link = None

    if column_codes:
        code_row = column_codes.find("input")
        if code_row:
            code = code_row["value"]
        link_row = column_codes.find("a")
        if link_row:
            link = link_row["href"]

    return code, link


def extract_reward_raw_data(column_rewards):
    """
    Estrae i dati grezzi delle ricompense dal testo della colonna.

    Args:
        column_rewards (BeautifulSoup.Tag): Elemento HTML della colonna ricompense.

    Returns:
        list: Lista di stringhe non vuote con i dati delle ricompense.
    """
    if not column_rewards:
        return []

    rewards = str(column_rewards.text).split("\n")
    # Rimuove le stringhe vuote
    return [el for el in rewards if el.strip()]


def parse_reward_names_and_amounts(raw_rewards):
    """
    Separa i nomi e le quantità delle ricompense.

    Args:
        raw_rewards (list): Lista con nomi e quantità alternati.

    Returns:
        tuple: (reward_names, reward_amounts) liste separate.
    """
    reward_names = []
    reward_amounts = []

    for i, el in enumerate(raw_rewards):
        if i % 2 == 0:
            reward_names.append(el)
        else:
            # Rimuove virgole e la "x" per ottenere il numero
            amount = int(el.replace(",", "").replace("x", ""))
            reward_amounts.append(amount)

    return reward_names, reward_amounts


def extract_reward_images(column_rewards):
    """
    Estrae gli URL delle immagini delle ricompense.

    Args:
        column_rewards (BeautifulSoup.Tag): Elemento HTML della colonna ricompense.

    Returns:
        list: Lista di URL delle immagini.
    """
    reward_imgs = []
    if column_rewards:
        imgs = column_rewards.find_all("img")
        for img in imgs:
            reward_imgs.append(img["data-src"])
    return reward_imgs


def process_rewards_column(column_rewards):
    """
    Elabora completamente la colonna delle ricompense.

    Args:
        column_rewards (BeautifulSoup.Tag): Elemento HTML della colonna ricompense.

    Returns:
        list: Lista di dizionari con le ricompense formattate.
    """
    if not column_rewards:
        return None

    raw_rewards = extract_reward_raw_data(column_rewards)
    if not raw_rewards:
        return None

    reward_names, reward_amounts = parse_reward_names_and_amounts(raw_rewards)
    reward_imgs = extract_reward_images(column_rewards)

    return format_rewards(reward_names, reward_amounts, reward_imgs)


def process_table_row(row):
    """
    Elabora una riga della tabella per estrarre codice e ricompense.

    Args:
        row (BeautifulSoup.Tag): Elemento HTML della riga della tabella.

    Returns:
        dict: Dizionario con chiavi "Codice", "Link", "Ricompense".
    """
    columns = row.find_all("td")
    if len(columns) < 2:
        return None

    code, link = extract_code_and_link(columns[0])
    rewards = process_rewards_column(columns[1])

    return {
        "Codice": code,
        "Link": link,
        "Ricompense": rewards
    }


def extract_table_rows(soup):
    """
    Estrae le righe della tabella dalla pagina.

    Args:
        soup (BeautifulSoup): Oggetto BeautifulSoup della pagina.

    Returns:
        list: Lista di righe della tabella (esclude l'intestazione).
    """
    tables = soup.find_all('table')
    if not tables:
        return []
    return tables[0].find_all('tr')[1:]  # Salta l'intestazione


def scrape_page(url):
    """
    Scrape le pagine web specificate negli URL e registra i dati estratti.

    Args:
        url (str): URL della pagina web da cui estrarre i dati.

    Returns:
        list: Lista di dizionari con i dati estratti, o None in caso di errore.
    """
    try:
        logging.info(f"Inizio scraping della pagina: {url}")
        response = requests.get(url)
        response.raise_for_status()  # Solleva un'eccezione per status code 4xx/5xx
        logging.debug(
            f"Pagina scaricata con successo. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        rows = extract_table_rows(soup)
        dict_list = []

        for row in rows:
            row_data = process_table_row(row)
            if row_data:
                dict_list.append(row_data)

        logging.info(
            f"Scraping completato. Trovati {len(dict_list)} codici promo")
        return dict_list

    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la richiesta a {url}: {e}")
    except Exception as e:
        logging.error(
            f"Errore durante l'estrazione dei dati da {url}: {e}")


def check_dir_exists(filepath):
    """Controlla se la directory del filepath esiste, altrimenti la crea.
    Args:
        filepath (str): Il percorso completo del file (incluso il nome del file)."""
    dir_path = os.path.dirname(filepath)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logging.info(f"Directory creata: {dir_path}")


def save_to_json(data, filepath, filename):
    """Salva i dati estratti in un file JSON.
    Args:
        data (list): La lista di dizionari da salvare.
        filepath (str): Il percorso della directory dove salvare il file.
        filename (str): Il nome del file (senza estensione)."""
    try:
        check_dir_exists(filepath)
        logging.info(
            f"Inizio salvataggio dati su file: {filepath + filename + '.json'}")
        with open(filepath + filename + ".json", "w") as file:
            json.dump(data, fp=file, indent=4)
        logging.info(
            f"Dati salvati con successo. File: {filepath + filename + '.json'} | Elementi: {len(data)}")
    except Exception as e:
        logging.error(
            f"Errore durante il salvataggio del file {filepath + filename + '.json'}: {e}")
        raise
