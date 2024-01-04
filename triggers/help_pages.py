import discord

BLANK = "\u200b"
USE_LEGACY_INLINE_SPLITS = True


def get():
    embed_infos = [
        get_preface(),
        get_commands(),
        get_command_list(),
        get_command_inspect(),
        get_command_add_1(),
        get_command_add_2(),
        get_command_edit(),
        get_command_remove(),
        get_property_mode_1(),
        get_property_mode_2(),
        get_property_response_1(),
        get_property_response_2(),
        get_property_uses_wildcards()
    ]

    # add page numbers
    for i in range(len(embed_infos)):
        footer_info = [f"Page {i + 1}/{len(embed_infos)}"]

        if i > 0:
            footer_info.append(f"Previous: [{get_title_from_info(embed_infos[i - 1])}]")

        if i < len(embed_infos) - 1:
            footer_info.append(f"Next: [{get_title_from_info(embed_infos[i + 1])}]")

        embed_infos[i][0].set_footer(text=" | ".join(footer_info))

    # add table of contents to the first page
    count = len(embed_infos)
    padding = len(str(count))
    contents = []
    for i in range(count):
        embed_info = embed_infos[i]
        embed = embed_info[0]
        formatted_title = embed_info[1]

        embed.title = f"Triggers Help - {formatted_title}"
        contents.append(f"`Page {str(i + 1).rjust(padding)}` {formatted_title}")

    embed_infos[0][0].add_field(inline=False, name="Table of Contents", value="\n".join(contents))

    return [embed_info[0] for embed_info in embed_infos]


def get_title_from_info(embed_info):
    return embed_info[2] if len(embed_info) > 2 else embed_info[1]


def add_split_fields(embed, names, legacy_title, entries):
    if USE_LEGACY_INLINE_SPLITS:
        embed.add_field(inline=False, name="", value=f"**{legacy_title}**")
        for entry in entries:
            embed.add_field(inline=False, name=f"- {entry[0]}", value="\n".join(entry[1:]))

        return

    column_count = len(names)
    assert 1 <= column_count <= 3

    for name in names:
        embed.add_field(inline=True, name=name, value="")

    for _ in range(3 - column_count):
        embed.add_field(inline=True, name="", value="")

    for entry in entries:
        for field in entry:
            embed.add_field(inline=True, name="", value=field)

        for _ in range(3 - column_count):
            embed.add_field(inline=True, name="", value="")


def make_title(title):
    return f"Triggers Help - {title}"


def get_preface():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Summary", value=(
            "Triggers are a way to make the bot respond to certain messages.\n"
            "This module offers multiple _matching modes_ along with the special mode `regex`, "
            "which allows you to use **regular expressions** to match messages, giving you the most flexibility."
        )
    )

    return embed, "Preface"


def get_commands():
    embed = discord.Embed()

    embed.add_field(inline=False, name="", value="The module introduces multiple slash commands.")
    add_split_fields(
        embed, ["Command", "Description"], "Commands", [
            ("`/triggers help`", "Display this help menu"),
            ("`/triggers list`", "Display a list of all triggers"),
            ("`/triggers inspect`", "Display information about a specific trigger"),
            ("`/triggers add`", "Add a new trigger"),
            ("`/triggers edit`", "Edit an existing trigger"),
            ("`/triggers remove`", "Remove an existing trigger")
        ]
    )

    return embed, "Commands"


def get_command_list():
    embed = discord.Embed()

    embed.add_field(inline=False, name="Usage", value="`/triggers list`")
    embed.add_field(
        inline=False, name="Description", value=(
            "This command allows you to view a list of all existing triggers.\n"
            "Useful to retrieve the ID of a trigger before editing or removing it."
        )
    )

    return embed, "Command: `list`", "Command: list"


