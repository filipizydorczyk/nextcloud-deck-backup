# General

Whole script is based on https://gist.github.com/svbergerem/5914d7f87764901aefddba125af99938. The only diffrence is that my script saves data to json and u can send it to another nextcloud instance whenever you want to, base script transfers deck between nextcloud instances.

# Arguments

| Argument  | Default value         | Description                                                                                                        |
| --------- | --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| mode      | backup                | Can be `backup` or `send`. Determinates if u want to donwload data to file or send to nextcloud instance from file |
| host      | http://localhost:8080 | nextcloud url                                                                                                      |
| username  | test                  | nextcloud username                                                                                                 |
| passwd    | test                  | nextcloud user's password                                                                                          |
| directory | .                     | directory where to save/download data. Just plain path program will search for file called `nextcloud-decks.json`  |

# Testing

If u want to test if it works u can run docker and test it with default values

```bash
docker-compose up -d
# create nextcloud user if it was run for the first time
python main.py # to download created decks from localhost
python main.py --mode send # to send data saved in file nextcloud-decks.json to localhost
```

# Makefile

-   `make init` - install requierments (only needed to pack script to single file if u dont want this u dont have to do this)
-   `make build` - pack python scripts to single file
-   `make install` - copy builded file to `~/.local/bin/` as `nextcloud-deck-backuper`
-   `make clean` - delete build and build artifacts from root project directory
