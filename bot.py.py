import discord
import os
from discord.ext import commands
import random
from typing import Optional
from dotenv import load_dotenv
from utils.role_helpers import parse_color, parse_permissions, format_role_info, role_templates, get_template_info
import asyncio
from datetime import datetime, timedelta
from utils.role_helpers import has_role_permission, get_role_commands_info
from keep_alive import keep_alive # Added import statement

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
last_created_role = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name="createrole")
@commands.has_permissions(manage_roles=True)
async def create_role(ctx, name: str, *, args: Optional[str] = ""):
    """Create a new role with specified name, color, and permissions
    Usage: !createrole RoleName color=red perms=kick,ban,manage_messages mentionable=true hoisted=true
    """
    guild = ctx.guild

    # Parse arguments
    args_dict = dict(arg.split('=') for arg in args.split() if '=' in arg)

    # Set up role parameters
    role_color = parse_color(args_dict.get('color', 'default'))
    permissions = discord.Permissions()

    if 'perms' in args_dict:
        perm_dict = parse_permissions(args_dict['perms'])
        permissions.update(**perm_dict)

    mentionable = args_dict.get('mentionable', 'false').lower() == 'true'
    hoisted = args_dict.get('hoisted', 'false').lower() == 'true'

    try:
        role = await guild.create_role(
            name=name,
            color=role_color,
            permissions=permissions,
            mentionable=mentionable,
            hoist=hoisted
        )
        last_created_role[guild.id] = role
        await ctx.send(f"Created role {role.mention} successfully!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to create roles!")
    except discord.HTTPException:
        await ctx.send("Failed to create role. Please try again.")

@bot.command(name="roleinfo")
async def role_info(ctx, *, role_name: str):
    """Display detailed information about a role
    Usage: !roleinfo RoleName
    """
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"Role '{role_name}' not found!")
        return

    await ctx.send(f"```\n{format_role_info(role)}\n```")

@bot.command(name="deleterole")
@commands.has_permissions(manage_roles=True)
async def delete_role(ctx, *, role_name: str):
    """Delete a role
    Usage: !deleterole RoleName
    """
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"Role '{role_name}' not found!")
        return

    try:
        await role.delete()
        await ctx.send(f"Deleted role '{role_name}' successfully!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to delete this role!")
    except discord.HTTPException:
        await ctx.send("Failed to delete role. Please try again.")

@bot.command(name="assignrole")
@commands.has_permissions(manage_roles=True)
async def assign_role(ctx, member: discord.Member, *, role_name: str):
    """Assign a role to a member
    Usage: !assignrole @Member RoleName
    """
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"Role '{role_name}' not found!")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"Assigned role {role.mention} to {member.mention}")
    except discord.Forbidden:
        await ctx.send("I don't have permission to assign this role!")
    except discord.HTTPException:
        await ctx.send("Failed to assign role. Please try again.")

@bot.command(name="removerole")
@commands.has_permissions(manage_roles=True)
async def remove_role(ctx, member: discord.Member, *, role_name: str):
    """Remove a role from a member
    Usage: !removerole @Member RoleName
    """
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    if not role:
        await ctx.send(f"Role '{role_name}' not found!")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"Removed role {role.mention} from {member.mention}")
    except discord.Forbidden:
        await ctx.send("I don't have permission to remove this role!")
    except discord.HTTPException:
        await ctx.send("Failed to remove role. Please try again.")

