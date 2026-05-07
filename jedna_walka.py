"""
PokeWars Bot - jedna walka z bossem.
Loguje sie, walczy raz i konczy.
"""

import sys
import time
import traceback
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

try:
    from config import EMAIL, HASLO, POKAZ_PRZEGLADARKE, TIMEOUT
except ImportError:
    print("Blad! Nie znaleziono pliku config.py.", flush=True)
    try:
        input("Nacisnij Enter zeby zamknac...")
    except EOFError:
        pass
    sys.exit(1)

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


def mow(msg: str) -> None:
    print(msg, flush=True)
    if _glos and msg.strip():
        try:
            _glos.Speak(msg)
        except Exception:
            pass


def main():
    mow("PokeWars Bot. Jedna walka z bossem.")
    mow("")

    with sync_playwright() as pw:
        mow("Uruchamiam przegladarke...")
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
                mow("Blad! Nie znaleziono formularza logowania.")
                return

            mow("Logowanie...")
            pole_email.fill(EMAIL)
            time.sleep(0.3)
            pole_haslo.fill(HASLO)
            time.sleep(0.3)

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

            try:
                page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
            except PlaywrightTimeout:
                pass
            time.sleep(3)

            if "gra.pokewars.pl" not in page.url:
                mow("Blad logowania! Sprawdz dane w config.py.")
                return

            mow("Zalogowano!")

            mow("Otwieram lokacje...")
            page.goto("https://gra.pokewars.pl/lokacje", wait_until="networkidle", timeout=TIMEOUT * 1000)
            time.sleep(3)
            try:
                page.locator("div.island-travel").first.wait_for(state="attached", timeout=15000)
            except Exception:
                time.sleep(5)

            bossy = page.evaluate("""() => {
                const result = [];
                const inputs = document.querySelectorAll('input[name="boss_fight"]');
                for (const input of inputs) {
                    const form = input.closest('form');
                    if (!form) continue;
                    const isl = form.querySelector('input[name="island_id"]');
                    if (!isl) continue;
                    const container = input.closest('.island-travel');
                    let nazwa = '', bossName = '';
                    if (container) {
                        const h2 = container.querySelector('h2');
                        if (h2) nazwa = h2.textContent.trim();
                        for (const li of container.querySelectorAll('li')) {
                            if (li.textContent.trim().startsWith('Boss:'))
                                bossName = li.textContent.trim().replace('Boss:', '').trim();
                        }
                    }
                    if (!input.classList.contains('blocked') && !input.disabled)
                        result.push({ island_id: isl.value, nazwa, boss: bossName });
                }
                return result;
            }""")

            if not bossy:
                mow("Nie znaleziono dostepnych bossow.")
                return

            boss = bossy[0]
            mow(f"Atakuje bossa {boss['boss']} na wyspie {boss['nazwa']}.")

            wyspa = page.locator(f"div.island-travel.isl_{boss['island_id']}")
            wyspa.hover(force=True, timeout=10000)
            time.sleep(1)

            btn = page.locator(f"div.isl_{boss['island_id']} input[name='boss_fight']")
            try:
                btn.wait_for(state="visible", timeout=5000)
                btn.click(timeout=5000)
            except Exception:
                btn.click(force=True, timeout=5000)

            try:
                page.wait_for_load_state("networkidle", timeout=TIMEOUT * 1000)
            except PlaywrightTimeout:
                pass
            time.sleep(2)

            tresc = page.content()
            tresc_lower = tresc.lower()

            if "udało ci się pokonać bossa" in tresc_lower:
                mow("Wynik: Wygrana! Pokonales bossa!")
            elif "nie udało ci się pokonać bossa" in tresc_lower:
                mow("Wynik: Przegrana. Nie udalo sie pokonac bossa.")
            elif "pokonał" in tresc_lower or "przegran" in tresc_lower:
                mow("Wynik: Przegrana.")
            else:
                mow("Walka zakonczona.")

            info_bar = page.locator("div.infoBar, div.alert-box").all()
            for el in info_bar:
                try:
                    txt = el.inner_text(timeout=2000).strip()
                    if txt:
                        mow(f"Komunikat gry: {txt}")
                except Exception:
                    pass

        except Exception as e:
            mow(f"Blad: {e}")
            traceback.print_exc()
        finally:
            mow("Zamykam przegladarke...")
            browser.close()

    mow("")
    mow("Gotowe.")
    try:
        input("Nacisnij Enter zeby zamknac...")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