def get_command_inspect():
    embed = discord.Embed()

    embed.add_field(inline=False, name="Usage", value="`/triggers inspect <id>`")
    embed.add_field(
        inline=False, name="Description", value=(
            "This command allows you to view detailed information about an existing trigger.\n"
            "Useful to check if a trigger is working as intended or before editing one."
        )
    )
    add_split_fields(
        embed, ["Argument", "Description"], "Arguments", [
            (
                "[**Required**] `id`",
                "The ID of the trigger to inspect. You can view each trigger's ID "
                "using the `/triggers list` command."
            )
        ]
    )

    return embed, "Command: `inspect`", "Command: inspect"


def get_command_add_1():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Usage",
        value="`/triggers add <mode> <pattern> <response> [options]`"
    )
    embed.add_field(
        inline=False, name="Description", value=(
            "This command allows you to create a new trigger.\n"
            "The logic behind the trigger depends heavily on the _matching mode_ you choose.\n"
            "The trigger will be added **at the end** of the list of triggers, and will be available immediately."
        )
    )
    add_split_fields(
        embed, ["Argument", "Description"], "Arguments", [
            (
                "[**Required**] `mode`",
                "The _matching mode_ to use. One of `plain`, `word`, `full`, `regex`."
            ),
            (
                "[**Required**] `pattern`",
                "The pattern to match. The syntax depends on the _matching mode_ you choose, and other "
                "optional arguments."
            ),
            (
                "[**Required**] `response`",
                "The response to send when the trigger is matched. Multiple responses can be registered "
                "by separating them with a semicolon (`;`). The bot will choose one of the responses at "
                "random."
            ),
        ]
    )

    return embed, "Command: `add` (1)", "Command: add (1)"


def get_command_add_2():
    embed = discord.Embed()

    add_split_fields(
        embed, ["Argument", "Description"], "Arguments", [
            (
                "[_Optional_] `cooldown`",
                "The cooldown of the trigger, in seconds. The bot will ignore messages that match the "
                "trigger if they are sent within the cooldown period.\n"
                "Defaults to `0`."
            ),
            (
                "[_Optional_] `case_sensitive`",
                "Whether to treat uppercase and lowercase letters the same. If set to `false`, the bot "
                "will ignore the case of the letters and treat \"a\" and \"A\" as the same letter.\n"
                "Defaults to `false`."
            ),
            (
                "[_Optional_] `uses_wildcards`",
                "Whether to treat the pattern as a wildcard pattern. If set to `true`, the bot will treat "
                "\"?\" and \"*\" as wildcards, and match them to any character or any sequence of characters.\n"
                "Defaults to `false`."
            ),
            (
                "[_Optional_] `start`",
                "If set to `true`, the bot will only match the pattern if it is at the start of the message.\n"
                "Defaults to `false`."
            ),
            (
                "[_Optional_] `end`",
                "If set to `true`, the bot will only match the pattern if it is at the end of the message.\n"
                "Defaults to `false`."
            ),
            (
                "[_Optional_] `avoid_links`",
                "If set to `true`, the bot will not look for the pattern in links.\n"
                "Defaults to `false`."
            ),
            (
                "[_Optional_] `avoid_emotes`",
                "If set to `true`, the bot will not look for the pattern in emote names.\n"
                "Defaults to `false`."
            )
        ]
    )

    return embed, "Command: `add` (2)", "Command: add (2)"


def get_command_edit():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Usage",
        value="`/triggers edit <id> [properties]`"
    )
    embed.add_field(
        inline=False, name="Description", value=(
            "This command allows you to edit an existing trigger.\n"
            "\n"
            "You can modify any of the trigger's properties defined in the `/triggers add` command, "
            "on top of modifying the trigger's ID, effectively changing its position in the list of triggers.\n"
            "\n"
            "The modifications will be available immediately."
        )
    )
    add_split_fields(
        embed, ["Argument", "Description"], "Arguments", [
            (
                "[**Required**] `id`",
                "The ID of the trigger to edit. You can view each trigger's ID "
                "using the `/triggers list` command."
            ),
            (
                "[_Optional_] `new_id`",
                "The new ID of the trigger. If not specified, the ID will not be changed."
            ),
        ]
    )

    return embed, "Command: `edit`", "Command: edit"


