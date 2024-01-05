import re
import discord
from types import SimpleNamespace


URL_REGEX = re.compile(
    r"https?://(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)"
)
EMOTE_REGEX = re.compile(r"<a?:[a-zA-Z0-9_]+:[0-9]+>")


def dict_to_simple_namespace(d):
    if isinstance(d, dict):
        return SimpleNamespace(**{k: dict_to_simple_namespace(v) for k, v in d.items()})
    return d


def human_time(seconds):
    parts = []

    minute = 60
    hour = minute * 60
    day = hour * 24
    week = day * 7

    weeks, seconds = divmod(seconds, week)
    days, seconds = divmod(seconds, day)
    hours, seconds = divmod(seconds, hour)
    minutes, seconds = divmod(seconds, minute)

    if weeks:
        parts.append(f"{weeks}w")
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def formatted_timestamp(timestamp, mode="R"):
    return f"<t:{timestamp}:{mode}>"


class ConfirmationView(discord.ui.View):
    def __init__(self, user: discord.User, timeout: int = 30):
        super().__init__(timeout=timeout)
        self.user = user
        self.original_response = None
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.button_press(interaction, True)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.button_press(interaction, False)

    async def on_timeout(self) -> None:
        self.clear_items()
        await self.original_response.edit(view=self)
        self.stop()

    async def button_press(self, interaction: discord.Interaction, value: bool):
        if interaction.user != self.user:
            return await interaction.response.send_message(  # type: ignore
                "This confirmation was not meant for you.",
                ephemeral=True
            )
        self.value = value

        await interaction.response.defer()  # type: ignore
        await self.on_timeout()

    async def wait_on_response(self, original_response: discord.InteractionMessage):
        self.original_response = original_response
        await self.wait()