@bot.command(name="moverole")
@commands.has_permissions(manage_roles=True)
async def moverole(ctx, *, args: str):
    """Move a role's position
    Usage: 
    !moverole RoleName move up 2
    !moverole RoleName move down 3
    !moverole RoleName move over ReferenceName
    !moverole RoleName move under ReferenceName
    !moverole RoleName moveto top/bottom
    """
    parts = args.split(" ")
    role_name = ""
    direction = ""
    amount = None
    reference_role = None

    for i, part in enumerate(parts):
        if part.lower() in ["move", "up", "down", "over", "under", "moveto", "top", "bottom"]:
            direction = " ".join(parts[i:])
            break
        role_name += part + " "

    role_name = role_name.strip()
    if direction.startswith("move over") or direction.startswith("move under"):
        direction, reference_role = direction.split(" ", 2)[1:]
    elif direction.startswith("move up") or direction.startswith("move down"):
        split_dir = direction.split(" ")
        if len(split_dir) > 2 and split_dir[2].isdigit():
            amount = int(split_dir[2])
        direction = split_dir[1]
    elif direction.startswith("moveto"):
        reference_role = direction.split(" ")[1]
        direction = "moveto"

    try:
        guild = ctx.guild
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            await ctx.send(f'Role `{role_name}` not found.')
            return

        roles = guild.roles
        current_index = roles.index(role)

        if direction == "up" and amount:
            new_index = max(1, current_index - amount)
        elif direction == "down" and amount:
            new_index = min(len(roles) - 1, current_index + amount)
        elif direction == "over" and reference_role:
            ref_role = discord.utils.get(guild.roles, name=reference_role)
            if not ref_role:
                await ctx.send(f'Reference role `{reference_role}` not found.')
                return
            new_index = roles.index(ref_role) - 1
        elif direction == "under" and reference_role:
            ref_role = discord.utils.get(guild.roles, name=reference_role)
            if not ref_role:
                await ctx.send(f'Reference role `{reference_role}` not found.')
                return
            new_index = roles.index(ref_role) + 1
        elif direction == "moveto" and reference_role:
            if reference_role.lower() == "top":
                new_index = 1
            elif reference_role.lower() == "bottom":
                new_index = len(roles) - 1
            else:
                await ctx.send("Invalid position! Use `top` or `bottom`.")
                return
        else:
            await ctx.send("Invalid command usage.")
            return

        new_roles = roles[:]
        new_roles.pop(current_index)
        new_roles.insert(new_index, role)
        await guild.edit_role_positions({r: i for i, r in enumerate(new_roles)})
        await ctx.send(f'Moved role `{role_name}` successfully.')
    except discord.Forbidden:
        await ctx.send("I don't have permission to move roles!")
    except discord.HTTPException:
        await ctx.send("Failed to move role. Please try again.")

@bot.command(name="cleanroles")
@commands.has_permissions(manage_roles=True)
async def clean_roles(ctx, *, pattern: Optional[str] = None):
    """Delete unused roles or roles matching a pattern
    Usage: !cleanroles [pattern]
    """
    guild = ctx.guild
    deleted_count = 0

    for role in guild.roles[1:]:  # Skip @everyone role
        if pattern:
            if pattern.lower() not in role.name.lower():
                continue

        if not any(member.roles for member in guild.members if role in member.roles):
            try:
                await role.delete()
                deleted_count += 1
            except (discord.Forbidden, discord.HTTPException):
                continue

    await ctx.send(f"Cleaned up {deleted_count} unused roles!")

@bot.command(name="createrolepreset")
@commands.has_permissions(manage_roles=True)
async def create_role_preset(ctx, template_name: str, role_name: Optional[str] = None):
    """Create a role using a predefined template
    Usage: !createrolepreset template_name [custom_role_name]
    Available templates: lesser_creature, knight, king, god
    """
    template_name = template_name.lower()
    if template_name not in role_templates:
        await ctx.send(f"Template '{template_name}' not found!\n\n{get_template_info()}")
        return

    template = role_templates[template_name]
    name = role_name if role_name else template_name.replace('_', ' ').title()

    try:
        role = await ctx.guild.create_role(
            name=name,
            color=template['color'],
            permissions=discord.Permissions(**template['permissions']),
            hoist=template['hoist'],
            mentionable=template['mentionable'],
            reason=f"Created using {template_name} template"
        )

        last_created_role[ctx.guild.id] = role
        await ctx.send(f"Created role {role.mention} using the {template_name} template!\n```\n{format_role_info(role)}\n```")
    except discord.Forbidden:
        await ctx.send("I don't have permission to create roles!")
    except discord.HTTPException:
        await ctx.send("Failed to create role. Please try again.")

@bot.command(name="listtemplates")
async def list_templates(ctx):
    """List all available role templates and their details"""
    await ctx.send(f"```\n{get_template_info()}\n```")


@bot.command(name="specialcommands")
async def list_special_commands(ctx):
    """List all special commands available for different roles"""
    await ctx.send(f"```\n{get_role_commands_info()}\n```")

