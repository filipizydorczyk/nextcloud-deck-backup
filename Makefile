clean:
	rm nextcloud-decks.json
	rm main.spec
	rm -rf build
	rm -rf dist

init:
	pip install -r requirements.txt

build:
	pyinstaller --onefile main.py

install:
	cp dist/main ~/.local/bin/nextcloud-deck-backuper