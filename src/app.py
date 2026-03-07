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

GAMES_MAP = {
    "Honkai Star Rail": "https://game8.co/games/Honkai-Star-Rail/archives/410296",
    "Genshin Impact": "https://game8.co/games/Genshin-Impact/archives/304759",
    "Zenless Zone Zero": "https://game8.co/games/Zenless-Zone-Zero/archives/435683"
}


class MyClient(commands.Bot):

    async def on_ready(self):
        logging.info(f'Logged in as {self.user} (ID: {self.user.id})')

        try:
            synced = await self.tree.sync(guild=GUILD_ID)
            logging.info(f"Synced {len(synced)} commands to {GUILD_ID.id}")
        except Exception:
            logging.exception("Error in sync")

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content.startswith('!hello'):
            await message.channel.send('Hello!')


intents = discord.Intents.default()
intents.message_content = True


def start_scraping(URLs: list[str]):
    try:
        for url in URLs:
            a=scraper.scrape_page(url)
            print(a)
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

    games_choices = [Choice(name=game, value=i+1) for i, game in enumerate(GAMES_MAP.keys())]

    @app_commands.command()
    @app_commands.describe(games='games to choose from')
    @app_commands.choices(games=games_choices)
    async def get_codes(interaction: discord.Interaction, games: Choice[int]):
        start_scraping([GAMES_MAP[games.name]])
        await interaction.response.send_message(f'Your favourite game is {games.name}.')

    client.tree.add_command(get_codes, guild=GUILD_ID)

    @client.tree.command(name="embed", description="Says hello in an embed!", guild=GUILD_ID)
    async def embed(interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="Hello!", description="This is an embed message!"))

    client.run(TOKEN)


if __name__ == "__main__":
    app()
