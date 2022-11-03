import os
import sys
import asyncio
from config import *
from translation import BATCH
from plugins.database import collection
from plugins.add_movies import caption
from config import ADMINS
from pyrogram import Client, filters
from pyrogram.errors.exceptions.forbidden_403 import ChatWriteForbidden
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from helpers.get_movie import get_movies
from helpers.send_movies import send_movie_pvt_handler
from helpers.validate_query import validate_q
from helpers.auto_delete import auto_delete
from pyrogram import Client, filters
from pyrogram.types import Message
from config import *
from translation import *
import urllib.parse


cancel_button = [[
    InlineKeyboardButton('Cancel 🔐', callback_data='cancel_process')
]
]


def escape_url(str):
    return urllib.parse.quote(str)


@Client.on_message(filters.private & filters.text & filters.incoming)
async def find_movies(c: Client, m:Message):
    print(True)
    try:
        reply_markup = None
        query = m.text
        query = await validate_q(query)
        if query and m.text:
            reply_markup = await get_movies(query=query, m=m)
            if reply_markup is None or reply_markup is False: 
                await send_movie_pvt_handler(m=m, query=query, reply_markup=reply_markup)

        reply_markup = reply_markup if reply_markup is not None else None
        await auto_delete(m, reply_markup) 
    except Exception as e:
        print(e)

@Client.on_message(filters.private & filters.command('batch'))
async def batch(c, m):
    if len(m.command) < 2:
        await m.reply_text(BATCH)
    else:
        channel_id = m.command[1]
        if channel_id.startswith("@"):
            channel_id = channel_id.split("@")[1]
        elif channel_id.startswith("-100"):
            channel_id = int(channel_id)
        elif channel_id.startswith("t.me"):
            channel_id = channel_id.split("/")[-1]
            if channel_id.startswith(("1", "2", "3", "4", "5", "6", "7", "8", "9", "0")):
                channel_id = int(channel_id)
            else:
                channel_id = str(channel_id)
        elif channel_id.startswith("https"):
            channel_id = channel_id.split("/")[-1]

        buttons = [
            [
                InlineKeyboardButton('Batch Short 🏕', callback_data=f'batch_{channel_id}')
            ],
            [
                InlineKeyboardButton('Cancel 🔐', callback_data='cancel')
            ]
        ]

        return await m.reply(text=f"Are you sure you want to batch short?\n\nChannel: {channel_id}",
                        reply_markup=InlineKeyboardMarkup(buttons))



@Client.on_callback_query(filters.regex(r'^cancel') | filters.regex(r'^batch'))
async def cancel(c:Client, m):
    if m.data == "cancel":
        await m.message.delete()
    elif m.data.startswith("batch"):
        info_text = "Batch Shortening Started!\n\n Channel: {}\n\nTo Cancel /cancel\n\n Message Saved: {}"
        channel_id = m.data.split("_")[1]

        count = 0 
        try:
            txt = await c.send_message(channel_id, ".")
            await txt.delete()

        except ChatWriteForbidden:
            await m.message.edit("Bot is not an admin in the given channel")
        await m.message.edit(text=info_text.format(channel_id, 0))
    
        for i in range(txt.id, 1, -1):
            
            try:
                post = await c.get_messages(channel_id, i)
                if post.caption:
                    message = post.caption
                  

                    collection.insert_one(
                        {"caption": message.markdown,
                            'title': message.splitlines()[0]}
                    )
                    count += 1
                    if count % 20 == 0:
                        await m.message.edit(text=info_text.format(channel_id, count))

            
            except Exception as e:
                print(e)
                await c.send_message(
                    chat_id=OWNER_ID,
                    text=e
                )

        return await m.message.edit(text=f"Message Saved: {count}" + "\n\nBatch Completed")



@Client.on_message(filters.command('cancel'))
async def stop_button(c, m):
    if m.from_user.id in ADMINS:
        print("Cancelled")
        msg = await c.send_message(
            text="<i>Trying To Stoping.....</i>",
            chat_id=m.chat.id
        )
        await asyncio.sleep(5)
        await msg.edit("Batch Shortening Stopped Successfully 👍")
        os.execl(sys.executable, sys.executable, *sys.argv)
