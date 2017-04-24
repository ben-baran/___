#!/usr/bin/env python

import asyncio
import websockets
import json
import queue
import time

import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

message_queue = queue.Queue()


class EventSocketPusher(FileSystemEventHandler):
    def on_any_event(self, event):
        message_queue.put([event.event_type, event.src_path])


settings = json.load(open('gibit.json'))
for path in settings['watch']:
    print(path)
    event_handler = EventSocketPusher()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()


async def filesys_info(websocket, path):
    for settings_root_path in settings['watch']:
        await websocket.send(json.dumps({'type': 'root_directory', 'path': settings_root_path}))
    # await websocket.send(json.dumps([entry for entry in os.walk('./test')]))

    while True:
        while not message_queue.empty():
            next_change = message_queue.get()
            message_data = {'type': 'system_change', 'change_type': next_change[0], 'change_dir': next_change[1]}
            message = json.dumps(message_data)
            await websocket.send(message)
            print(message)

        # name = await websocket.recv()
        # print("< {}".format(name))
        name = "auto"

        # greeting = "Hello {}!".format(name)
        # await websocket.send(greeting)
        # print("> {}".format(greeting))
        time.sleep(1)


start_server = websockets.serve(filesys_info, 'localhost', 8787)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
