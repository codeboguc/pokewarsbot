"""
PokeWars Bot - automatyczne walki z bossem.
Interfejs konsolowy kompatybilny z czytnikiem ekranu NVDA.
Komunikaty sa czytane na glos przez synteze mowy Windows.
"""

import sys
import time
import random
import traceback
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

try:
    from config import (
        EMAIL, HASLO, MIN_PRZERWA, MAX_PRZERWA,
        LIMIT_WALK, POKAZ_PRZEGLADARKE, TIMEOUT,
    )
except ImportError:
    print("Blad! Nie znaleziono pliku config.py.", flush=True)
    print("Skopiuj szablon: copy config.example.py config.py i uzupelnij EMAIL oraz HASLO.", flush=True)
    try:
        input("Nacisnij Enter zeby zamknac...")
    except EOFError:
        pass
    sys.exit(1)

# --- Synteza mowy (Windows SAPI bezposrednio) ---
_glos = None

def _inicjalizuj_mowe():
    global _glos
    try:
        import win32com.client
        _glos = win32com.client.Dispatch("SAPI.SpVoice")
        _glos.Rate = 2
        for v in _glos.GetVoices():
            if "polish" in v.GetDescription().lower():
                _glos.Voice = v
                break
    except Exception:
        _glos = None

_inicjalizuj_mowe()

statystyki = {"wygrane": 0, "przegrane": 0, "nieznane": 0, "bledy": 0}


def mow(msg: str) -> None:
    """Wypisuje komunikat na ekran i czyta go na glos przez Windows SAPI."""
    print(msg, flush=True)
    if _glos and msg.strip():
        try:
            _glos.Speak(msg)
        except Exception:
            pass


def czekaj_na_enter(komunikat: str = "Nacisnij Enter zeby zamknac...") -> None:
    try:
        input(komunikat)
    except EOFError:
        time.sleep(5)


def przerwa() -> None:
    delay = random.uniform(MIN_PRZERWA, MAX_PRZERWA)
    mow(f"Czekam {delay:.0f} sekund przed kolejna walka...")
    time.sleep(delay)


