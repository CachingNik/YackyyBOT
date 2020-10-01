from discord.ext import commands
import aiml
from pymongo import MongoClient
import os
import datetime


client = commands.Bot(command_prefix="!")


cluster = MongoClient(os.getenv("DB"))
db = cluster["QG_Data"]
cdu = db["cooldown_user"]


BRAIN_FILE = "brain.dump"
k = aiml.Kernel()


@client.event
async def on_ready():
    k.setBotPredicate("name", "Yackyy")
    if os.path.exists(BRAIN_FILE):
        print("Loading from brain file...")
        k.loadBrain(BRAIN_FILE)
    else:
        print("Parsing aiml files...")
        k.bootstrap(learnFiles="std-startup.xml", commands="load aiml b")
        print("Saving brain file...")
        k.saveBrain(BRAIN_FILE)
    print("Bot is Ready")


@client.event
async def on_message(msg):

    if msg.channel.name != "chat-with-yackyy":
        return

    if msg.content == "/res":
        return

    if msg.author.bot:
        return

    my_query = {"User": msg.author.name}

    if msg.author.name != "BratherNik":
        if cdu.count_documents(my_query) > 0:
            for user in cdu.find(my_query):
                duration = datetime.datetime.now() - user['Time']
                if user['Score'] == 10 and duration.total_seconds() < 1800:
                    print("Time left to remove cool down:", 300 - duration.total_seconds())
                    if duration.total_seconds() < 300:
                        await msg.channel.send(str(msg.author.mention) + ", You are on cool down for " + "{:.2f}".format(300-duration.total_seconds()) + "secs")
                        print("Cool Down Mode!")
                        return
                    else:
                        cdu.update_one(my_query, {"$set": {'Score': 1, 'Time': datetime.datetime.now()}})
                        print("User cool down removed.")
                else:
                    cdu.update_one(my_query, {"$inc": {"Score": 1}, "$set": {"Time": datetime.datetime.now()}})
                    print("Updating cds for a user...")
        else:
            post = {"User": msg.author.name, "Score": 1, "Time": datetime.datetime.now()}
            cdu.insert_one(post)
            print("Inserting new user cds...")

    text = msg.content
    for ch in ['/', "'", ".", "\\", "(", ")", '"', '\n', '@', '<', '>']:
        text = text.replace(ch, '')

    response = k.respond(text)
    response = response.replace("://", "")
    response = response.replace("@", "")
    response = "`@%s`: %s" % (msg.author.name, response)

    await msg.channel.send(response)


client.run(os.getenv("TOKEN"))
