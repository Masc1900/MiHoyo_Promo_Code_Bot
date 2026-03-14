import discord
import logging
import os
import json
import scraper_functions as scraper
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import Choice

load_dotenv()


def ensure_log_directory():
    """Crea la cartella logs se non esiste."""
    if not os.path.exists("logs"):
        os.makedirs("logs")


def ensure_config_directory():
    """Crea la cartella config se non esiste."""
    if not os.path.exists("config"):
        os.makedirs("config")


def load_channel_config() -> dict:
    """Carica la configurazione dei canali da file JSON.

    Returns:
        dict: Dizionario mappando guild_id -> channel_id
    """
    ensure_config_directory()
    config_file = "config/channels.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(
                f"Errore nel caricamento della configurazione: {e}")
            return {}
    return {}


def save_channel_config(config: dict) -> None:
    """Salva la configurazione dei canali su file JSON.

    Args:
        config (dict): Dizionario mappando guild_id -> channel_id
    """
    ensure_config_directory()
    config_file = "config/channels.json"
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        logging.error(f"Errore nel salvataggio della configurazione: {e}")


def get_channel_for_guild(guild_id: int, config: dict) -> int | None:
    """Recupera l'ID canale per una specifica guild.

    Args:
        guild_id (int): ID della guild Discord
        config (dict): Configurazione caricata

    Returns:
        int | None: ID canale o None se non configurato
    """
    channel_id = config.get(str(guild_id))
    return int(channel_id) if channel_id else None


def set_channel_for_guild(guild_id: int, channel_id: int, config: dict) -> None:
    """Salva l'ID canale per una specifica guild.

    Args:
        guild_id (int): ID della guild Discord
        channel_id (int): ID del canale Discord
        config (dict): Configurazione da aggiornare
    """
    config[str(guild_id)] = str(channel_id)
    save_channel_config(config)


# Crea la directory dei log prima di configurare il logging
ensure_log_directory()

# Configura il logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/discord.log'),
        logging.StreamHandler()
    ]
)

# Imposta il livello di logging di discord
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
TOKEN = os.getenv("DISCORD_TOKEN")
try:
    GUILD_ID = discord.Object(
        id=int(os.getenv("DISCORD_GUILD_ID")))  # type: ignore
    logging.info(f"Guild ID impostato a {GUILD_ID.id}")
except (ValueError, TypeError):
    GUILD_ID = None

GAMES_MAP = {  # Espandibile in futuro
    "Honkai Star Rail": "https://game8.co/games/Honkai-Star-Rail/archives/410296",
    "Genshin Impact": "https://game8.co/games/Genshin-Impact/archives/304759",
    "Zenless Zone Zero": "https://game8.co/games/Zenless-Zone-Zero/archives/435683"
}

LOGO_MAP = {  # Espandibile in futuro
    "Honkai Star Rail": "https://cdn2.steamgriddb.com/logo/804bfd285116c91c935176b2b199894d.png",
    "Genshin Impact": "https://cdn2.steamgriddb.com/logo_thumb/944eefd22dfe99fe7631b8ecc732c7cf.png",
    "Zenless Zone Zero": "https://cdn2.steamgriddb.com/logo_thumb/6636876050dcade8ec8e3023b1afe9bc.png"
}

# Configurazione dei canali per guild (caricata da file JSON)
channel_config = load_channel_config()


class MyClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_new_codes_task = None

    async def on_ready(self):
        if self.user is not None:
            logging.info(
                f'Riuscito accesso come {self.user} (ID: {self.user.id})')

        try:
            synced = await self.tree.sync()
            logging.info(
                f"Sincronizzati {len(synced)} comandi globalmente")
        except Exception:
            logging.exception("Errore durante la sincronizzazione")

        # Avvia il task check_new_codes se assegnato e non sta già girando
        if self.check_new_codes_task and not self.check_new_codes_task.is_running():
            # Poi avvia il loop per i controlli successivi
            self.check_new_codes_task.start()
            logging.info("Iniziato il controllo periodico dei nuovi codici.")

    async def on_message(self, message):
        # non rispondere ai propri messaggi
        if message.author == self.user:
            return


intents = discord.Intents.default()
intents.message_content = True


def start_scraping(URLs: list[str]):
    """Avvia lo scraping delle pagine web.

    Args:
        URLs (list[str]): Lista di URL da scrapare.

    Returns:
        list: Lista di codici estratti, o None in caso di errore.
    """
    try:
        for url in URLs:
            codes = scraper.scrape_page(url)
            return codes
    except Exception:
        logging.exception("Errore durante lo scraping.")


def check_file_exists(filepath):
    """Controlla se un file esiste.

    Args:
        filepath (str): Il percorso completo del file (incluso il nome del file).

    Returns:
        bool: True se il file esiste, False altrimenti.
    """
    return os.path.isfile(filepath)


def create_embeds_for_codes(game_name: str, codes, base_embed: discord.Embed):
    embed_list = []

    scraper.check_dir_exists("output/")
    scraper.save_to_json(codes, "output/", f"{game_name}")

    embed = base_embed.copy()

    for code in codes:
        embed.add_field(
            name="", value=f"[{code['Codice']}]({code['Link']})", inline=False)
        rewards = "\n".join([reward["Nome"] for reward in code["Ricompense"]])
        quantity = "\n".join([str(reward["Quantita'"])
                             for reward in code["Ricompense"]])
        embed.add_field(name="", value=rewards, inline=True)
        embed.add_field(name="", value=quantity, inline=True)

        if len(embed.fields) >= 20:  # Limite Discord di campi per embed
            embed_list.append(embed)
            embed = base_embed.copy()
    embed_list.append(embed)
    return embed_list


