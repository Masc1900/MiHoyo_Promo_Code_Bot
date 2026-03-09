import discord
import logging
import os
import scraper_functions as scraper
from dotenv import load_dotenv
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

load_dotenv()
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


class MyClient(commands.Bot):

    async def on_ready(self):
        if self.user is not None:
            logging.info(f'Logged in as {self.user} (ID: {self.user.id})')

        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            logging.info(f"Synced {len(synced)} commands to {GUILD_ID.id}")
        except Exception:
            logging.exception("Error in sync")

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
        print("Error while scraping.")


def app():
    print(os.getenv("DISCORD_GUILD_ID"))
    client = MyClient(command_prefix='!', intents=intents)

    @client.tree.command(name="hello", description="Says hello!", guild=GUILD_ID)
    async def hello(interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

    @client.tree.command(name="printer", description="Echo Message", guild=GUILD_ID)
    async def printer(interaction: discord.Interaction, printer: str):
        await interaction.response.send_message(printer)

    games_choices = [Choice(name=game, value=i+1)
                     for i, game in enumerate(GAMES_MAP.keys())]

    @app_commands.command()
    @app_commands.describe(games='games to choose from')
    @app_commands.choices(games=games_choices)
    async def get_codes(interaction: discord.Interaction, games: Choice[int]):
        codes = start_scraping([GAMES_MAP[games.name]])
        embed = discord.Embed(title=f"Codici per {games.name}", description="Ecco i codici attivi al momento:", color=0x00ff00)
        embed.set_thumbnail(url=LOGO_MAP[games.name])  # Immagine del gioco scelto
        if not codes:
            embed.add_field(name="Nessun codice trovato", value="Non sono riuscito a trovare codici attivi per questo gioco.", inline=False)
            return
        for code in codes:
            embed.add_field(name="", value=f"[{code["Codice"]}]({code["Link"]})", inline=False)
            rewards = "\n".join([reward["Nome"] for reward in code["Ricompense"]])
            quantity = "\n".join([str(reward["Quantita'"]) for reward in code["Ricompense"]])
            embed.add_field(name="", value=rewards, inline=True)
            embed.add_field(name="", value=quantity, inline=True)
        await interaction.response.send_message(embed=embed)

    client.tree.add_command(get_codes, guild=GUILD_ID)

    if TOKEN is None:
        logging.error("DISCORD_TOKEN environment variable non impostata.")
        return
    client.run(TOKEN)


if __name__ == "__main__":
    app()