# Knight Commands
@bot.command(name="knightannounce")
@has_role_permission("Knight")
async def knight_announce(ctx, *, message: str):
    """Send an announcement with special formatting
    Usage: !knightannounce Your message here
    """
    embed = discord.Embed(
        title="📢 Knight's Announcement",
        description=message,
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Announced by Knight {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command(name="knightmute")
@has_role_permission("Knight")
async def knight_mute(ctx, member: discord.Member, duration: int = 5):
    """Temporarily mute a user
    Usage: !knightmute @user [duration_in_minutes]
    """
    if duration > 60:
        await ctx.send("Knights can only mute for up to 60 minutes!")
        return

    try:
        await member.edit(mute=True)
        await ctx.send(f"🔇 {member.mention} has been muted for {duration} minutes by Knight {ctx.author.display_name}")
        await asyncio.sleep(duration * 60)
        await member.edit(mute=False)
        await ctx.send(f"🔊 {member.mention} has been unmuted")
    except discord.Forbidden:
        await ctx.send("I don't have permission to mute members!")

# King Commands
@bot.command(name="kingdecree")
@has_role_permission("King")
async def king_decree(ctx, *, decree: str):
    """Make a server-wide decree
    Usage: !kingdecree Your royal decree here
    """
    embed = discord.Embed(
        title="👑 Royal Decree",
        description=decree,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Decreed by King {ctx.author.display_name}")

    # Pin the decree
    message = await ctx.send(embed=embed)
    try:
        await message.pin()
    except discord.Forbidden:
        await ctx.send("Could not pin the decree (insufficient permissions)")

@bot.command(name="kingrename")
@has_role_permission("King")
async def king_rename(ctx, member: discord.Member, *, new_name: str):
    """Rename a user
    Usage: !kingrename @user New Name
    """
    old_name = member.display_name
    try:
        await member.edit(nick=new_name)
        await ctx.send(f"👑 By royal decree, {old_name} shall now be known as {new_name}")
    except discord.Forbidden:
        await ctx.send("I don't have permission to change nicknames!")

@bot.command(name="kingexile")
@has_role_permission("King")
async def king_exile(ctx, member: discord.Member, *, reason: str = "Royal decree"):
    """Kick a user from the server
    Usage: !kingexile @user [reason]
    """
    try:
        await member.kick(reason=f"Exiled by King {ctx.author.display_name}: {reason}")
        await ctx.send(f"👑 {member.name} has been exiled from the realm!")
    except discord.Forbidden:
        await ctx.send("I don't have permission to exile members!")

# God Commands
@bot.command(name="godsmite")
@has_role_permission("God")
async def god_smite(ctx, member: discord.Member, *, reason: str = "Divine judgment"):
    """Ban a user dramatically
    Usage: !godsmite @user [reason]
    """
    smite_messages = [
        "⚡ Divine lightning strikes {user}!",
        "🌋 The heavens open up to cast {user} into the abyss!",
        "💫 {user} has been banished to the shadow realm!",
        "🌟 {user} faces divine judgment!"
    ]

    try:
        message = random.choice(smite_messages).format(user=member.name)
        await ctx.send(message)
        await asyncio.sleep(2)  # Dramatic pause
        await member.ban(reason=f"Smited by God {ctx.author.display_name}: {reason}")
        await ctx.send(f"The divine will has been carried out. {member.name} has been banished! ⚡")
    except discord.Forbidden:
        await ctx.send("I lack the divine permission to smite!")

@bot.command(name="godblessing")
@has_role_permission("God")
async def god_blessing(ctx, member: discord.Member):
    """Grant a random special permission to a user
    Usage: !godblessing @user
    """
    blessings = [
        ("attach_files", "share sacred scrolls"),
        ("mention_everyone", "call upon all believers"),
        ("manage_messages", "moderate divine messages"),
        ("move_members", "guide lost souls")
    ]

    blessing = random.choice(blessings)
    try:
        # Create a new role with the blessed permission
        role = await ctx.guild.create_role(
            name=f"Blessed with {blessing[1]}",
            permissions=discord.Permissions(**{blessing[0]: True}),
            color=discord.Color.purple(),
            reason=f"Divine blessing from {ctx.author.display_name}"
        )
        await member.add_roles(role)
        await ctx.send(f"✨ {member.mention} has been blessed with the power to {blessing[1]}!")
    except discord.Forbidden:
        await ctx.send("I lack the divine permission to grant blessings!")

@bot.command(name="godspeak")
@has_role_permission("God")
async def god_speak(ctx, *, message: str):
    """Send a divine message to all channels
    Usage: !godspeak Your divine message here
    """
    embed = discord.Embed(
        title="📿 Divine Message",
        description=message,
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Spoken by {ctx.author.display_name}, Voice of the Divine")

    sent_count = 0
    for channel in ctx.guild.text_channels:
        try:
            await channel.send(embed=embed)
            sent_count += 1
        except discord.Forbidden:
            continue

    await ctx.send(f"Your divine message has been spread to {sent_count} channels! 🙏")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param.name}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument provided!")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# Get the token from environment variables
TOKEN = os.getenv('ur bot token (u need it for the bot to work blud)')
if not TOKEN:
    raise ValueError("No Discord bot token found. Please set the DISCORD_BOT_TOKEN environment variable.")

# Keep the bot alive
keep_alive() # Added keep_alive() call
bot.run(TOKEN)