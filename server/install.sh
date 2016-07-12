#!/usr/bin/env bash
docker run --name gamin-redis -d redis redis-server --appendonly yes
echo 'Redis loaded'
docker run -d -t --name gamin-discord --link gamin-redis:redis wingedrat/gamin-discord
echo 'Discord bot loaded'
# docker run -d -t --name gamin-tg --link gamin-redis:redis wingedrat/telegram-discord
# echo 'Telegram bot loaded'
echo 'Service is working'