import asyncio
import json
import logging
import os
import random
import time
import urllib.request
import xml.etree.ElementTree as ElementTree

import discord
import redis
from cleverbot import Cleverbot

try:
    redis_address = os.environ['REDIS_ADDRESS']
except KeyError:
    redis_address = 'redis'
client = discord.Client()
cb = Cleverbot()
r = redis.StrictRedis(host=redis_address, port=6379, db=0)
log_time = time.strftime('%Y-%m-%d_%H:%M:%S')
try:
    os.mkdir('logs')
except FileExistsError:
    pass
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s ', datefmt='%d/%m/%Y %H:%M:%S',
                    filename='logs/{0}.log'.format(log_time), level=logging.DEBUG)
last_message = None


@client.event
async def on_ready():
    print('Initializing bot...')
    await redis_check()
    print('--------------------------------------------------------------------')
    print('Discord API version is: {0}'.format(discord.__version__))
    print('Logfile: logs/{0}.log'.format(log_time))
    if discord.opus.is_loaded():
        logging.info('Opus successfully loaded')
        print('Opus successfully loaded')
    else:
        logging.error('Opus failed to load!')
        print('Opus failed to load. Voice functionality is unavailable')
    logging.info('Successfully logged in as {0} with id {1}'.format(client.user.name, client.user.id))
    print('Successfully logged in as {0} with id {1}'.format(client.user.name, client.user.id))
    try:
        status = redis_get('discord:status')
        if not status:
            status = 'https://git.io/vKcCg'
        await client.change_status(game=discord.Game(name=status))
        logging.info('Status is set to: \'Playing {0}\''.format(status))
        print('Status message: \'Playing {0}\''.format(status))
    except AttributeError or TypeError:
        logging.error('No status message set')
        print('No status message')
    print('--------------------------------------------------------------------')
    print('Bot is now awaiting for client messages...')
    print('And calling redis. Last message id is {0}'.format(last_message))


@client.event
async def on_member_join(member):
    await client.send_message(member.server, 'Привет, {0}\nДобро пожаловать на сервер {1}!'
                              .format(member.mention, member.server.name))


@client.event
async def on_message(message):
    content = message.content
    if message.author != client.user:
        if content.startswith('!'):
            try:
                prefix_and_command, arguments = content.split(maxsplit=1)
                arguments = arguments.split()
            except ValueError:
                prefix_and_command = content
                arguments = ''
            prefix = prefix_and_command[0]
            command = prefix_and_command[1:]
            logging.debug('Prefix: {0}'.format(prefix))
            logging.debug('Command: {0}'.format(command))
            arguments_string = ''
            for i in arguments:
                arguments_string = arguments_string + i + ' '
            logging.debug('Arguments: {0}'.format(arguments_string))
            if command == 'radio':
                radio()
            elif command == 'np':
                await client.send_message(message.channel, now_playing())
            elif command == 'issue':
                await client.send_message(message.channel, issue())
            elif command == 'get':
                await client.send_message(message.channel, redis_get(arguments[0]))
            elif command == 'set':
                await client.send_message(message.channel, redis_set(arguments[0], arguments[1]))
        elif client.user in message.mentions:
            # CleverBot-интеграция
            time_to_wait = random.random() * 10
            await client.send_typing(message.channel)
            await asyncio.sleep(time_to_wait)
            answer = cb.ask(message.content.replace(message.author.mention + ' ', '')) \
                .encode('ISO-8859-1').decode('utf-8')
            await client.send_message(message.channel, '{0} {1}'.format(message.author.mention, answer))
        elif message.channel == discord.utils.find(lambda c: c.name == 'dev', message.server.channels):
            forward(message)
    print('[{1}] {0} {3}/#{4} {2}: {5}'.
          format(time.strftime('%H:%M:%S'),
                 last_message, message.author.name, message.server, message.channel, message.content))


async def redis_check():
    global last_message
    if redis_get('message_query:last') is not None:
        last_message = int(redis_get('message_query:last'))
    else:
        last_message = 0
    return True
    while True:
        if redis_get('message_query:last') is not None:
            last_message = int(redis_get('message_query:last'))
        else:
            last_message = 0
        # Частота опроса Redis (точнее, время ожидания до следующего опроса)
        # 1 = 1 раз в секунду, 2 = каждые две секунды
        await asyncio.sleep(1)


def redis_get(key):
    try:
        content_b = r.get(key)
        content_str = content_b.decode('utf-8')
        logging.debug('Got {0} from Redis. Value is: {1}'.format(key, content_str))
        return content_str
    except AttributeError:
        logging.error('Could not get {0} from Redis'.format(key))
        return False


def redis_set(key, value):
    try:
        r.set(key, value)
        logging.debug('Set {0} to {1}'.format(key, value))
        return True
    except AttributeError:
        logging.error('Could not set {0} to {1} in Redis'.format(key, value))
        return False


def json_compose(message):
    json_msg = \
        {'id': last_message,
         'author': message.author.name,
         'content': message.content,
         'origin': 'discord'}
    return json.dumps(json_msg)


def json_parse(json_text):
    message = json.loads(json_text.replace("'", "\""))
    return '\nType: {0}\nContent: {1}\nParsed: \n\nID: {3}\nAuthor: {2}\nContent: {5}\nOrigin: {4}'.\
        format(type(message),
               message,
               message.get('author'),
               message.get('id'),
               message.get('origin'),
               message.get('content'))


def forward(message):
    global last_message
    composed_msg = json_compose(message)
    redis_set('message_query:id{0}'.format(last_message), composed_msg)
    last_message += 1
    redis_set('message_query:last', last_message)
    logging.debug('Message id{0} forwarded'.format(last_message))


def issue():
    # TODO GitHub Issues Integration
    pass


def radio():
    # TODO Radio functionality
    pass


def now_playing():
    response = urllib.request.urlopen('http://radioparadise.com/xml/now.xml')
    tree = ElementTree.parse(response)
    root = tree.getroot()
    return '#nowplaying: {0} - {1} с альбома {2} \n' \
           'http://www.radioparadise.com/rp_2.php?#name=Music&file=songinfo&song_id={3}'.\
        format(root[0][3].text, root[0][4].text, root[0][6].text, root[0][5].text)


try:
    token = redis_get('discord:token')
    client.loop.create_task(redis_check())
    client.run(token)
except FileNotFoundError:
    client.logout()
    print('Logged out')
