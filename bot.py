import discord
import redis
import logging
import time
import os
import urllib.request
import xml.etree.ElementTree as ElementTree

client = discord.Client()
r = redis.StrictRedis(host='localhost', port=6379, db=0)
log_time = time.strftime('%Y-%m-%d_%H:%M:%S')
try:
    os.mkdir('logs')
except FileExistsError:
    pass
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s: %(message)s ', datefmt='%d/%m/%Y %H:%M:%S',
                    filename='logs/{0}.log'.format(log_time), level=logging.DEBUG)


@client.event
async def on_ready():
    print('Initializing bot...')
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
        await client.change_status(game=discord.Game(name=redis_get('discord:status')))
        logging.info('Status is set to: \'Playing {0}\''.format(redis_get('discord:status')))
        print('Status message: \'Playing {0}\''.format(redis_get('discord:status')))
    except AttributeError or TypeError:
        logging.error('No status message set')
        print('No status message')
    print('--------------------------------------------------------------------')
    print('Bot is now awaiting for client messages...')
    last_message = int(redis_get('message_query:last'))
    print('And calling redis. Last message id is {0}'.format(last_message))
    while 1:
        time.sleep(1)
        message_query_last = int(redis_get('message_query:last'))
        if last_message != message_query_last:
            await client.send_message(
                discord.utils.find(lambda c: c.name == 'bots', discord.utils.find(lambda c: c.name == 'RogueLabs', client.servers).channels), '{0}: {1}'.format(
                    redis_get('message_query:id{0}:author'.format(message_query_last)),
                    redis_get('message_query:id{0}:content'.format(message_query_last))))
            last_message = message_query_last


@client.event
async def on_message(message):
    content = message.content
    if message.author != client.user:
        print(message.channel)
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
                radio(arguments, message.channel)
            elif command == 'np':
                await client.send_message(message.channel, now_playing())
            elif command == 'issue':
                await client.send_message(message.channel, issue())
            elif command == 'get':
                await client.send_message(message.channel, redis_get(arguments[0]))
            elif command == 'set':
                await client.send_message(message.channel, redis_set(arguments[0], arguments[1]))
        elif message.channel == discord.utils.find(lambda c: c.name == 'gamin', message.server.channels):
            forward(message)


def forward(message):
    message_query_last = int(redis_get('message_query:last'))
    if message_query_last is None:
        message_query_last = 0
    logging.debug('Message id{0} forwarded'.format(message_query_last))
    redis_set('message_query:id{0}:author'.format(message_query_last + 1), message.author)
    redis_set('message_query:id{0}:content'.format(message_query_last + 1), message.content)
    redis_set('message_query:id{0}:origin'.format(message_query_last + 1), 'discord')
    redis_set('message_query:last', message_query_last + 1)


def issue():
    pass


def radio(arguments, channel):
    pass


def now_playing():
    response = urllib.request.urlopen('http://radioparadise.com/xml/now.xml')
    tree = ElementTree.parse(response)
    root = tree.getroot()
    return '#nowplaying: {0} - {1} с альбома {2} \n' \
           'http://www.radioparadise.com/rp_2.php?#name=Music&file=songinfo&song_id={3}'.\
        format(root[0][3].text, root[0][4].text, root[0][6].text, root[0][5].text)


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


try:
    token = open('etc/token').read()
    client.run(token)
except FileNotFoundError:
    client.logout()
    print('Logged out')
