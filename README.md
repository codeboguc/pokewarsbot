# PokeWars Boss Bot

Automatyzacja przeglądarki dla [pokewars.pl](https://pokewars.pl): logowanie, przejście na lokacje, walka z bossem (najechanie na wyspę na mapie i kliknięcie „Walcz z bossem”). Komunikaty tekstowe w konsoli oraz **synteza mowy Windows SAPI** (polski głos), przydatne przy korzystaniu z czytnika ekranu lub bez patrzenia w okno.

**Uwaga:** regulamin gry zabrania botów i skryptów — ryzyko bana konta. Używasz na własną odpowiedzialność.

## Wymagania

- Windows 10+
- Python 3.10+ (z zaznaczonym „Add Python to PATH”)
- Połączenie z internetem

## Instalacja

```powershell
cd pokewars
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Skonfiguruj konto:

1. Skopiuj `config.example.py` jako `config.py`.
2. W `config.py` ustaw `EMAIL` i `HASLO`.

```powershell
copy config.example.py config.py
```

Następnie edytuj `config.py` w edytorze tekstu.

## Uruchomienie

| Plik | Działanie |
|------|-----------|
| `start.bat` | Auto logowanie + walki z bossem w pętli |
| `jedna_walka.bat` | Auto logowanie + jedna walka |
| `walka_boss.bat` | Ty logujesz się ręcznie w przeglądarce, potem jedna walka |

Możesz też uruchomić: `python pokewars_bot.py`, `python jedna_walka.py`, `python walka_boss.py`.

## Konfiguracja (`config.py`)

- `MIN_PRZERWA` / `MAX_PRZERWA` — losowa przerwa między walkami (sekundy)
- `LIMIT_WALK` — `0` = bez limitu, inaczej maksymalna liczba walk
- `POKAZ_PRZEGLADARKE` — `True` = widoczna przeglądarka
- `TIMEOUT` — timeout ładowania strony (sekundy)

Plik `config.py` jest w `.gitignore`, żeby nie wrzucać hasła do Git.

Repozytorium: [github.com/codeboguc/pokewarsbot](https://github.com/codeboguc/pokewarsbot). Klonowanie:

```powershell
git clone https://github.com/codeboguc/pokewarsbot.git
```

## Dostępność

- Konsola: komunikaty z `flush=True`, żeby NVDA mógł je ogłaszać na bieżąco.
- Mowa: Windows SAPI (`win32com`), domyślnie polski głos jeśli jest zainstalowany.

Szczegóły po polsku: [INSTRUKCJA.txt](INSTRUKCJA.txt).

## Struktura projektu

- `pokewars_bot.py` — główny bot (pętla)
- `jedna_walka.py` — jedna walka z auto logowaniem
- `walka_boss.py` — jedna walka po ręcznym logowaniu
- `config.example.py` — szablon konfiguracji

## Licencja

Kod udostępniany bez gwarancji. Gra i znaki towarowe Pokémon należą do ich właścicieli.