def get_command_remove():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Usage",
        value="`/triggers remove <id>`"
    )
    embed.add_field(
        inline=False, name="Description", value=(
            "This command allows you to remove an existing trigger.\n"
            "\n"
            "The trigger will be removed immediately."
        )
    )
    add_split_fields(
        embed, ["Argument", "Description"], "Arguments", [
            (
                "[**Required**] `id`",
                "The ID of the trigger to remove. You can view each trigger's ID "
                "using the `/triggers list` command."
            )
        ]
    )

    return embed, "Command: `remove`", "Command: remove"


def get_property_mode_1():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Description", value=(
            "The logic behind the trigger depends heavily on the _matching mode_ you choose.\n"
            "The following modes are available: `plain`, `word`, `full`, `regex`.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Mode: `plain`", value=(
            "This mode is the simplest one. The bot will check if the message contains the pattern, "
            "wherever it is in the message.\n"
            "This means that a pattern of `\"end\"` _will_ trigger on the message `\"Friendship is important\"`, "
            "because `\"Friendship\"` contains `\"end\"`.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Mode: `word`", value=(
            "This mode may be the most useful one. The bot will check if the message contains the "
            "given pattern, but only if it is not part of other words.\n"
            "This means that a pattern of `\"end\"` _will not_ trigger on the message `\"Friendship is important\"`, "
            "because `\"end\"` is not a standalone word in the message.\n"
            "On the other hand, the pattern `\"end\"` _will_ trigger on the message `\"The end is near\"`, because "
            "`\"end\"` is a standalone word in the message.\n"
            "\n"
            "Keep in mind that this is not limited to single words. You can also "
            "trigger the pattern `\"ship is\"` on the message `\"My ship is sinking\"`. Likewise, this pattern "
            "will _not_ trigger on the message `\"Friendship is important\"`, because `\"ship\"` is part "
            "of another word."
        )
    )

    return embed, "Property: `mode` (1)", "Property: mode (1)"


def get_property_mode_2():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Mode: `full`", value=(
            "The bot will check _the entire message_ against the pattern. This means that the pattern "
            "`\"Friendship is important\"` _will not_ trigger on the message `\"Friendship is important!\"`, "
            "because the message contains an exclamation mark, which is not part of the pattern.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Mode: `regex`", value=(
            "This mode allows you to use a regular expression as the pattern. This is the most powerful "
            "mode, but also the most complicated one. "
            "_Any other mode can be replicated using a regular expression._\n"
            "You can find more information about regular expressions [here](https://www.regular-expressions.info/).\n"
            "\n"
            "A popular use case for the simple user would be to look for _different_ patterns in the same "
            "message. For example, you could use the pattern `\"hello|hi\"`, and the bot would trigger on "
            "messages that contain either `\"hello\"` **or** `\"hi\"`.\n"
            "\n"
            "Other simple purposes:\n"
            "- Multiple word options: `\"I (love|like) (cats|dogs) a lot\"`, "
            "`\"(Christmas|Chrismas|Xmas) is so fun\"`\n"
            "- Optional word(s): `\"I like cats( a lot)?\"` will match both `\"I like cats\"` and "
            "`\"I like cats a lot\"`\n"
            "\n"
            "For more advanced purposes, you should consult with someone capable of writing regular expressions."
        )
    )

    return embed, "Property: `mode` (2)", "Property: mode (2)"


