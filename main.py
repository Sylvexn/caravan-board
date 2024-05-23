import discord
from discord.ext import commands
import requests
import json
import asyncio
from discord import app_commands
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

RIOT_API_KEY = os.getenv('RIOT_API_KEY')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
LEADERBOARD_CHANNEL_ID = int(os.getenv('LEADERBOARD_CHANNEL_ID'))
DATA_FILE = 'leaderboard_data.json'

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            if 'players' not in data or 'limit' not in data:
                raise ValueError("Invalid data format")
            return data
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        # Initialize with default values if the file is missing or corrupted
        default_data = {'players': [], 'limit': 10}
        save_data(default_data)
        return default_data

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def fetch_puuid(game_name, tag_line):
    url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}?api_key={RIOT_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch PUUID: {response.status_code} - {response.text}")
        return None

def fetch_summoner_data(puuid):
    url = f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}?api_key={RIOT_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch summoner data: {response.status_code} - {response.text}")
        return None

def fetch_summoner_rank(summoner_id):
    url_rank = f'https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}?api_key={RIOT_API_KEY}'
    response = requests.get(url_rank)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch rank data: {response.status_code} - {response.text}")
        return None

async def update_leaderboard(interaction=None):
    channel = bot.get_channel(LEADERBOARD_CHANNEL_ID)
    if channel:
        data = load_data()
        leaderboard = []

        for player in data['players']:
            puuid_data = fetch_puuid(player['game_name'], player['tag_line'])
            if puuid_data:
                puuid = puuid_data['puuid']
                summoner_data = fetch_summoner_data(puuid)
                if summoner_data:
                    summoner_id = summoner_data['id']
                    rank_data = fetch_summoner_rank(summoner_id)
                    if rank_data:
                        solo_rank = next((entry for entry in rank_data if entry['queueType'] == 'RANKED_SOLO_5x5'), None)
                        if solo_rank:
                            leaderboard.append({
                                'riot_id': f"{player['game_name']}#{player['tag_line']}",
                                'tier': solo_rank['tier'],
                                'rank': solo_rank['rank'],
                                'lp': solo_rank['leaguePoints'],
                                'wins': solo_rank['wins'],
                                'losses': solo_rank['losses'],
                                'hot_streak': solo_rank['hotStreak']
                            })

        leaderboard = sorted(leaderboard, key=lambda x: (x['tier'], x['rank'], x['lp']), reverse=True)
        limit = data['limit']
        leaderboard = leaderboard[:limit]

        embed = discord.Embed(title="Leaderboard", color=discord.Color.blue())
        for idx, entry in enumerate(leaderboard, start=1):
            position = f"{idx}️⃣"
            hot_streak = "🔥" if entry['hot_streak'] else ""
            embed.add_field(
                name=f"{position} {entry['riot_id']}",
                value=f"{entry['tier']} {entry['rank']} {entry['lp']} LP - {entry['wins']}/{entry['losses']} - {hot_streak}",
                inline=False
            )

        await channel.purge()
        message = await channel.send(embed=embed, view=LeaderboardView())

        if interaction:
            await interaction.response.send_message("Leaderboard updated.", ephemeral=True)

class LeaderboardView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.manage_guild:
            await update_leaderboard(interaction)
        else:
            await interaction.response.send_message("You do not have permission to refresh the leaderboard.", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user}')
    await update_leaderboard()

@bot.tree.command(name="add")
async def add(interaction: discord.Interaction, riot_id: str):
    game_name, tag_line = riot_id.split('#')
    data = load_data()
    if any(player['game_name'] == game_name and player['tag_line'] == tag_line for player in data['players']):
        await interaction.response.send_message("Player is already on the leaderboard.", ephemeral=True)
        return

    data['players'].append({'game_name': game_name, 'tag_line': tag_line})
    save_data(data)
    await interaction.response.send_message(f"Added {riot_id} to the leaderboard.", ephemeral=True)

@bot.tree.command(name="remove")
async def remove(interaction: discord.Interaction, riot_id: str):
    game_name, tag_line = riot_id.split('#')
    data = load_data()
    data['players'] = [player for player in data['players'] if not (player['game_name'] == game_name and player['tag_line'] == tag_line)]
    save_data(data)
    await interaction.response.send_message(f"Removed {riot_id} from the leaderboard.", ephemeral=True)

@bot.tree.command(name="setlimit")
@commands.has_permissions(manage_guild=True)
async def setlimit(interaction: discord.Interaction, limit: int):
    data = load_data()
    data['limit'] = limit
    save_data(data)
    await interaction.response.send_message(f"Leaderboard display limit set to {limit}.", ephemeral=True)

bot.run(DISCORD_BOT_TOKEN)