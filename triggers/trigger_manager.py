import re
import random
from datetime import datetime
from typing import Literal, Optional, Any

import discord.app_commands
from discord.ext import commands
from discord.app_commands import Range

import utils
from . import help_pages
from .descriptions import desc
from .entities import TriggerEntity, TriggerSettingsEntity
from cofdb import db


class TriggerCog(commands.Cog):
    group = discord.app_commands.Group(name="triggers", description="Manage this server's triggers")

    def __init__(self, bot):
        self.bot = bot
        if not db.is_connection_usable():
            db.connect()
            db.create_tables([TriggerEntity, TriggerSettingsEntity])

        # ensure there is only one row in the settings table
        settings_entities = TriggerSettingsEntity.select()

        with db.atomic() as transaction:
            try:
                if len(settings_entities) == 0:
                    settings_entity = TriggerSettingsEntity()
                    settings_entity.save()
                elif len(settings_entities) > 1:
                    settings_entities[1:].delete_instance()
            except Exception as e:
                transaction.rollback()
                raise RuntimeError("Failed to sanitize the settings table.") from e

        raw_triggers = TriggerEntity.select().order_by(TriggerEntity.position)
        self.triggers = [(trigger, re.compile(str(trigger.regex_pattern))) for trigger in raw_triggers]
        self.globals = settings_entities.select().get()

    @group.command(description=desc.command.help)
    async def help(self, interaction: discord.Interaction):
        pages = utils.Pages(help_pages.get())
        await pages.show(interaction)

    @group.command(description=desc.command.list)
    async def list(self, interaction: discord.Interaction):
        embeds = []

        if not await self.check_trigger_count(interaction):
            return

        for index in range(0, len(self.triggers), 10):
            embed = discord.Embed(title="Triggers", description="_List of all available triggers_")

            for trigger, _ in self.triggers[index:index + 10]:
                pattern = discord.utils.escape_mentions(trigger.user_pattern)
                if len(pattern) > 50:
                    pattern = pattern[:50] + "..."

                embed.add_field(
                    name=f"{trigger.position + 1}. `{pattern}`",
                    value=f"Mode: **{trigger.mode}**",
                    inline=False
                )

            embeds.append(embed)

        pages = utils.Pages(embeds)
        await pages.show(interaction)

    @group.command(description=desc.command.help)
    @discord.app_commands.rename(id_="id")
    @discord.app_commands.describe(id_=desc.argument.inspect.id)
    async def inspect(self, interaction: discord.Interaction, id_: Range[int, 1]):
        id_ -= 1  # user inputs it as 1-indexed
        if not await self.check_id(id_, interaction):
            return

        trigger, _ = self.triggers[id_]

        embed = self.trigger_to_embed(trigger, "_Information about the selected trigger_")

        await interaction.response.send_message(embed=embed)  # type: ignore

    @group.command(description=desc.command.add)
    @discord.app_commands.describe(mode=desc.argument.mode)
    @discord.app_commands.describe(pattern=desc.argument.pattern)
    @discord.app_commands.describe(response=desc.argument.response)
    @discord.app_commands.describe(cooldown=desc.argument.cooldown)
    @discord.app_commands.describe(case_sensitive=desc.argument.case_sensitive)
    @discord.app_commands.describe(avoid_links=desc.argument.avoid_links)
    @discord.app_commands.describe(avoid_emotes=desc.argument.avoid_emotes)
    @discord.app_commands.describe(start=desc.argument.start)
    @discord.app_commands.describe(end=desc.argument.end)
    async def add(
            self, interaction: discord.Interaction,
            mode: Literal["plain", "word", "full", "regex"],
            pattern: str,
            response: str,
            cooldown: Optional[Range[int, 0]] = None,
            case_sensitive: Optional[bool] = None,
            avoid_links: Optional[bool] = None,
            avoid_emotes: Optional[bool] = None,
            start: Optional[bool] = False,
            end: Optional[bool] = False
    ):
        with db.atomic() as transaction:
            try:
                # create a new entity
                new_trigger = TriggerEntity(
                    mode=mode,
                    user_pattern=pattern,
                    response=self.unescape_response(response),
                    cooldown=cooldown,
                    case_sensitive=case_sensitive,
                    avoid_links=avoid_links,
                    avoid_emotes=avoid_emotes,
                    start=start,
                    end=end,
                    regex_pattern=self.compute(mode, pattern, case_sensitive, start, end),
                    position=len(self.triggers),
                    last_used=None
                )

                new_trigger.save()
                self.triggers.append((new_trigger, re.compile(str(new_trigger.regex_pattern))))

                await interaction.response.send_message("Trigger added!")  # type: ignore
            except Exception as e:
                transaction.rollback()
                message = "Failed to add the trigger."
                await interaction.response.send_message(message)  # type: ignore
                raise RuntimeError(message) from e

    @group.command(description=desc.command.edit)
    @discord.app_commands.rename(id_="id")
    @discord.app_commands.describe(id_=desc.argument.edit.id)
    @discord.app_commands.describe(mode=desc.argument.mode)
    @discord.app_commands.describe(pattern=desc.argument.pattern)
    @discord.app_commands.describe(response=desc.argument.response)
    @discord.app_commands.describe(cooldown=desc.argument.cooldown)
    @discord.app_commands.describe(case_sensitive=desc.argument.case_sensitive)
    @discord.app_commands.describe(avoid_links=desc.argument.avoid_links)
    @discord.app_commands.describe(avoid_emotes=desc.argument.avoid_emotes)
    @discord.app_commands.describe(start=desc.argument.start)
    @discord.app_commands.describe(end=desc.argument.end)
    @discord.app_commands.describe(new_id=desc.argument.edit.new_id)
    async def edit(
            self, interaction: discord.Interaction,
            id_: Range[int, 1],
            mode: Optional[Literal["plain", "word", "full", "regex"]] = None,
            pattern: Optional[str] = None,
            response: Optional[str] = None,
            cooldown: Optional[Range[int, 0]] = None,
            case_sensitive: Optional[bool] = None,
            avoid_links: Optional[bool] = None,
            avoid_emotes: Optional[bool] = None,
            start: Optional[bool] = None,
            end: Optional[bool] = None,
            new_id: Optional[Range[int, 1]] = None
    ):
        with db.atomic() as transaction:
            try:
                has_modifications = any(param is not None for param in [
                    mode, pattern, response, cooldown, case_sensitive, avoid_links, avoid_emotes, start, end, new_id
                ])

                if not has_modifications:
                    return await interaction.response.send_message("Nothing to change.")  # type: ignore

                id_ -= 1  # user inputs it as 1-indexed
                if not await self.check_id(id_, interaction):
                    return

                trigger, _ = self.triggers[id_]

                def test_and_update(field: str, value: Any, has_default: bool = False):
                    if value is None and not has_default:
                        return False

                    if getattr(trigger, field) == value:
                        return False

                    setattr(trigger, field, value)
                    return True

                has_modifications = False
                used_id = id_

                if new_id is not None and new_id != trigger.position:
                    new_id -= 1  # user inputs it as 1-indexed
                    if new_id >= len(self.triggers):
                        return await interaction.response.send_message(  # type: ignore
                            f"Invalid new ID, must be between 1 and {len(self.triggers)}."
                        )

                    old_position = trigger.position
                    trigger.position = new_id
                    has_modifications = True

                    if old_position < new_id:
                        for i in range(old_position + 1, new_id + 1):
                            self.triggers[i][0].position -= 1
                    else:
                        for i in range(new_id, old_position):
                            self.triggers[i][0].position += 1

                    self.triggers.sort(key=lambda t: t[0].position)

                    used_id = new_id

                needs_recompute = False
                needs_recompute |= test_and_update("mode", mode)
                needs_recompute |= test_and_update("user_pattern", pattern)
                needs_recompute |= test_and_update("case_sensitive", case_sensitive, True)
                needs_recompute |= test_and_update("start", start)
                needs_recompute |= test_and_update("end", end)

                has_modifications |= needs_recompute

                cooldown_modified = test_and_update("cooldown", cooldown, True)
                has_modifications |= cooldown_modified

                has_modifications |= test_and_update("response", self.unescape_response(response))
                has_modifications |= test_and_update("avoid_links", avoid_links, True)
                has_modifications |= test_and_update("avoid_emotes", avoid_emotes, True)

                if not has_modifications:
                    return await interaction.response.send_message("Nothing changed.")  # type: ignore

                if needs_recompute:
                    trigger.regex_pattern = self.compute(
                        trigger.mode, trigger.user_pattern, trigger.case_sensitive,
                        trigger.start, trigger.end
                    )

                    self.triggers[used_id] = (trigger, re.compile(trigger.regex_pattern))

                if cooldown_modified:
                    trigger.last_triggered = None

                trigger.save()

                embed = self.trigger_to_embed(trigger, "_Trigger edited successfully_")
                await interaction.response.send_message(embed=embed)  # type: ignore
            except Exception as e:
                transaction.rollback()
                message = "Failed to edit the trigger."
                await interaction.response.send_message(message)  # type: ignore
                raise RuntimeError(message) from e

    @group.command(description=desc.command.remove)
    @discord.app_commands.rename(id_="id")
    @discord.app_commands.describe(id_=desc.argument.remove.id)
    async def remove(self, interaction: discord.Interaction, id_: Range[int, 1]):
        id_ -= 1  # user inputs it as 1-indexed
        if not await self.check_id(id_, interaction):
            return

        trigger, _ = self.triggers[id_]

        confirmation = utils.ConfirmationView(interaction.user)

        await interaction.response.send_message(  # type: ignore
            f"Are you sure you want to remove the trigger with **ID `{id_ + 1}`**?",
            view=confirmation
        )
        original_response = await interaction.original_response()
        await confirmation.wait_on_response(original_response)

        if not confirmation.value:
            return  # nothing to do

        with db.atomic() as transaction:
            try:
                trigger.delete_instance()

                for i in range(trigger.position + 1, len(self.triggers)):
                    self.triggers[i][0].position -= 1

                self.triggers.pop(id_)

                await interaction.followup.send("Trigger removed successfully.")
            except Exception as e:
                transaction.rollback()
                message = "Failed to remove the trigger."
                await interaction.followup.send(message)
                raise RuntimeError(message) from e

    @group.command(description=desc.command.setglobal)
    @discord.app_commands.describe(cooldown=desc.argument.cooldown)
    @discord.app_commands.describe(case_sensitive=desc.argument.case_sensitive)
    @discord.app_commands.describe(avoid_links=desc.argument.avoid_links)
    @discord.app_commands.describe(avoid_emotes=desc.argument.avoid_emotes)
    async def setglobal(
            self, interaction: discord.Interaction,
            cooldown: Optional[Range[int, 0]] = None,
            case_sensitive: Optional[bool] = None,
            avoid_links: Optional[bool] = None,
            avoid_emotes: Optional[bool] = None,
    ):
        has_modifications = any(param is not None for param in [
            cooldown, case_sensitive, avoid_links, avoid_emotes
        ])

        if not has_modifications:
            return await interaction.response.send_message("Nothing to change.")  # type: ignore

        with db.atomic() as transaction:
            try:
                if cooldown is not None:
                    self.globals.cooldown = cooldown

                if case_sensitive is not None:
                    self.globals.case_sensitive = case_sensitive

                if avoid_links is not None:
                    self.globals.avoid_links = avoid_links

                if avoid_emotes is not None:
                    self.globals.avoid_emotes = avoid_emotes

                self.globals.save()

                await interaction.response.send_message("Global settings updated successfully.")  # type: ignore
            except Exception as e:
                transaction.rollback()
                message = "Failed to update global settings."
                await interaction.response.send_message(message)  # type: ignore
                raise RuntimeError(message) from e

    @group.command(description=desc.command.setglobal)
    @discord.app_commands.rename(id_="id")
    @discord.app_commands.rename(property_="property")
    @discord.app_commands.describe(id_=desc.argument.reset.id)
    @discord.app_commands.describe(property_=desc.argument.reset.property)
    async def reset(
            self, interaction: discord.Interaction,
            id_: Range[int, 1],
            property_: Literal["cooldown", "case_sensitive", "avoid_links", "avoid_emotes"]
    ):
        id_ -= 1  # user inputs it as 1-indexed
        if not await self.check_id(id_, interaction):
            return

        trigger, _ = self.triggers[id_]

        old_value = getattr(trigger, property_)
        if old_value is None:
            return await interaction.response.send_message(  # type: ignore
                f"The trigger with **ID `{id_ + 1}`** already has the default value for this property."
            )

        setattr(trigger, property_, None)
        new_value = getattr(self.globals, property_)
        await interaction.response.send_message(  # type: ignore
            f"Successfully reset the property `{property_}` of the trigger with **ID `{id_ + 1}`** "
            f"from `{old_value}` to `{new_value}`."
        )

    async def check_id(self, id_: Range[int, 1], interaction: discord.Interaction) -> bool:
        if not await self.check_trigger_count(interaction):
            return False

        if id_ >= len(self.triggers):
            await interaction.response.send_message(  # type: ignore
                f"Invalid ID, must be between 1 and {len(self.triggers)}."
            )

            return False

        return True

    async def check_trigger_count(self, interaction: discord.Interaction) -> bool:
        if len(self.triggers) == 0:
            await interaction.response.send_message(  # type: ignore
                "There are no triggers in this server. Use `/triggers add` to add one."
            )

            return False

        return True

    def trigger_to_embed(self, trigger, description):
        embed = discord.Embed(title="Triggers", description=description)

        embed.add_field(name="🆔 ID", value=f"`{trigger.position + 1}`", inline=True)
        embed.add_field(name="⚙️ Mode", value=f"`{trigger.mode}`", inline=True)
        embed.add_field(
            name="🔍 Pattern", value=f"`{discord.utils.escape_mentions(trigger.user_pattern)}`", inline=False
        )

        responses = self.split_responses(trigger.response)
        responses_title = "💬 Response" if len(responses) == 1 else "💬 Responses"
        for index in range(len(responses)):
            responses[index] = f"- {responses[index]}"
        embed.add_field(name=responses_title, value="\n".join(responses), inline=False)

        def cooldown_mapping(cooldown):
            return utils.human_time(cooldown) if cooldown > 0 else "None"

        embed.add_field(
            name="⏲️ Cooldown",
            value=self.get_value_or_default(trigger.cooldown, self.globals.cooldown, cooldown_mapping),
            inline=True
        )

        embed.add_field(
            name="🔡 Case Sensitive",
            value=self.get_value_or_default(trigger.case_sensitive, self.globals.case_sensitive),
            inline=True
        )

        embed.add_field(
            name="🔗 Avoid Links",
            value=self.get_value_or_default(trigger.avoid_links, self.globals.avoid_links),
            inline=True
        )

        embed.add_field(
            name="😶 Avoid Emotes",
            value=self.get_value_or_default(trigger.avoid_emotes, self.globals.avoid_emotes),
            inline=True
        )

        embed.add_field(name="⏮️ Start", value=f"`{str(trigger.start)}`", inline=True)
        embed.add_field(name="⏭️ End", value=f"`{str(trigger.end)}`", inline=True)

        embed.add_field(name="", value="**[Advanced]**", inline=False)
        embed.add_field(
            name="🛠 Computed Pattern", value=f"`{discord.utils.escape_markdown(trigger.regex_pattern)}`", inline=False
        )

        last_triggered = trigger.last_triggered
        if last_triggered is None:
            last_triggered = "Never"
        else:
            last_triggered = utils.formatted_timestamp(int(last_triggered.timestamp()))
        embed.add_field(name="🗓 Last Triggered", value=last_triggered, inline=False)

        return embed

    @staticmethod
    def get_value_or_default(value, global_value, extra_mapping=None):
        if value is None:
            value = global_value
            is_global = True
        else:
            is_global = False

        if extra_mapping is not None:
            value = extra_mapping(value)

        value = f"`{str(value)}`"
        if is_global:
            value = f"🌍 {value}"

        return value

    @staticmethod
    def compute(mode: str, pattern: str, case_sensitive: bool, start: bool, end: bool):
        # non regex patterns need to be escaped
        regex_builder = pattern if mode == "regex" else re.escape(pattern)

        # "plain" and "word" with both start and end are simply "full"
        if mode in ["plain", "word"] and start and end:
            mode = "full"

        if mode == "full":
            start = True
            end = True

        if mode == "word":
            regex_builder = f"\\b{regex_builder}\\b"

        if start:
            regex_builder = f"^{regex_builder}"

        if end:
            regex_builder = f"{regex_builder}$"

        used_case_sensitive = case_sensitive if case_sensitive is not None \
            else TriggerSettingsEntity.select().get().case_sensitive

        if not used_case_sensitive:
            regex_builder = f"(?i){regex_builder}"

        return regex_builder

    @staticmethod
    def split_responses(response):
        return re.split(r"(?<!\\);", response)

    @staticmethod
    def unescape_response(response):
        if response is None:
            return None

        # discord automatically escapes backslashes, but we want to offer support for newlines
        # so we need to unescape them
        return response.replace("\\n", "\n")

    @staticmethod
    def format_response_variables(message: discord.Message, match: re.Match, response: str):
        # replace simple variables
        response = response.replace("@{author_username}", message.author.mention)
        response = response.replace("@{author_display}", message.author.mention)
        response = response.replace("@{author_nickname}", message.author.mention)
        response = response.replace("@{author_id}", message.author.mention)
        response = response.replace("{author_username}", message.author.name)
        response = response.replace("{author_display}", message.author.display_name)
        response = response.replace("{author_nickname}", message.author.nick)
        response = response.replace("{author_id}", str(message.author.id))

        # replace regex match groups
        for group_index in range(len(match.groups())):
            response = response.replace(f"{{match{group_index}}}", match.group(group_index))

        return response

    @staticmethod
    def test_valid_match(message: discord.Message, match: re.Match, trigger: TriggerEntity):
        if match is None:
            return False

        if trigger.avoid_links:
            links = utils.URL_REGEX.findall(message.content)

            # test if the match is inside a link
            for link in links:
                if match.start() >= link.start() and match.end() <= link.end():
                    return False

        if trigger.avoid_emotes:
            emotes = utils.EMOTE_REGEX.findall(message.content)

            # test if the match is inside an emote
            for emote in emotes:
                if match.start() >= emote.start() and match.end() <= emote.end():
                    return False

        return True

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return  # ignore DMs and bots

        for trigger, pattern in self.triggers:
            match = pattern.search(message.content)
            if self.test_valid_match(message, match, trigger):
                if not self.is_on_cooldown(trigger):
                    await message.channel.send(self.format_response_variables(
                        message, match, random.choice(self.split_responses(trigger.response))
                    ))

                    with db.atomic() as transaction:
                        try:
                            trigger.last_triggered = datetime.now()
                            trigger.save()
                        except Exception as e:
                            transaction.rollback()
                            raise RuntimeError(f"Failed to update trigger \"{trigger.pattern}\"") from e

                return

    def is_on_cooldown(self, trigger):
        trigger_cooldown = trigger.cooldown if trigger.cooldown is not None else self.globals.cooldown

        if trigger_cooldown == 0 or trigger_cooldown is None or trigger.last_triggered is None:
            return False

        return (datetime.now() - trigger.last_triggered).total_seconds() < trigger_cooldown


async def setup(bot):
    await bot.add_cog(TriggerCog(bot))