def zaloguj(page) -> bool:
    mow("Otwieram strone pokewars.pl...")
    page.goto("https://pokewars.pl", wait_until="networkidle", timeout=TIMEOUT * 1000)
    time.sleep(2)

    pole_email = None
    pole_haslo = None
    for sel in ['input[name="email"]', 'input[type="email"]', 'input[name="login"]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                pole_email = el
                break
        except Exception:
            continue

    for sel in ['input[type="password"]', 'input[name="password"]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                pole_haslo = el
                break
        except Exception:
            continue

    if not pole_email or not pole_haslo:
        mow("Blad! Nie znaleziono formularza logowania na stronie.")
        return False

    mow("Wpisuje dane logowania...")
    pole_email.click()
    pole_email.fill(EMAIL)
    time.sleep(0.5)
    pole_haslo.click()
    pole_haslo.fill(HASLO)
    time.sleep(0.5)

    for sel in ['button:has-text("Zaloguj")', 'button[type="submit"]', 'input[type="submit"]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                break
        except Exception:
            continue
    else:
        pole_haslo.press("Enter")

    mow("Logowanie, prosze czekac...")
    try:
        page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
    except PlaywrightTimeout:
        pass
    time.sleep(3)

    if "gra.pokewars.pl" in page.url:
        mow("Zalogowano pomyslnie!")
        return True

    mow("Blad logowania! Sprawdz email i haslo w pliku config.py.")
    return False


def czekaj_na_mape(page) -> None:
    """Czeka az mapa z wyspami pojawi sie na stronie."""
    try:
        page.locator("div.island-travel").first.wait_for(state="attached", timeout=15000)
    except Exception:
        time.sleep(5)


def pobierz_dostepnych_bossow(page) -> list[dict]:
    """Odczytuje liste bossow z DOM strony lokacji."""
    try:
        return page.evaluate("""() => {
            const result = [];
            const inputs = document.querySelectorAll('input[name="boss_fight"]');
            for (const input of inputs) {
                const form = input.closest('form');
                if (!form) continue;
                const islandInput = form.querySelector('input[name="island_id"]');
                if (!islandInput) continue;

                const islandId = islandInput.value;
                const container = input.closest('.island-travel') || input.closest('.island-data-box');
                let nazwa = '';
                let bossName = '';
                if (container) {
                    const h2 = container.querySelector('h2');
                    if (h2) nazwa = h2.textContent.trim();
                    const lis = container.querySelectorAll('li');
                    for (const li of lis) {
                        const text = li.textContent.trim();
                        if (text.startsWith('Boss:')) {
                            bossName = text.replace('Boss:', '').trim();
                        }
                    }
                }

                const isBlocked = input.classList.contains('blocked') || input.disabled;
                result.push({ island_id: islandId, nazwa: nazwa, boss: bossName, blocked: isBlocked });
            }
            return result;
        }""")
    except Exception:
        return []


def walcz_z_bossem(page, island_id: str) -> bool:
    """Najedz myszka na wyspe na mapie, poczekaj na dropdown, kliknij Walcz z bossem."""
    wyspa = page.locator(f"div.island-travel.isl_{island_id}")
    try:
        wyspa.hover(force=True, timeout=10000)
        time.sleep(1)
    except Exception:
        mow(f"Nie udalo sie najechac na wyspe numer {island_id}.")
        return False

    btn = page.locator(f"div.isl_{island_id} input[name='boss_fight']")
    try:
        btn.wait_for(state="visible", timeout=5000)
        btn.click(timeout=5000)
        return True
    except Exception:
        try:
            btn.click(force=True, timeout=5000)
            return True
        except Exception:
            mow("Nie udalo sie kliknac przycisku walki z bossem.")
            return False


def odczytaj_wynik_walki(page) -> str:
    """Odczytuje wynik walki ze strony."""
    try:
        tresc = page.content().lower()
    except Exception:
        return "nieznany"

    for slowo in ["captcha", "recaptcha", "nie jestem robotem"]:
        if slowo in tresc:
            mow("")
            mow("Uwaga! Wykryto captche!")
            mow("Musisz recznie rozwiazac captche w oknie przegladarki.")
            mow("Po rozwiazaniu nacisnij Enter tutaj.")
            czekaj_na_enter("Nacisnij Enter po rozwiazaniu captchy...")
            return "captcha"

    # Odczytaj komunikaty gry (infoBar, alert-box)
    komunikaty = []
    for el in page.locator("div.infoBar, div.alert-box").all():
        try:
            txt = el.inner_text(timeout=2000).strip()
            if txt:
                komunikaty.append(txt)
        except Exception:
            pass

    for k in komunikaty:
        mow(f"Komunikat gry: {k}")

    if "udało ci się pokonać bossa" in tresc:
        return "wygrana"
    if "nie udało ci się pokonać bossa" in tresc:
        return "przegrana"
    if "pokonał" in tresc:
        return "przegrana"

    return "nieznany"


def wyswietl_statystyki() -> None:
    w = statystyki["wygrane"]
    p = statystyki["przegrane"]
    n = statystyki["nieznane"]
    b = statystyki["bledy"]
    mow(f"Statystyki sesji: {w} wygranych, {p} przegranych, {n} nieznanych, {b} bledow.")


def otworz_lokacje(page) -> bool:
    """Otwiera strone lokacji i czeka na zaladowanie mapy."""
    page.goto("https://gra.pokewars.pl/lokacje", wait_until="networkidle", timeout=TIMEOUT * 1000)
    time.sleep(3)
    czekaj_na_mape(page)
    return "/lokacje" in page.url


def petla_walki(page):
    walka_nr = 0
    nieudane_z_rzedu = 0

    mow("")
    mow("Przechodze do strony z lokacjami...")
    if not otworz_lokacje(page):
        mow("Blad! Nie udalo sie otworzyc strony lokacji.")
        return

    bossy = pobierz_dostepnych_bossow(page)
    if not bossy:
        mow("Blad! Nie znaleziono zadnych bossow na stronie.")
        return

    mow(f"Znaleziono {len(bossy)} bossow na mapie:")
    for b in bossy:
        status = ", zablokowany" if b["blocked"] else ", dostepny"
        mow(f"  {b['nazwa']}, boss {b['boss']}{status}")

    dostepni = [b for b in bossy if not b["blocked"]]
    if not dostepni:
        mow("Wszyscy bossowie sa zablokowani. Sprobuj pozniej.")
        return

    mow("")
    if LIMIT_WALK > 0:
        mow(f"Rozpoczynam serie {LIMIT_WALK} walk.")
    else:
        mow("Rozpoczynam walki bez limitu. Nacisnij Control plus C zeby zatrzymac.")
    mow("")

    boss_idx = 0

    while True:
        if 0 < LIMIT_WALK <= walka_nr:
            mow(f"Osiagnieto limit {LIMIT_WALK} walk.")
            break

        walka_nr += 1
        boss = dostepni[boss_idx % len(dostepni)]

        mow(f"Walka numer {walka_nr}. "
            f"Atakuje bossa {boss['boss']} na wyspie {boss['nazwa']}.")

        if not walcz_z_bossem(page, boss["island_id"]):
            statystyki["bledy"] += 1
            nieudane_z_rzedu += 1
            if nieudane_z_rzedu >= 5:
                mow("5 nieudanych prob z rzedu. Zatrzymuje skrypt.")
                break
            mow(f"Nieudana proba numer {nieudane_z_rzedu} z 5.")
            przerwa()
            otworz_lokacje(page)
            continue

        try:
            page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
        except PlaywrightTimeout:
            pass
        time.sleep(2)

        wynik = odczytaj_wynik_walki(page)

        if wynik == "wygrana":
            statystyki["wygrane"] += 1
            mow(f"Wynik walki numer {walka_nr}: Wygrana!")
        elif wynik == "przegrana":
            statystyki["przegrane"] += 1
            mow(f"Wynik walki numer {walka_nr}: Przegrana.")
        elif wynik == "captcha":
            pass
        else:
            statystyki["nieznane"] += 1
            mow(f"Wynik walki numer {walka_nr}: Nie udalo sie odczytac wyniku.")

        nieudane_z_rzedu = 0

        if walka_nr % 5 == 0:
            wyswietl_statystyki()

        przerwa()

        mow("Wracam do lokacji...")
        otworz_lokacje(page)

        bossy = pobierz_dostepnych_bossow(page)
        dostepni = [b for b in bossy if not b["blocked"]]

        if not dostepni:
            mow("Wszyscy bossowie zablokowani. Czekam 30 sekund...")
            time.sleep(30)
            page.reload()
            time.sleep(3)
            czekaj_na_mape(page)
            bossy = pobierz_dostepnych_bossow(page)
            dostepni = [b for b in bossy if not b["blocked"]]
            if not dostepni:
                mow("Bossowie nadal zablokowani. Koncze.")
                break

        boss_idx += 1

    mow("")
    mow(f"Zakonczono po {walka_nr} walkach.")
    wyswietl_statystyki()


def main():
    mow("")
    mow("PokeWars Bot, wersja 1.0.")
    mow("Automatyczne walki z bossem.")
    mow("")
    mow(f"Konto: {EMAIL}")
    mow(f"Przerwa miedzy walkami: od {MIN_PRZERWA} do {MAX_PRZERWA} sekund.")
    if LIMIT_WALK > 0:
        mow(f"Limit walk: {LIMIT_WALK}.")
    else:
        mow("Limit walk: bez limitu.")
    mow("")

    with sync_playwright() as pw:
        mow("Uruchamiam przegladarke, prosze czekac...")
        browser = pw.chromium.launch(
            headless=not POKAZ_PRZEGLADARKE,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        try:
            if not zaloguj(page):
                try:
                    page.screenshot(path="blad_logowania.png")
                except Exception:
                    pass
                czekaj_na_enter()
                return

            petla_walki(page)

        except KeyboardInterrupt:
            mow("")
            mow("Zatrzymano przez uzytkownika.")
            wyswietl_statystyki()
        except Exception as e:
            mow(f"Nieoczekiwany blad: {e}")
            traceback.print_exc()
            try:
                page.screenshot(path="blad_krytyczny.png")
            except Exception:
                pass
        finally:
            mow("Zamykam przegladarke...")
            browser.close()

    mow("")
    mow("Skrypt zakonczony.")
    czekaj_na_enter()


if __name__ == "__main__":
    main()
