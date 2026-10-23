FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm
# Le dépôt apt de Yarn livré avec l'image a une clé expirée : il fait échouer « apt-get update »
# (et donc l'installation de Docker-in-Docker). Huntboard n'utilise pas Yarn.
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn*.list
