import discord
from discord.ext import commands
import aiml
from pymongo import MongoClient
import os
import datetime


client = commands.Bot(command_prefix='!')


cluster = MongoClient(os.getenv("DB"))
db = cluster["QG_Data"]
cdu = db["cooldown_user"]


BRAIN_FILE = "brain.dump"
k = aiml.Kernel()


@client.event
async def on_ready():
    channel = client.get_channel(760587314207522826)
    k.setBotPredicate("name", "Yackyy")
    if os.path.exists(BRAIN_FILE):
        print("Loading from brain file...")
        k.loadBrain(BRAIN_FILE)
    else:
        print("Parsing aiml files...")
        k.bootstrap(learnFiles="std-startup.xml", commands="load aiml b")
        print("Saving brain file...")
        k.saveBrain(BRAIN_FILE)
    await channel.send("🟢 ONLINE")
    print("Bot is Ready")


@client.event
async def on_message(msg):

    if msg.channel.name != "chat-with-yackyy":
        return

    if msg.author.bot:
        return

    my_query = {"User_id": msg.author.id}

    if msg.author.id != 390755289038848000 and msg.content != "!cdlist":
        if cdu.count_documents(my_query) > 0:
            for user in cdu.find(my_query):
                if user['Score'] == 15:
                    duration = datetime.datetime.now() - user['Time']
                    if not user['Hit'] and duration.total_seconds() < 900:
                        cdu.update_one(my_query, {"$set": {"Time": datetime.datetime.now(), "Hit": True}})
                        print("Cool Down Mode!")
                        await msg.channel.send(str(msg.author.mention) + ", You are set to cool down for 3 mins.")
                        return
                    if duration.total_seconds() < 180:
                        print("Time left to remove cool down:", 180 - duration.total_seconds())
                        await msg.channel.send(str(msg.author.mention) + ", You are on cool down for " + "{:.2f}"
                                               .format(180-duration.total_seconds()) + " secs")
                        return
                    else:
                        cdu.update_one(my_query, {"$set": {"Score": 1, "Time": datetime.datetime.now(), "Hit": False}})
                        print("User cool down removed.")
                else:
                    duration = datetime.datetime.now() - user['Time']
                    if duration.total_seconds() > 900:
                        cdu.update_one(my_query, {"$set": {"Score": 1, "Time": datetime.datetime.now(), "Hit": False}})
                    else:
                        cdu.update_one(my_query, {"$inc": {"Score": 1}, "$set": {"Time": datetime.datetime.now()}})
                    print("Updating cds for a user...")
        else:
            post = {"User_name": msg.author.name, "User_id": msg.author.id, "Score": 1, "Time": datetime.datetime.now(),
                    "Hit": False}
            cdu.insert_one(post)
            print("Inserting new user cds...")

    text = msg.content
    for ch in ['/', "'", ".", "\\", "(", ")", '"', '\n', '@', '<', '>']:
        text = text.replace(ch, '')

    if text[0] != '!':
        response = k.respond(text)
        response = response.replace("://", "")
        response = response.replace("@", "")
        response = "`@%s`: %s" % (msg.author.name, response)
        await msg.channel.send(response)

    await client.process_commands(msg)


@client.command()
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    print("Shutting Down...")
    await ctx.send("🔴 OFFLINE")
    await ctx.bot.logout()


@client.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    await ctx.send("Resetting my brain...")
    print("Brain Reset")
    k.resetBrain()
    k.setBotPredicate("name", "Yackyy")
    k.learn("std-startup.xml")
    k.respond("load aiml b")
    k.saveBrain(BRAIN_FILE)
    await ctx.send("✅ Done")


@client.command()
async def cdlist(ctx):
    my_query = {"Hit": True}
    cd_users = "\n".join(user['User_name'] for user in cdu.find(my_query))
    cd_time_list = []
    for user in cdu.find(my_query):
        duration = (datetime.datetime.now() - user['Time']).total_seconds()
        if duration <= 180:
            cd_time_list.append("{:.2f}".format(180 - duration))
        else:
            cd_time_list.append("CD Time OVER")
    cd_time = "\n".join(cd_time_list)

    if cd_users == "":
        cd_users = "-"
    if cd_time == "":
        cd_time = "-"

    embed = discord.Embed(title="CD Users List", color=discord.Color.dark_magenta())
    embed.add_field(name="User", value=cd_users, inline=True)
    embed.add_field(name="Time Left (sec)", value=cd_time, inline=True)
    await ctx.send(embed=embed)


@client.command()
@commands.has_permissions(administrator=True)
async def sc(ctx):
    await ctx.send("https://github.com/CachingNik/YackyyBOT")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Access Denied")


client.run(os.getenv("TOKEN"))
