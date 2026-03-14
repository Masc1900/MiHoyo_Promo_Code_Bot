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


# Create logs directory before setting up logging
ensure_log_directory()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/discord.log'),
        logging.StreamHandler()
    ]
)

# Set discord logger level
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.INFO)
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = discord.Object(
    id=int(os.getenv("DISCORD_GUILD_ID")))  # type: ignore

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

# Channel ID for sending new codes
channel_id = None


class MyClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.check_new_codes_task = None

    async def on_ready(self):
        if self.user is not None:
            logging.info(f'Logged in as {self.user} (ID: {self.user.id})')

        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            logging.info(f"Synced {len(synced)} commands to {GUILD_ID.id}")
        except Exception:
            logging.exception("Error in sync")

        # Start the check_new_codes task if it's assigned and not already running
        if self.check_new_codes_task and not self.check_new_codes_task.is_running():
            # Then start the loop for subsequent checks
            self.check_new_codes_task.start()
            logging.info("check_new_codes task started")

    async def on_message(self, message):
        # non rispondere ai propri messaggi
        if message.author == self.user:
            return


intents = discord.Intents.default()
intents.message_content = True


def start_scraping(URLs: list[str]):
    try:
        for url in URLs:
            codes = scraper.scrape_page(url)
            return codes
    except Exception:
        logging.exception("Error while scraping.")


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

        if len(embed.fields) >= 20:  # Limite di campi per embed
            embed_list.append(embed)
            embed = base_embed.copy()
    embed_list.append(embed)
    return embed_list


def app():
    client = MyClient(command_prefix='!', intents=intents)

    games_choices = [Choice(name=game, value=i+1)
                     for i, game in enumerate(GAMES_MAP.keys())]

    @app_commands.command()
    @app_commands.describe(games='games to choose from')
    @app_commands.choices(games=games_choices)
    async def get_codes(interaction: discord.Interaction, games: Choice[int]):
        logging.info(f"{interaction.user} ha richiesto i codici per {games.name}.")
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

    client.tree.add_command(get_codes, guild=GUILD_ID)

    async def channel_autocomplete(
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        guild = interaction.guild
        if not guild:
            return []

        # Get all text channels and filter by current input
        channels = [
            c for c in guild.text_channels
            if current.lower() in c.name.lower()
        ]

        return [
            app_commands.Choice(name=channel.name, value=str(channel.id))
            for channel in channels[:25]  # Discord limit is 25 choices
        ]

    @app_commands.command(name="set_channel", description="Setta il canale per i nuovi codici")
    @app_commands.autocomplete(channel=channel_autocomplete)
    async def choose_channel_for_new_codes(interaction: discord.Interaction, channel: str):
        global channel_id
        channel_id = int(channel)
        chosen_channel = interaction.guild.get_channel(  # type: ignore
            int(channel))  # type: ignore
        if chosen_channel:
            await interaction.response.send_message(
                f"Canale impostato a {chosen_channel.mention}!",
                ephemeral=True
            )

    client.tree.add_command(choose_channel_for_new_codes, guild=GUILD_ID)

    # Controlla nuovi codici ogni 30 minuti:
    @tasks.loop(minutes=1)  # Per test, altrimenti 30
    async def check_new_codes():
        logging.info("Controllo nuovi codici...")
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

                        if channel_id is not None:
                            channel = client.get_channel(int(channel_id))
                        else:
                            channel = None

                        for embed in embed_list:
                            if channel is not None:
                                await channel.send(embed=embed)  # type: ignore
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
        logging.error("DISCORD_TOKEN environment variable non impostata.")
        return

    # Store task reference on client so it can be started in on_ready()
    client.check_new_codes_task = check_new_codes  # type: ignore
    client.run(TOKEN)


if __name__ == "__main__":
    app()