def app():
    client = MyClient(command_prefix='!', intents=intents)

    games_choices = [Choice(name=game, value=i+1)
                     for i, game in enumerate(GAMES_MAP.keys())]

    @app_commands.command(name="get_codes", description="Mostra i codici promo attivi per un gioco")
    @app_commands.describe(games='giochi tra cui scegliere')
    @app_commands.choices(games=games_choices)
    async def get_codes(interaction: discord.Interaction, games: Choice[int]):
        logging.info(
            f"{interaction.user} nel server {interaction.guild} ha richiesto i codici per {games.name}.")
        codes = start_scraping([GAMES_MAP[games.name]])
        if not codes:
            await interaction.response.send_message("Non sono riuscito a trovare codici attivi per questo gioco.", ephemeral=True)
            return

        base_embed = discord.Embed(
            title=f"Codici per {games.name}", description="Ecco i codici attivi al momento:", color=0x00ff00)
        # Immagine del gioco scelto
        base_embed.set_thumbnail(url=LOGO_MAP[games.name])

        embed_list = create_embeds_for_codes(games.name, codes, base_embed)
        has_responded = False

        for embed in embed_list:
            logging.debug(embed_list)
            if not has_responded:
                await interaction.response.send_message(embed=embed)
                has_responded = True
            else:
                await interaction.followup.send(embed=embed)

    client.tree.add_command(get_codes)

    async def channel_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        guild = interaction.guild
        if not guild:
            return []

        # Ottiene tutti i canali di testo e filtra in base all'input attuale
        channels = [
            c for c in guild.text_channels
            if current.lower() in c.name.lower()
        ]

        return [
            app_commands.Choice(name=channel.name, value=str(channel.id))
            for channel in channels[:25]  # Il limite di Discord è 25 scelte
        ]

    @app_commands.command(name="set_channel", description="Setta il canale per i nuovi codici")
    @app_commands.autocomplete(channel=channel_autocomplete)
    async def choose_channel_for_new_codes(interaction: discord.Interaction, channel: str):
        global channel_config
        channel_id = int(channel)
        guild_id = interaction.guild.id if interaction.guild else None  # type: ignore

        if guild_id:
            set_channel_for_guild(guild_id, channel_id, channel_config)

        chosen_channel = interaction.guild.get_channel(  # type: ignore
            channel_id)  # type: ignore
        if chosen_channel:
            await interaction.response.send_message(
                f"Canale impostato a {chosen_channel.mention}!",
                ephemeral=True
            )

    client.tree.add_command(choose_channel_for_new_codes)

    # Controlla nuovi codici ogni 30 minuti
    @tasks.loop(minutes=30)  # Per test: 1, altrimenti: 30
    async def check_new_codes():
        """Controlla nuovi codici promo disponibili per ogni gioco."""
        global channel_config
        logging.info("Controllo nuovi codici...")

        # Ricarica la configurazione per ottenere i canali attuali
        channel_config = load_channel_config()

        for game, url in GAMES_MAP.items():
            try:
                new_codes = scraper.scrape_page(url)
                if not new_codes:
                    logging.info(f"Nessun codice trovato per {game}.")
                    continue

                filepath = f"output/{game}.json"
                if check_file_exists(filepath):
                    with open(filepath, 'r') as f:
                        old_codes = json.load(f)
                    old_code_set = set(code['Codice'] for code in old_codes)
                    new_code_set = set(code['Codice'] for code in new_codes)
                    added_codes_set = new_code_set - old_code_set

                    # Se ci sono nuovi codici, crea un embed prendendo da new_codes solo quelli nuovi
                    if added_codes_set:
                        added_codes = []
                        for code in new_codes:
                            if code["Codice"] in added_codes_set:
                                added_codes.append(code)

                        logging.info(
                            f"Nuovi codici trovati per {game}: {added_codes_set}")
                        # Manda un embed al canale Discord se ci sono nuovi codici
                        base_embed = discord.Embed(
                            title=f"Nuovi codici per {game}", description="Sono stati trovati nuovi codici attivi:", color=0xff0000)
                        base_embed.set_thumbnail(url=LOGO_MAP[game])
                        embed_list = create_embeds_for_codes(
                            game, added_codes, base_embed)

                        # Invia il messaggio a tutti i canali configurati per le diverse guild
                        if channel_config:
                            for guild_id_str, channel_id_str in channel_config.items():
                                try:
                                    channel = client.get_channel(
                                        int(channel_id_str))
                                    if channel is not None:
                                        for embed in embed_list:
                                            # type: ignore
                                            await channel.send(embed=embed)  # type: ignore
                                    else:
                                        logging.warning(
                                            f"Canale non trovato per guild {guild_id_str}")
                                except Exception as channel_error:
                                    logging.error(
                                        f"Errore nell'invio del messaggio a guild {guild_id_str}: {channel_error}")
                        else:
                            logging.info(
                                "Nessun canale impostato per l'invio dei nuovi codici.")

                        scraper.save_to_json(new_codes, "output/", game)
                else:
                    scraper.save_to_json(new_codes, "output/", game)
            except Exception as e:
                logging.error(
                    f"Errore durante il controllo dei codici per {game}: {e}", exc_info=True)

    if TOKEN is None:
        logging.error("Variabile di ambiente DISCORD_TOKEN non impostata.")
        return

    # Memorizza il riferimento del task nel client in modo da avviarlo in on_ready()
    client.check_new_codes_task = check_new_codes  # type: ignore
    client.run(TOKEN)


if __name__ == "__main__":
    app()
