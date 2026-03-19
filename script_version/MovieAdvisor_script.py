#!/usr/bin/env python3
"""
Movie Advisor
============
Descrivi in italiano (o inglese) il film che vuoi vedere e ricevi
suggerimenti personalizzati con motivazioni e piattaforme streaming.

Architettura:
  1. Gemini riceve la richiesta e ragiona liberamente sui migliori film
     da consigliare, producendo una breve introduzione narrativa e una
     lista di titoli con motivazione personalizzata per ciascuno.
  2. TMDB viene usato solo come lookup finale per arricchire ogni titolo
     con dati fattuali: anno, voto, trama ufficiale, piattaforme streaming.

Dipendenze:
    pip install google-genai requests

API key necessarie (gratuite):
    - GEMINI_API_KEY  → https://aistudio.google.com/app/apikey
    - TMDB_API_KEY    → https://www.themoviedb.org/settings/api
"""

import os
import sys
import json
import requests

try:
    from google import genai
    from google.genai import types
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "google-genai", "requests"], check=True)
    from google import genai
    from google.genai import types


# ─── Configurazione ────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TMDB_API_KEY   = os.getenv("TMDB_API_KEY", "")

GEMINI_MODEL   = "gemini-2.5-flash-lite"
TMDB_BASE      = "https://api.themoviedb.org/3"
TMDB_COUNTRY   = "IT"   # Paese per Watch Providers (ISO 3166-1, es. IT, US, GB)
DEBUG          = False  # Imposta True per vedere i blocchi grezzi di Gemini

LINE_WIDTH = 140   # larghezza massima dell'output, modificabile a piacere
INDENT     = "  " # rientro base (2 spazi)
INDENT2    = "      " # rientro per i dettagli film (6 spazi)


# ─── Prompt di sistema per Gemini ─────────────────────────────────────────────

SYSTEM_PROMPT = """Sei un esperto cinefilo e consulente cinematografico personale.
L'utente ti descrive cosa vuole vedere — può essere una richiesta precisa, un'emozione,
un'atmosfera, un regista, un attore, o qualcosa di vago come "qualcosa che mi tenga sveglio".

Il tuo compito è consigliare film in modo intelligente e personalizzato.
Ragiona liberamente: considera generi, temi, atmosfera, stile visivo, ritmo narrativo.
Non sei vincolato a filtri rigidi: puoi consigliare film che corrispondono
allo spirito della richiesta anche se non matchano parola per parola.

Rispondi SEMPRE e SOLO con un oggetto JSON valido, senza testo aggiuntivo,
senza markdown, senza backtick. Il JSON deve avere questa struttura:

{
  "introduzione": "2-3 frasi narrative che contestualizzano i consigli, scritte in modo caldo e personale",
  "ordinamento": null,
  "film": [
    {
      "titolo": "Titolo originale del film",
      "anno": 1999,
      "motivazione": "1-2 frasi che spiegano perché questo film è perfetto per la richiesta specifica dell'utente"
    }
  ]
}

Il campo "ordinamento" deve essere null di default. Impostalo solo se l'utente
chiede esplicitamente un ordinamento specifico, scegliendo uno di questi valori:
- "anno_asc"   → dal più vecchio al più recente
- "anno_desc"  → dal più recente al più vecchio
- "voto_asc"   → dal punteggio più basso al più alto
- "voto_desc"  → dal punteggio più alto al più basso

Regole importanti:
- Usa sempre il titolo ORIGINALE del film (non la traduzione italiana), per poterlo cercare correttamente su database esterni.
- L'anno deve essere un intero, non una stringa.
- Consiglia tra 3 e 10 film, calibrando il numero in base alla richiesta
  (es. "tutti i film di X" → tutti quelli che conosci; "consigliami un film" → 3-5).
- Le motivazioni devono essere personalizzate sulla richiesta dell'utente,
  non descrizioni generiche del film.
- Scrivi in italiano.
- Non includere mai serie TV, solo film.
"""


# ─── Funzioni helper ───────────────────────────────────────────────────────────

def check_keys() -> bool:
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not TMDB_API_KEY:
        missing.append("TMDB_API_KEY")
    if missing:
        print("\n❌ API key mancanti. Imposta le variabili d'ambiente:")
        for k in missing:
            print(f"   export {k}='la-tua-chiave'")
        print("\n   Dove ottenerle:")
        print("   GEMINI_API_KEY → https://aistudio.google.com/app/apikey")
        print("   TMDB_API_KEY   → https://www.themoviedb.org/settings/api")
        return False
    return True


