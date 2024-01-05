from utils import dict_to_simple_namespace

desc = dict_to_simple_namespace({
    "command": {
        "help": "Display the help menu",
        "list": "Display a list of all triggers",
        "inspect": "Display information about a specific trigger",
        "add": "Add a new trigger",
        "edit": "Edit an existing trigger",
        "remove": "Remove an existing trigger",
        "setglobal": "Manage global values for optional properties",
        "reset": "Reset a trigger's optional properties to their default values"
    },
    "argument": {
        "mode": "The matching logic to use",
        "pattern": "The pattern to match",
        "response": "The response to send",
        "cooldown": "The cooldown in seconds",
        "case_sensitive": "Whether the pattern should be case sensitive",
        "avoid_links": "Whether the trigger should avoid searching inside links",
        "avoid_emotes": "Whether the trigger should avoid searching inside emotes",
        "start": "Whether the pattern should match at the start of the message",
        "end": "Whether the pattern should match at the end of the message",
        "inspect": {
            "id": "The ID of the trigger to inspect"
        },
        "edit": {
            "id": "The ID of the trigger to edit",
            "new_id": "The new ID (position) of the trigger"
        },
        "remove": {
            "id": "The ID of the trigger to remove"
        },
        "reset": {
            "id": "The ID of the trigger to whose property to reset",
            "property": "The property to reset"
        }
    }
})
