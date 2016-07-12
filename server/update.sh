#!/usr/bin/env bash
docker stop gamin-discord
docker rm gamin-discord
docker pull wingedrat/gamin-discord
docker run -d -t --name gamin-discord --link gamin-redis:redis -d wingedrat/gamin-discord
echo Discord bot is updated