def ask_gemini(user_input: str) -> dict:
    """
    Invia la richiesta a Gemini con web search abilitato.
    Gemini può cercare informazioni aggiornate (film recenti, uscite 2025/2026)
    prima di formulare i consigli. Restituisce il JSON con introduzione e lista film.
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_input,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )

    parts = response.candidates[0].content.parts

    if DEBUG:
        print(f"\n  [DEBUG] {len(parts)} blocchi ricevuti da Gemini:")
        for i, part in enumerate(parts):
            text = getattr(part, "text", None)
            preview = repr(text[:120]) if text else "None"
            print(f"  [DEBUG] blocco {i} | type={type(part).__name__} | text={preview}")

    # Raccogliamo tutti i blocchi di testo in ordine
    text_blocks = [
        getattr(p, "text", None)
        for p in parts
        if getattr(p, "text", None) and getattr(p, "text", "").strip()
    ]

    raw = ""

    # Prima scelta: blocco che inizia con "{" o "```" (il JSON atteso)
    for block in text_blocks:
        cleaned = block.strip()
        if cleaned.startswith("{") or cleaned.startswith("```"):
            raw = cleaned
            break

    # Seconda scelta: blocco che contiene "{" al suo interno
    if not raw:
        for block in text_blocks:
            if "{" in block:
                start = block.index("{")
                raw = block[start:].strip()
                break

    # Fallback finale: ultimo blocco di testo disponibile
    if not raw and text_blocks:
        raw = text_blocks[-1].strip()

    if DEBUG and raw:
        print(f"\n  [DEBUG] raw estratto: {repr(raw[:200])}")

    # Pulizia difensiva nel caso Gemini aggiunga backtick o "```json"
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    if not raw:
        raise ValueError(
            "Gemini ha restituito una risposta vuota o non parsabile. "
            "Imposta DEBUG=True per vedere i blocchi grezzi."
        )

    return json.loads(raw)


def tmdb_search(title: str, year: int | None) -> dict | None:
    """
    Cerca un film su TMDB per titolo e anno opzionale.
    Restituisce il primo risultato pertinente o None.
    """
    url = f"{TMDB_BASE}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": title,
        "language": "it-IT",
        "include_adult": "false",
    }
    if year:
        params["year"] = year

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        return results[0] if results else None
    except Exception:
        return None


def tmdb_watch_providers(movie_id: int) -> dict:
    """
    Recupera le piattaforme streaming per un film tramite TMDB Watch Providers.
    Restituisce un dict con chiavi 'stream', 'rent', 'buy'.
    """
    url = f"{TMDB_BASE}/movie/{movie_id}/watch/providers"
    try:
        r = requests.get(url, params={"api_key": TMDB_API_KEY}, timeout=10)
        r.raise_for_status()
        country_data = r.json().get("results", {}).get(TMDB_COUNTRY, {})
    except Exception:
        return {"stream": [], "rent": [], "buy": []}

    def names(key: str) -> list[str]:
        return sorted(p["provider_name"] for p in country_data.get(key, []))

    return {
        "stream": names("flatrate") + names("free") + names("ads"),
        "rent":   names("rent"),
        "buy":    names("buy"),
    }


def enrich_with_tmdb(film: dict) -> dict:
    """
    Arricchisce un film suggerito da Gemini con i metadati TMDB.
    """
    titolo = film.get("titolo", "")
    anno   = film.get("anno")

    tmdb = tmdb_search(titolo, anno)
    if not tmdb:
        # Secondo tentativo senza anno (per film con anno impreciso)
        tmdb = tmdb_search(titolo, None)

    if tmdb:
        film["tmdb_id"]     = tmdb.get("id")
        film["voto"]        = tmdb.get("vote_average")
        film["trama"]       = tmdb.get("overview") or ""
        film["anno_tmdb"]   = (tmdb.get("release_date") or "")[:4]
        film["piattaforme"] = tmdb_watch_providers(tmdb["id"]) if tmdb.get("id") else {}
    else:
        film["tmdb_id"]     = None
        film["voto"]        = None
        film["trama"]       = ""
        film["anno_tmdb"]   = str(anno) if anno else ""
        film["piattaforme"] = {}

    return film


def sort_film_list(film_list: list[dict], ordinamento: str | None) -> list[dict]:
    """Riordina la lista film in base al criterio richiesto, usando i dati TMDB."""
    if not ordinamento:
        return film_list

    if ordinamento == "anno_asc":
        return sorted(film_list, key=lambda f: f.get("anno_tmdb") or "0")
    if ordinamento == "anno_desc":
        return sorted(film_list, key=lambda f: f.get("anno_tmdb") or "0", reverse=True)
    if ordinamento == "voto_asc":
        return sorted(film_list, key=lambda f: f.get("voto") or 0.0)
    if ordinamento == "voto_desc":
        return sorted(film_list, key=lambda f: f.get("voto") or 0.0, reverse=True)

    return film_list


def wrap(text: str, indent: str = INDENT, width: int = LINE_WIDTH) -> str:
    """Wrappa il testo alla larghezza massima rispettando le parole intere."""
    available = width - len(indent)
    words = text.split()
    lines, line = [], ""
    for w in words:
        if len(line) + len(w) + (1 if line else 0) > available:
            if line:
                lines.append(indent + line)
            line = w
        else:
            line = f"{line} {w}".strip() if line else w
    if line:
        lines.append(indent + line)
    return "\n".join(lines)


def print_sep(char="─", w=None):
    print(char * (w or LINE_WIDTH))


def print_film(film: dict, index: int) -> None:
    """Stampa le informazioni complete di un singolo film."""
    titolo = film.get("titolo", "Titolo sconosciuto")
    anno   = film.get("anno_tmdb") or (str(film.get("anno")) if film.get("anno") else "")
    voto   = film.get("voto")
    trama  = film.get("trama", "")
    motiv  = film.get("motivazione", "")
    pf     = film.get("piattaforme", {})

    rating = f"⭐ {voto:.1f}" if voto else ""
    print(f"\n{INDENT}[{index}] {titolo} {f'({anno})' if anno else ''}  {rating}")

    if motiv:
        print(wrap(f"💬 {motiv}", indent=INDENT2))

    if trama:
        print(wrap(f"📖 {trama}", indent=INDENT2))

    if pf.get("stream"):
        print(wrap(f"📺 Streaming incluso: {', '.join(pf['stream'])}", indent=INDENT2))
    if pf.get("rent"):
        print(wrap(f"🔑 Noleggio: {', '.join(pf['rent'])}", indent=INDENT2))
    if pf.get("buy"):
        print(wrap(f"💳 Acquisto: {', '.join(pf['buy'])}", indent=INDENT2))
    if not any((pf.get("stream"), pf.get("rent"), pf.get("buy"))):
        print(f"{INDENT2}❌ Non disponibile sulle piattaforme italiane")


# ─── Flusso principale ─────────────────────────────────────────────────────────

def main():
    print()
    print_sep("═")
    print("  🎬  Film Advisor — powered by Gemini + TMDB")
    print_sep("═")

    if not check_keys():
        sys.exit(1)

    print()
    try:
        user_input = input("  Descrivi il film che vuoi vedere:\n  > ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\n  Arrivederci! 👋")
        sys.exit(0)

    if not user_input:
        print("  ⚠️  Nessun input. Uscita.")
        sys.exit(0)

    # Step 1 — Gemini ragiona e consiglia
    print("\n  ⏳ Chiedo consiglio a Gemini…")
    try:
        risposta = ask_gemini(user_input)
    except Exception as e:
        print(f"\n  ❌ Errore Gemini: {e}")
        sys.exit(1)

    introduzione = risposta.get("introduzione", "")
    ordinamento  = risposta.get("ordinamento")
    film_list    = risposta.get("film", [])

    if not film_list:
        print("\n  ❌ Gemini non ha restituito film. Prova con una descrizione diversa.")
        sys.exit(0)

    # Step 2 — TMDB arricchisce ogni titolo con metadati e piattaforme
    print(f"  ⏳ Recupero metadati e piattaforme da TMDB…")
    film_list = [enrich_with_tmdb(f) for f in film_list]

    # Step 3 — Ordinamento finale sui dati TMDB (precisi)
    film_list = sort_film_list(film_list, ordinamento)

    # Output
    print()
    print_sep("═")
    print(wrap(f"🎥  Consigli per: \"{user_input}\""))
    print_sep("═")

    if introduzione:
        print()
        print(wrap(introduzione))

    print_sep()

    for i, film in enumerate(film_list, start=1):
        print_film(film, i)

    print()
    print_sep()


if __name__ == "__main__":
    main()
