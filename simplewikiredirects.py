import toolforge, re
import pywikibot
from collections import defaultdict

DRY_RUN = False

def get_db_connection():
    return toolforge.connect('simplewiki', charset='utf8mb4')

def fetch_movie_pages(cursor):
    cursor.execute("SELECT page_title FROM page WHERE page_namespace = 0 AND (page_title REGEXP '\\\\([0-9]{4}_movie\\\\)$' OR page_title REGEXP '\\\\([0-9]{4}_film\\\\)$' OR page_title LIKE '%(movie)' OR page_title LIKE '%(film)')"); return cursor.fetchall()

def parse_movie_titles(rows):
    pairs = defaultdict(dict)
    for (title,) in rows:
        decoded = title.decode('utf-8').replace('_', ' ')
        m = re.match(r'^(.*)\s\((\d{4}) (movie|film)\)$', decoded)
        if m:
            base, year, kind = m.groups()
            key = f"{base.strip()} ({year})"
            pairs[key][kind] = f"{base.strip()} ({year} {kind})"
            continue
        m = re.match(r'^(.*)\s\((movie|film)\)$', decoded)
        if m:
            base, kind = m.groups()
            key = base.strip()
            pairs[key][kind] = f"{base.strip()} ({kind})"
    return pairs

def get_redirect_data(cursor, movie_pages):
    if not movie_pages: return {}, {}
    format_strings = ','.join(['%s'] * len(movie_pages))
    cursor.execute(f"SELECT p.page_title, p.page_is_redirect, r.rd_title FROM page p LEFT JOIN redirect r ON p.page_id = r.rd_from WHERE p.page_namespace = 0 AND p.page_title IN ({format_strings})", movie_pages); redirect_map, redirect_status = {}, {}
    for page_title, is_redirect, rd_title in cursor.fetchall():
        source = page_title.decode('utf-8').replace('_', ' ')
        if is_redirect and rd_title:
            target = rd_title.decode('utf-8').replace('_', ' ')
            redirect_map[source] = target
            redirect_status[source] = True
        else:
            redirect_map[source] = source
            redirect_status[source] = False
    return redirect_map, redirect_status

def generate_film_title(base):
    if re.match(r'.* \(\d{4}\)$', base):
        year = re.search(r'\((\d{4})\)$', base).group(1)
        title = re.sub(r' \(\d{4}\)$', '', base)
        return f"{title} ({year} film)"
    return f"{base} (film)"

def create_redirects(pairs, redirect_map, redirect_status):
    site = pywikibot.Site('simple', 'wikipedia')
    to_create = [(generate_film_title(base), redirect_map[kinds['movie']], redirect_status[kinds['movie']]) for base, kinds in sorted(pairs.items()) if 'movie' in kinds and 'film' not in kinds]
    print(f"{len(to_create)} pages to create")
    for film_title, redirect_target, resolved in to_create:
        if DRY_RUN:
            status = " [resolved]" if resolved else ""
            print(f"{film_title} --> {redirect_target}{status}")
        else:
            film_page = pywikibot.Page(site, film_title)
            if not film_page.exists():
                film_page.text = f"#REDIRECT [[{redirect_target}]]"
                film_page.save(summary=f"Redirected page to [[{redirect_target}]]")

conn = get_db_connection()
cursor = conn.cursor()
try:
    rows = fetch_movie_pages(cursor)
    pairs = parse_movie_titles(rows)
    movie_pages = [kinds['movie'].replace(' ', '_') for base, kinds in pairs.items() if 'movie' in kinds]
    redirect_map, redirect_status = get_redirect_data(cursor, movie_pages)
    create_redirects(pairs, redirect_map, redirect_status)
finally:
    cursor.close(); conn.close()