def get_property_response_1():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Description", value=(
            "The response is the message that the bot will send when the trigger is matched.\n"
            "\n"
            "You can specify multiple responses by separating them with a semicolon (`;`). The bot will "
            "choose one of the responses at random.\n"
            "\n"
            "Responses can also contain special variables, which will be replaced with the appropriate "
            "values when the response is sent.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Variable `{author_username}`", value=(
            "The **username** of the author of the message that triggered the response.\n"
            "This is the unique name that identifies the user, and is not necessarily the same as their "
            "display name or server nickname.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Variable `{author_display_name}`", value=(
            "The **display name** of the author of the message that triggered the response.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Variable `{author_server_nickname}`", value=(
            "The **server nickname** of the author of the message that triggered the response.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Additional features", value=(
            "You can add \"@\" before any of these variables to mention the user instead of just using their name."
        )
    )

    return embed, "Property: `response` (1)", "Property: response (1)"


def get_property_response_2():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Variable `{match<id>}`", value=(
            "[**Advanced**] This variable only has effect when using the `regex` mode or the `uses_wildcards` option.\n"
            "It will be replaced with the text that matched the corresponding group in the regular expression, "
            "or the corresponding wildcard-containing word.\n"
            "\n"
            "For example, if you use the regex pattern `\"(hello|hi) (there|people)\"`, and the message is "
            "`\"hello there\"`, the variable `{match1}` will be replaced with `\"hello\"`, and `{match2}` "
            "with `\"there\"`.\n"
            "\n"
            "If you use the wildcard pattern `\"I * you\"`, and the message is `\"I love you\"`, the variable "
            "`{match1}` will be replaced with `\"love\"`.\n"
            "\n"
            "If you use the wildcard pattern `\"I love p*c?ns and p?ns so* much\"`, and the message is "
            "`\"I love pelicans and pens sooo much\"`, the variable `{match1}` will be replaced with `\"pelicans\"`, "
            "and `{match2}` with `\"pens\"`, and `{match3}` with `\"sooo\"`.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="Additional features", value=(
            "[**Advanced**] If you need to use any special characters mentioned above in your response, you can "
            "escape them by adding a backslash (`\\`) before them. For example, if you want to use an actual "
            "semicolon (`;`) in your response, you can write `\\;` instead.\n"
            "If by any chance you want to use a backslash (`\\`) in your response, you can escape it by adding "
            "another backslash before it (`\\\\`)."
        )
    )

    return embed, "Property: `response` (2)", "Property: response (2)"


def get_property_uses_wildcards():
    embed = discord.Embed()

    embed.add_field(
        inline=False, name="Description", value=(
            "This argument is optional. If you don't specify it, the bot will assume that you don't want to "
            "use wildcards.\n"
            "**This argument is ignored if you use the `regex` mode.**\n"
            "\n"
            "Wildcards allow you to use the special characters `?` and `*` in your pattern, both of them "
            "holding special meanings.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="`?` matches any single character", value=(
            "For example, the pattern `\"p?n\"` will match `\"pin\"`, `\"pan\"`, `\"pun\"`, etc.\n" +
            BLANK
        )
    )
    embed.add_field(
        inline=False, name="`*` matches any number of characters, including none", value=(
            "For example, the pattern `\"p*n\"` will match `\"pn\"`, `\"pin\"`, `\"pan\"`, `\"pelican\"`, etc.\n"
            "The pattern `\"p*\"` essentially means \"any word that starts with `p`\".\n"
            "The pattern `\"I love c* so much\"` will match `\"I love cats so much\"`, `\"I love cookies so much\"` "
            "etc.\n"
            "The pattern `\"I love p*c?ns and p?ns so* much\"` will match `\"I love pelicans and pens sooo much\"`, "
            "`\"I love pelicans and pans so much\"`, etc."
        )
    )
    embed.add_field(
        inline=False, name="", value=(
            "Keep in mind that these wildcards only apply to **single words**. If you want a more advanced "
            "logic, consider using the `regex` mode.\n"
            "\n"
            "[**Advanced**] If you want to use the special characters `?` and `*` in your pattern "
            "without them being treated as wildcards, you can escape them by adding "
            "a backslash (`\\`) before them.\n"
            "For example, if you want to match the messages `\"Where did mum go?\"` and `\"Where did mom go?\"`, "
            "you can use the pattern `\"Where did m?m go\\?\"`.\n"
            "The first `?` is an actual wildcard, whereas the second `?` is just a normal character."
        )
    )

    return embed, "Property: `uses_wildcards`", "Property: uses_wildcards"
