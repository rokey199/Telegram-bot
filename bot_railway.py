
import os
import asyncio
import sqlite3
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telethon import TelegramClient, events, Button

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

conn = sqlite3.connect('posts.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        title TEXT,
        video_link TEXT,
        group_link1 TEXT,
        group_link2 TEXT,
        target_group_id INTEGER,
        post_time TEXT
    )
''')
conn.commit()

scheduler = AsyncIOScheduler()
scheduler.start()

async def post_to_group(post):
    buttons = [
        [
            Button.url("Join Group A", post[4]),
            Button.url("Join Group B", post[5])
        ]
    ]
    await bot.send_file(
        post[6],
        file=post[1],
        caption=f"**{post[2]}**\n\nVideo Link: {post[3]}",
        buttons=buttons
    )

def load_and_schedule_posts():
    cursor.execute("SELECT * FROM posts")
    for post in cursor.fetchall():
        run_time = datetime.strptime(post[7], "%Y-%m-%d %H:%M")
        scheduler.add_job(post_to_group, 'date', run_date=run_time, args=[post])

load_and_schedule_posts()

@bot.on(events.NewMessage(from_users=OWNER_ID, pattern='/newpost'))
async def handler(event):
    await event.respond("Send the thumbnail image...")

    image_event = await bot.wait_for(events.NewMessage(from_users=OWNER_ID, func=lambda e: e.photo))
    file = await image_event.download_media()

    await event.respond("Now send the *title*.", parse_mode='markdown')
    title_event = await bot.wait_for(events.NewMessage(from_users=OWNER_ID))
    title = title_event.text

    await event.respond("Send the *video link*.", parse_mode='markdown')
    link_event = await bot.wait_for(events.NewMessage(from_users=OWNER_ID))
    video_link = link_event.text

    await event.respond("Send *Group Link 1*.", parse_mode='markdown')
    g1_event = await bot.wait_for(events.NewMessage(from_users=OWNER_ID))
    group_link1 = g1_event.text

    await event.respond("Send *Group Link 2*.", parse_mode='markdown')
    g2_event = await bot.wait_for(events.NewMessage(from_users=OWNER_ID))
    group_link2 = g2_event.text

    await event.respond("Send *Target Group ID* (as number).", parse_mode='markdown')
    group_event = await bot.wait_for(events.NewMessage(from_users=OWNER_ID))
    target_group_id = int(group_event.text)

    await event.respond("Send *Post Time* in `YYYY-MM-DD HH:MM` format (24hr clock).", parse_mode='markdown')
    time_event = await bot.wait_for(events.NewMessage(from_users=OWNER_ID))
    post_time = time_event.text

    cursor.execute('''INSERT INTO posts (file_id, title, video_link, group_link1, group_link2, target_group_id, post_time)
                      VALUES (?, ?, ?, ?, ?, ?, ?)''',
                   (file, title, video_link, group_link1, group_link2, target_group_id, post_time))
    conn.commit()

    cursor.execute("SELECT * FROM posts ORDER BY id DESC LIMIT 1")
    post = cursor.fetchone()
    scheduler.add_job(post_to_group, 'date', run_date=datetime.strptime(post[7], "%Y-%m-%d %H:%M"), args=[post])

    await event.respond("Post scheduled successfully!")

print("Bot is running...")
bot.run_until_disconnected()
