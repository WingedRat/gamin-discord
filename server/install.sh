#!/usr/bin/env bash
docker run --name gamin-redis -d redis redis-server --appendonly yes
docker run -d -t --name gamin-discord --link gamin-redis:redis -d wingedrat/gamin-discord
# docker run -d -t --name gamin-tg --link gamin-redis:redis -d wingedrat/telegram-discord