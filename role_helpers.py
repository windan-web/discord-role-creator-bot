import discord
from typing import Optional, Dict, List, Tuple
import re
from discord.ext import commands
from functools import wraps

# Predefined role templates with their configurations
role_templates = {
    "lesser_creature": {
        "color": discord.Color.light_grey(),
        "permissions": {
            "view_channels": True,
            "read_messages": True,
            "send_messages": True,
            "add_reactions": True,
        },
        "hoist": False,
        "mentionable": False,
        "description": "Basic member with limited permissions"
    },
    "knight": {
        "color": discord.Color.blue(),
        "permissions": {
            "view_channels": True,
            "read_messages": True,
            "send_messages": True,
            "add_reactions": True,
            "attach_files": True,
            "mention_everyone": True,
            "mute_members": True,
            "deafen_members": True,
        },
        "hoist": True,
        "mentionable": True,
        "description": "Trusted member with moderate permissions"
    },
    "king": {
        "color": discord.Color.gold(),
        "permissions": {
            "administrator": False,  # Kings don't have full admin
            "manage_roles": True,
            "manage_channels": True,
            "manage_messages": True,
            "kick_members": True,
            "ban_members": True,
            "mention_everyone": True,
            "mute_members": True,
            "deafen_members": True,
            "move_members": True,
        },
        "hoist": True,
        "mentionable": True,
        "description": "High-level administrator with extensive control"
    },
    "god": {
        "color": discord.Color.purple(),
        "permissions": {
            "administrator": True,  # Gods have full administrative access
        },
        "hoist": True,
        "mentionable": True,
        "description": "Supreme role with complete server control"
    }
}

def parse_color(color_str: str) -> discord.Color:
    """Convert a color string to discord.Color object."""
    color_dict = {
        "red": discord.Color.red(),
        "blue": discord.Color.blue(),
        "green": discord.Color.green(),
        "yellow": discord.Color.gold(),
        "purple": discord.Color.purple(),
        "orange": discord.Color.orange(),
        "white": discord.Color.light_gray(),
        "black": discord.Color.default()
    }

    if color_str.lower() in color_dict:
        return color_dict[color_str.lower()]

    hex_match = re.match(r'^#?([A-Fa-f0-9]{6})$', color_str)
    if hex_match:
        hex_color = int(hex_match.group(1), 16)
        return discord.Color(hex_color)

    return discord.Color.default()

def parse_permissions(permission_str: str) -> Dict[str, bool]:
    """Convert permission string to dictionary of permissions."""
    available_permissions = {
        "admin": "administrator",
        "kick": "kick_members",
        "ban": "ban_members",
        "manage_roles": "manage_roles",
        "manage_channels": "manage_channels",
        "manage_messages": "manage_messages",
        "mention_everyone": "mention_everyone",
        "mute": "mute_members",
        "deafen": "deafen_members",
        "move": "move_members",
        "view_channels": "view_channels",
        "send_messages": "send_messages",
        "read_messages": "read_messages",
        "attach_files": "attach_files",
        "add_reactions": "add_reactions"
    }

    permissions = {}
    perms = permission_str.lower().split(',')

    for perm in perms:
        perm = perm.strip()
        if perm.startswith('-'):
            perm = perm[1:]
            value = False
        else:
            value = True

        if perm in available_permissions:
            permissions[available_permissions[perm]] = value

    return permissions

def format_role_info(role: discord.Role) -> str:
    """Format role information for display."""
    info = [
        f"Role: {role.name}",
        f"ID: {role.id}",
        f"Color: #{hex(role.color.value)[2:].zfill(6)}",
        f"Position: {role.position}",
        f"Mentionable: {role.mentionable}",
        f"Hoisted: {role.hoist}",
        "\nPermissions:"
    ]

    for perm, value in role.permissions:
        if value:
            info.append(f"✅ {perm}")

    return "\n".join(info)

def get_template_info() -> str:
    """Get information about available role templates."""
    info = ["Available Role Templates:"]
    for name, template in role_templates.items():
        info.append(f"\n{name.replace('_', ' ').title()}:")
        info.append(f"Description: {template['description']}")
        info.append("Key Permissions: " + ", ".join(
            [k for k, v in template['permissions'].items() if v]
        ))
    return "\n".join(info)

def has_role_permission(role_name: str):
    """Decorator to check if user has the required role."""
    async def predicate(ctx):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"The {role_name} role doesn't exist in this server!")
            return False
        return role in ctx.author.roles
    return commands.check(predicate)

def get_role_commands_info() -> str:
    """Get information about special commands available for each role."""
    info = ["Special Commands by Role:"]

    info.extend([
        "\nKnight Commands:",
        "!knightannounce [message] - Send an announcement with special formatting",
        "!knightmute @user [duration] - Temporarily mute a user",

        "\nKing Commands:",
        "!kingdecree [message] - Make a server-wide decree",
        "!kingrename @user [new_name] - Rename a user",
        "!kingexile @user - Kick a user from the server",

        "\nGod Commands:",
        "!godsmite @user - Ban a user dramatically",
        "!godblessing @user - Grant a random special permission",
        "!godspeak [message] - Send a divine message to all channels"
    ])

    return "\n".join(info)