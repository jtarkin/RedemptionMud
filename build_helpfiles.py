#!/usr/bin/env python3
"""Parse help_db.txt and generate helpfiles.html for Redemption MUD."""

import re
import html
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "help_db.txt")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "helpfiles.html")

# ── MUD color code mapping ──────────────────────────────────────────────────
COLOR_MAP = {
    'r': '#b03030',      # red
    'R': '#ff4444',      # bright red
    'g': '#30b030',      # green
    'G': '#44ff44',      # bright green
    'b': '#3030b0',      # blue
    'B': '#4444ff',      # bright blue
    'c': '#30b0b0',      # cyan
    'C': '#44ffff',      # bright cyan
    'y': '#b0b030',      # yellow (dark)
    'Y': '#ffff44',      # bright yellow
    'w': '#b0b0b0',      # white (dark)
    'W': '#ffffff',      # bright white
    'm': '#b030b0',      # magenta
    'M': '#ff44ff',      # bright magenta
    'D': '#666666',      # dark gray
}

def convert_color_codes(text):
    """Convert MUD {x color codes to HTML spans."""
    text = html.escape(text)
    # Replace {{ with a placeholder first
    text = text.replace('{{', '\x00LBRACE\x00')

    open_spans = 0

    def replace_code(m):
        nonlocal open_spans
        code = m.group(1)
        if code == 'x':
            if open_spans > 0:
                open_spans -= 1
                return '</span>'
            return ''
        elif code == 'u':
            open_spans += 1
            return '<span style="text-decoration:underline">'
        elif code in COLOR_MAP:
            # Close previous color span if one is open, then open new
            prefix = ''
            if open_spans > 0:
                prefix = '</span>'
            else:
                open_spans += 1
            return prefix + f'<span style="color:{COLOR_MAP[code]}">'
        return m.group(0)

    text = re.sub(r'\{([rRgGbBcCyYwWmMDxu])', replace_code, text)
    # Close any unclosed spans
    text += '</span>' * open_spans
    # Restore literal braces
    text = text.replace('\x00LBRACE\x00', '{')
    return text


# ── Parser ───────────────────────────────────────────────────────────────────
def parse_help_db(filepath):
    """Parse help_db.txt and return list of {level, keywords, body} dicts."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    entries = []
    # Split on ~ delimiters. The format is:
    # ~\n<level> <KEYWORDS>~\n<body>\n~
    # We split by lines and use a state machine.
    lines = content.split('\n')
    i = 0
    # Skip header
    while i < len(lines) and not lines[i].strip() == '~':
        i += 1

    while i < len(lines):
        # Find the ~ that starts an entry boundary
        if lines[i].strip() == '~':
            i += 1
            if i >= len(lines):
                break
            # Next line should be: <level> <KEYWORDS>~
            header_line = lines[i]
            if header_line.strip() == '#$':
                break
            # Parse header: level followed by keywords ending with ~
            hm = re.match(r'^(\d+)\s+(.+?)~\s*$', header_line)
            if not hm:
                i += 1
                continue
            level = int(hm.group(1))
            keywords_str = hm.group(2).strip()
            # Skip the sentinel entry
            if keywords_str == '$':
                break
            i += 1
            # Collect body until next standalone ~
            body_lines = []
            while i < len(lines) and lines[i].strip() != '~':
                body_lines.append(lines[i])
                i += 1
            body = '\n'.join(body_lines).strip()

            # Parse keywords - split by spaces, but respect quoted multi-word
            keywords = []
            for part in re.findall(r"'[^']+?'|[^\s]+", keywords_str):
                keywords.append(part.strip("'"))

            entries.append({
                'level': level,
                'keywords': keywords,
                'keywords_str': keywords_str,
                'body': body,
            })
        else:
            i += 1

    return entries


# ── Categorization ───────────────────────────────────────────────────────────
# Each rule: (category, subcategory, set_of_keywords_or_pattern)
# Order matters - first match wins.

GETTING_STARTED_BASICS = {
    'MOTD', 'RULES', 'FAQ', 'STORY', 'NEWBIE', 'BASICS', 'START', 'BEGIN',
    'GREETING', 'DIKU', 'MERC', 'ROM', 'REDEMPTION', 'CREDITS', 'AREAS',
    'SLIST', 'COMMANDS', 'HELP', 'SUMMARY', 'COLOR', 'COLOUR',
    'AUTOLIST', 'AUTOASSIST', 'AUTOEXIT', 'AUTOGOLD', 'AUTOLOOT',
    'AUTOSAC', 'AUTOSPLIT', 'BRIEF', 'COMPACT', 'PROMPT', 'SCROLL',
    'CONFIG', 'DESCRIPTION', 'TITLE', 'PASSWORD', 'QUIT', 'SAVE',
    'WHO', 'WHOIS', 'SOCIALS', 'EMOTE', 'BUG', 'TYPO', 'IDEA',
    'WIZLIST', 'IMMLIST', 'TIPS', 'OUTFIT', 'FINGER', 'AFK',
    'REPLAY', 'ALIAS', 'UNALIAS', 'MACRO',
}

GETTING_STARTED_MOVEMENT = {
    'NORTH', 'SOUTH', 'EAST', 'WEST', 'UP', 'DOWN', 'MOVEMENT', 'MOVE',
    'RECALL', 'EXITS', 'LOOK', 'SCAN', 'SEARCH', 'OPEN', 'CLOSE',
    'LOCK', 'UNLOCK', 'PICK', 'DOOR', 'WHERE', 'ENTER',
}

BASE_CLASSES = {
    'MAGE', 'CLERIC', 'THIEF', 'WARRIOR', 'PALADIN', 'RANGER',
    'DRUID', 'MONK', 'BARD', 'NECROMANCER', 'RUNIST',
}

REMORT_CLASSES = {
    'BLADEMASTER', 'SHADOWFIST', 'BLADESINGER', 'NINJA', 'ASSASSIN',
    'CRUSADER', 'TEMPLAR', 'AVENGER', 'ZEALOT', 'INQUISITOR',
    'ARCHMAGE', 'WARLOCK', 'SORCERER', 'LICH', 'ELEMENTALIST',
    'WARDEN', 'BEASTMASTER', 'SCOUT', 'STRIDER', 'HERBALIST',
    'ARCHDRUID', 'SHAPESHIFTER', 'HIEROPHANT',
    'GRANDMASTER', 'MYSTIC', 'TRANSCENDENT',
    'TROUBADOUR', 'MINSTREL', 'VIRTUOSO',
    'RECLASS', 'REMORT',
}

BASE_RACES = {
    'HUMAN', 'ELF', 'DWARF', 'GIANT', 'PIXIE', 'HALFLING', 'HALFORC',
    'HALF-ORC', 'HALF-ELF', 'HALFELF', 'DROW', 'GNOME', 'OGRE',
    'TROLL', 'HOBBIT', 'AVIAN', 'MINOTAUR', 'CENTAUR', 'RACES',
}

DRAGON_RACES = {
    'DRAGON', 'BAHAMUT', 'TIAMAT', 'RED DRAGON', 'BLUE DRAGON',
    'GREEN DRAGON', 'WHITE DRAGON', 'BLACK DRAGON', 'GOLD DRAGON',
    'SILVER DRAGON', 'BRONZE DRAGON', 'COPPER DRAGON', 'BRASS DRAGON',
    'CHROMATIC', 'METALLIC', 'PRISMATIC', 'SHADOW DRAGON',
    'CRYSTAL DRAGON', 'AMETHYST DRAGON', 'EMERALD DRAGON',
    'SAPPHIRE DRAGON', 'TOPAZ DRAGON', 'RUBY DRAGON',
}

OTHER_REMORT_RACES = {
    'VAMPIRE', 'WEREWOLF', 'ANGEL', 'DEMON', 'DJINN', 'DOPPELGANGER',
    'GOLEM', 'LICH RACE', 'WRAITH', 'REVENANT', 'SHADE', 'SPECTRE',
    'UNDEAD', 'CELESTIAL', 'FIEND', 'FAE', 'SYLPH', 'SALAMANDER',
    'GARGOYLE', 'NAGA', 'SIDHE', 'TITAN',
}

CHAR_STATS = {
    'SCORE', 'WORTH', 'AFFECTS', 'TRAIN', 'PRACTICE', 'LEVEL',
    'EXPERIENCE', 'ALIGNMENT', 'STATS', 'ATTRIBUTES', 'PRAC',
    'GROUP', 'GAIN', 'HITPOINTS', 'MANA', 'HITROLL', 'DAMROLL',
    'ARMOR', 'AC', 'STANCE', 'REPORT',
}

COMBAT_SKILLS = {
    'BASH', 'KICK', 'DISARM', 'TRIP', 'DIRT', 'BACKSTAB', 'CIRCLE',
    'DUAL WIELD', 'SECOND ATTACK', 'THIRD ATTACK', 'FOURTH ATTACK',
    'DODGE', 'PARRY', 'SHIELD BLOCK', 'ENHANCED DAMAGE', 'BERSERK',
    'RAGE', 'FLURRY', 'COUNTER', 'RIPOSTE', 'FEINT', 'LUNGE',
    'CHARGE', 'CLEAVE', 'HAMSTRING', 'HEADBUTT', 'PUMMEL',
    'UPPERCUT', 'ROUNDHOUSE', 'SWEEP', 'STUN', 'GOUGE',
    'POWER ATTACK', 'WHIRLWIND', 'FRENZY', 'FURY',
    'SNEAK', 'HIDE', 'STEAL', 'ENVENOM', 'PEEK',
    'HAND TO HAND', 'FAST HEALING', 'MEDITATION',
    'LORE', 'HAGGLE', 'RESCUE', 'SCROLLS', 'STAVES', 'WANDS',
    'DIRT KICKING', 'SHIELD BASH',
}

COMBAT_GENERAL = {
    'KILL', 'FLEE', 'WIMPY', 'CONSIDER', 'FIGHT', 'COMBAT',
    'MURDER', 'WEAPONS', 'WEAPON', 'DAMAGE', 'DEATH',
    'CORPSE', 'SACRIFICE', 'LOOT', 'GET', 'DROP', 'GIVE',
    'PUT', 'WEAR', 'WIELD', 'REMOVE', 'EQUIPMENT', 'INVENTORY',
    'COMPARE', 'EAT', 'DRINK', 'FILL', 'POUR', 'REST', 'SLEEP',
    'WAKE', 'STAND', 'SIT', 'DRAW', 'SHEATH', 'TRASH',
}

COMMUNICATION = {
    'SAY', 'TELL', 'YELL', 'GOSSIP', 'CHANNELS', 'CHAT', 'REPLY',
    'GTELL', 'MUSIC', 'QUESTION', 'ANSWER', 'GRATS', 'SHOUT',
    'AUCTION', 'NOTE', 'BOARD', 'DEAF', 'OOC', 'CLANTALK',
}

CLANS_PK = {
    'CLAN', 'CLANS', 'PK', 'LONER', 'WAR', 'PKILL', 'PLAYER KILLING',
    'DUEL', 'CHALLENGE', 'HARDCORE', 'CLANSTATS', 'CLANMEMBERS',
    'ACCEPT', 'RECRUIT', 'PETITION', 'LEADER', 'ADDRECRUITER',
    'DROPRECRUITER', 'SWAPLEADER', 'LEADERCOMMANDS', 'DELEGATE',
    'PRICES',
}

WORLD_SYSTEMS = {
    'QUEST', 'QUESTS', 'BANK', 'SHOP', 'SHOPS', 'BUY', 'SELL',
    'LIST', 'VALUE', 'GOLD', 'SILVER', 'MONEY', 'CRAFTING', 'CRAFT',
    'TRAIN', 'HEAL', 'HEALER', 'WEATHER', 'TIME', 'MAP',
    'PORTAL', 'TAXI', 'TRANSPORT', 'CLASS CHANGE', 'CLASSCHANGE',
}

# OLC keywords
OLC_KEYWORDS = {
    'OLC', 'AEDIT', 'REDIT', 'OEDIT', 'MEDIT', 'MPEDIT', 'HEDIT',
    'CEDIT', 'SEDIT', 'GEDIT', 'SKEDIT',
    'RESETS', 'VNUM', 'ASAVE', 'ALIST',
}


def categorize_entry(entry):
    """Return (category, subcategory) for an entry."""
    level = entry['level']
    kws = {k.upper() for k in entry['keywords']}
    kws_str = entry['keywords_str'].upper()

    # Immortal entries (level 54+)
    if level >= 54:
        # Check if OLC
        if kws & OLC_KEYWORDS or any(k in kws_str for k in OLC_KEYWORDS):
            return ('Immortal', 'Builder (OLC)')
        return ('Immortal', 'Admin Commands')

    # Check for spell patterns in keywords (quoted multi-word like 'CURE LIGHT')
    has_spell_keyword = any("'" in k or k.startswith("'") for k in entry['keywords'])
    body_upper = entry['body'].upper()
    is_spell = has_spell_keyword or 'CAST ' in body_upper[:200] or 'SYNTAX: CAST' in body_upper[:200]

    # Categorize by keyword matching (first match wins)
    if kws & CLANS_PK:
        return ('World', 'Clans & PK')
    if kws & BASE_CLASSES:
        return ('Character', 'Base Classes')
    if kws & REMORT_CLASSES:
        return ('Character', 'Remort & Reclass')
    if kws & BASE_RACES:
        return ('Character', 'Races')
    if kws & DRAGON_RACES or any('DRAGON' in k for k in kws):
        return ('Character', 'Races')
    if kws & OTHER_REMORT_RACES:
        return ('Character', 'Races')
    if is_spell:
        # Try to sub-categorize spells
        body_lower = entry['body'].lower()
        if any(w in body_lower for w in ['damage', 'attack', 'offensive', 'fireball', 'lightning', 'bolt', 'blast']):
            return ('Magic & Skills', 'Offensive Spells')
        if any(w in body_lower for w in ['heal', 'cure', 'protect', 'armor', 'shield', 'bless', 'sanctuary', 'ward']):
            return ('Magic & Skills', 'Defensive & Healing')
        return ('Magic & Skills', 'Other Spells')
    if kws & COMBAT_SKILLS:
        return ('Combat', 'Skills')
    if kws & COMBAT_GENERAL:
        return ('Combat', 'General')
    if kws & COMMUNICATION:
        return ('World', 'Communication')
    if kws & WORLD_SYSTEMS:
        return ('World', 'Systems')
    if kws & CHAR_STATS:
        return ('Character', 'Stats & Info')
    if kws & GETTING_STARTED_MOVEMENT:
        return ('Getting Started', 'Movement')
    if kws & GETTING_STARTED_BASICS:
        return ('Getting Started', 'Basics')

    # Check body for spell hints we missed
    if 'learned by:' in entry['body'].lower():
        return ('Magic & Skills', 'Other Spells')

    return ('Miscellaneous', 'General')


# ── HTML Generation ──────────────────────────────────────────────────────────

def make_entry_id(entry, seen_ids):
    """Generate a unique HTML id for an entry."""
    # Use first keyword, sanitized
    base = entry['keywords'][0].lower().replace(' ', '-').replace("'", '')
    base = re.sub(r'[^a-z0-9\-]', '', base)
    if not base:
        base = 'entry'
    eid = base
    counter = 2
    while eid in seen_ids:
        eid = f"{base}-{counter}"
        counter += 1
    # For duplicate keywords at different levels, add level suffix
    if base in seen_ids and entry['level'] >= 54:
        eid = f"{base}-imm"
        counter = 2
        while eid in seen_ids:
            eid = f"{base}-imm-{counter}"
            counter += 1
    seen_ids.add(eid)
    return eid


def generate_html(entries):
    """Generate the full helpfiles.html content."""
    # Categorize all entries
    categorized = {}  # {(cat, subcat): [(entry, entry_id), ...]}
    seen_ids = set()

    for entry in entries:
        cat, subcat = categorize_entry(entry)
        eid = make_entry_id(entry, seen_ids)
        entry['id'] = eid
        entry['category'] = cat
        entry['subcategory'] = subcat
        key = (cat, subcat)
        if key not in categorized:
            categorized[key] = []
        categorized[key].append(entry)

    # Sort entries within each subcategory
    for key in categorized:
        categorized[key].sort(key=lambda e: e['keywords'][0].upper())

    # Define category order
    category_order = [
        ('Getting Started', ['Basics', 'Movement']),
        ('Combat', ['General', 'Skills']),
        ('Magic & Skills', ['Offensive Spells', 'Defensive & Healing', 'Other Spells']),
        ('Character', ['Base Classes', 'Remort & Reclass', 'Races', 'Stats & Info']),
        ('World', ['Communication', 'Clans & PK', 'Systems']),
        ('Miscellaneous', ['General']),
        ('Immortal', ['Admin Commands', 'Builder (OLC)']),
    ]

    # Build sidebar HTML
    sidebar_html = ''
    for cat, subcats in category_order:
        # Collect subcats that actually have entries
        active_subcats = []
        for sc in subcats:
            if (cat, sc) in categorized:
                active_subcats.append(sc)
        # Also pick up any subcats we didn't predefine
        for key in categorized:
            if key[0] == cat and key[1] not in subcats:
                active_subcats.append(key[1])

        if not active_subcats:
            continue

        imm_class = ' imm-section' if cat == 'Immortal' else ''
        sidebar_html += f'      <div class="sidebar-section{imm_class}">\n'
        sidebar_html += f'        <details{"" if cat == "Immortal" else " open"}>\n'
        sidebar_html += f'          <summary class="sidebar-section-title">{html.escape(cat)}</summary>\n'

        for sc in active_subcats:
            entries_in = categorized.get((cat, sc), [])
            if not entries_in:
                continue
            sidebar_html += f'          <div class="sidebar-subsection">\n'
            sidebar_html += f'            <div class="sidebar-subsection-title">{html.escape(sc)} <span class="badge">{len(entries_in)}</span></div>\n'
            for e in entries_in:
                display_name = e['keywords'][0].title()
                sidebar_html += f'            <span class="sidebar-link" onclick="showEntry(\'{e["id"]}\')">{html.escape(display_name)}</span>\n'
            sidebar_html += f'          </div>\n'

        sidebar_html += f'        </details>\n'
        sidebar_html += f'      </div>\n'

    # Build entries HTML
    entries_html = ''
    first = True
    for cat, subcats in category_order:
        for sc in subcats:
            for e in categorized.get((cat, sc), []):
                active_class = ' active' if first else ''
                imm_class = ' imm-entry' if e['level'] >= 54 else ''
                first = False

                title = e['keywords'][0].title()
                aliases = ', '.join(e['keywords']).upper()
                body_html = convert_color_codes(e['body'])

                entries_html += f'      <div class="help-entry{active_class}{imm_class}" id="entry-{e["id"]}" data-level="{e["level"]}">\n'
                entries_html += f'        <div class="help-entry-title">{html.escape(title)}</div>\n'
                entries_html += f'        <div class="help-entry-aliases">{html.escape(aliases)}</div>\n'
                if e['level'] >= 54:
                    entries_html += f'        <div class="help-entry-level">Immortal Level {e["level"]}+</div>\n'
                entries_html += f'        <hr>\n'
                entries_html += f'        <pre>{body_html}</pre>\n'
                entries_html += f'      </div>\n\n'
        # Also handle subcats not in predefined list
        for key in categorized:
            if key[0] == cat and key[1] not in subcats:
                for e in categorized[key]:
                    active_class = ' active' if first else ''
                    imm_class = ' imm-entry' if e['level'] >= 54 else ''
                    first = False
                    title = e['keywords'][0].title()
                    aliases = ', '.join(e['keywords']).upper()
                    body_html = convert_color_codes(e['body'])
                    entries_html += f'      <div class="help-entry{active_class}{imm_class}" id="entry-{e["id"]}" data-level="{e["level"]}">\n'
                    entries_html += f'        <div class="help-entry-title">{html.escape(title)}</div>\n'
                    entries_html += f'        <div class="help-entry-aliases">{html.escape(aliases)}</div>\n'
                    if e['level'] >= 54:
                        entries_html += f'        <div class="help-entry-level">Immortal Level {e["level"]}+</div>\n'
                    entries_html += f'        <hr>\n'
                    entries_html += f'        <pre>{body_html}</pre>\n'
                    entries_html += f'      </div>\n\n'

    # Count stats
    total = len(entries)
    imm_count = sum(1 for e in entries if e['level'] >= 54)
    player_count = total - imm_count

    # Assemble full HTML
    full_html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Help Files — Redemption MUD</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --gold: #c9a84c; --gold-lt: #e8c96a;
      --red: #8b1a1a; --red-lt: #b03030;
      --bg: #0a0a0f; --bg2: #10101a; --bg3: #161626;
      --border: #2a2a3a; --text: #d4d0c8; --text-lt: #f0ece0;
    }}
    html {{ scroll-behavior: smooth; }}
    body {{ background: var(--bg); color: var(--text); font-family: 'Georgia', serif; line-height: 1.7; }}
    a {{ color: var(--gold); text-decoration: none; }}
    a:hover {{ color: var(--gold-lt); text-decoration: underline; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; }}

    nav {{
      position: sticky; top: 0; z-index: 100;
      background: rgba(10,10,15,0.95); backdrop-filter: blur(6px);
      border-bottom: 1px solid var(--border); padding: 0 1.5rem;
    }}
    .nav-inner {{ max-width: 1100px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; height: 62px; }}
    .nav-logo {{ font-size: 1.3rem; font-weight: bold; color: var(--gold); letter-spacing: 0.1em; text-transform: uppercase; }}
    .nav-links {{ display: flex; gap: 1.5rem; list-style: none; }}
    .nav-links a {{ color: var(--text); font-size: 0.85rem; letter-spacing: 0.05em; text-transform: uppercase; }}
    .nav-links a:hover {{ color: var(--gold); text-decoration: none; }}
    .nav-play-btn {{ background: var(--red); color: #fff !important; padding: 0.35rem 1rem; border-radius: 3px; border: 1px solid var(--red-lt); }}

    .page-hero {{
      padding: 5rem 1.5rem 3rem;
      background: linear-gradient(180deg, #08080e 0%, var(--bg2) 100%);
      border-bottom: 1px solid var(--border);
      text-align: center;
    }}
    .page-eyebrow {{ font-size: 0.8rem; letter-spacing: 0.3em; text-transform: uppercase; color: var(--gold); margin-bottom: 0.8rem; }}
    .page-title {{ font-size: clamp(2rem, 5vw, 3.5rem); color: var(--text-lt); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.8rem; }}
    .page-sub {{ font-size: 1rem; font-style: italic; color: var(--text); opacity: 0.8; max-width: 600px; margin: 0 auto 1.5rem; }}

    /* Search */
    .search-bar {{
      max-width: 500px; margin: 0 auto;
      display: flex; gap: 0;
    }}
    .search-bar input {{
      flex: 1;
      background: var(--bg3);
      border: 1px solid var(--border);
      border-right: none;
      border-radius: 4px 0 0 4px;
      padding: 0.7rem 1rem;
      color: var(--text-lt);
      font-family: 'Courier New', monospace;
      font-size: 0.9rem;
      outline: none;
    }}
    .search-bar input:focus {{ border-color: var(--gold); }}
    .search-bar button {{
      background: var(--red);
      border: 1px solid var(--red-lt);
      border-radius: 0 4px 4px 0;
      padding: 0.7rem 1.2rem;
      color: #fff;
      font-family: inherit;
      font-size: 0.85rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      cursor: pointer;
    }}
    .search-bar button:hover {{ background: var(--red-lt); }}

    .search-controls {{
      max-width: 500px; margin: 0.8rem auto 0;
      display: flex; align-items: center; justify-content: center; gap: 1.2rem;
    }}
    .search-controls label {{
      font-size: 0.82rem; color: var(--text); cursor: pointer;
      display: flex; align-items: center; gap: 0.4rem;
    }}
    .search-controls input[type="checkbox"] {{ accent-color: var(--gold); }}

    /* Layout */
    .help-layout {{
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 0;
      min-height: 80vh;
    }}
    .help-sidebar {{
      background: var(--bg2);
      border-right: 1px solid var(--border);
      padding: 1rem 0;
      position: sticky;
      top: 62px;
      height: calc(100vh - 62px);
      overflow-y: auto;
    }}

    .sidebar-filter {{
      padding: 0.5rem 1rem 0.8rem;
    }}
    .sidebar-filter input {{
      width: 100%;
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 0.45rem 0.7rem;
      color: var(--text-lt);
      font-family: 'Courier New', monospace;
      font-size: 0.8rem;
      outline: none;
    }}
    .sidebar-filter input:focus {{ border-color: var(--gold); }}

    .sidebar-section {{
      margin-bottom: 0.2rem;
    }}
    .sidebar-section details {{ }}
    .sidebar-section-title {{
      font-size: 0.72rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--gold);
      padding: 0.5rem 1rem;
      cursor: pointer;
      list-style: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .sidebar-section-title::-webkit-details-marker {{ display: none; }}
    .sidebar-section-title::after {{
      content: '\\25B6';
      font-size: 0.6rem;
      transition: transform 0.2s;
    }}
    details[open] > .sidebar-section-title::after {{
      transform: rotate(90deg);
    }}

    .sidebar-subsection {{
      margin-bottom: 0.3rem;
    }}
    .sidebar-subsection-title {{
      font-size: 0.7rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--text);
      opacity: 0.5;
      padding: 0.3rem 1.2rem;
    }}
    .badge {{
      background: rgba(201,168,76,0.15);
      color: var(--gold);
      font-size: 0.65rem;
      padding: 0.1rem 0.4rem;
      border-radius: 8px;
      margin-left: 0.4rem;
    }}
    .sidebar-link {{
      display: block;
      padding: 0.25rem 1.5rem;
      font-size: 0.82rem;
      color: var(--text);
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      border-left: 2px solid transparent;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .sidebar-link:hover, .sidebar-link.active {{
      background: rgba(201,168,76,0.08);
      color: var(--gold);
      border-left-color: var(--gold);
      text-decoration: none;
    }}

    .help-main {{ padding: 2rem; }}
    .help-entry {{
      display: none;
      max-width: 760px;
    }}
    .help-entry.active {{ display: block; }}
    .help-entry-title {{
      font-size: 1.6rem;
      color: var(--gold);
      letter-spacing: 0.06em;
      text-transform: uppercase;
      margin-bottom: 0.3rem;
    }}
    .help-entry-aliases {{
      font-size: 0.78rem;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--text);
      opacity: 0.5;
      margin-bottom: 0.5rem;
      font-family: 'Courier New', monospace;
    }}
    .help-entry-level {{
      font-size: 0.75rem;
      color: var(--red-lt);
      font-family: 'Courier New', monospace;
      margin-bottom: 0.5rem;
    }}
    .help-entry hr {{
      border: none;
      border-top: 1px solid var(--border);
      margin-bottom: 1rem;
    }}
    .help-entry p {{ margin-bottom: 1rem; font-size: 0.95rem; }}
    .help-entry pre {{
      background: rgba(0,0,0,0.3);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 1rem;
      font-family: 'Courier New', monospace;
      font-size: 0.85rem;
      color: var(--text-lt);
      overflow-x: auto;
      margin-bottom: 1rem;
      white-space: pre-wrap;
      line-height: 1.5;
    }}
    code {{
      font-family: 'Courier New', monospace;
      background: rgba(201,168,76,0.08);
      color: var(--gold);
      padding: 0.1rem 0.4rem;
      border-radius: 3px;
      font-size: 0.9em;
    }}

    /* search results */
    #search-results {{
      display: none;
      max-width: 760px;
    }}
    #search-results h2 {{ font-size: 1.2rem; color: var(--gold); margin-bottom: 1rem; }}
    .search-result-item {{
      background: var(--bg3);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 0.8rem 1rem;
      margin-bottom: 0.6rem;
      cursor: pointer;
      transition: border-color 0.15s;
    }}
    .search-result-item:hover {{ border-color: var(--gold); }}
    .search-result-name {{ color: var(--gold); font-size: 0.95rem; margin-bottom: 0.2rem; }}
    .search-result-preview {{ font-size: 0.82rem; color: var(--text); opacity: 0.7; }}

    /* Immortal toggle */
    .imm-entry {{ display: none !important; }}
    .imm-entry.active {{ display: none !important; }}
    body.show-imm .imm-entry {{ display: none; }}
    body.show-imm .imm-entry.active {{ display: block !important; }}
    body.show-imm .imm-section {{ display: block; }}
    .imm-section {{ display: none; }}

    footer {{ background: var(--bg2); border-top: 1px solid var(--border); padding: 2rem 1.5rem; text-align: center; }}
    .footer-logo {{ font-size: 1.3rem; color: var(--gold); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.4rem; }}
    .footer-copy {{ font-size: 0.78rem; color: var(--text); opacity: 0.35; }}

    @media (max-width: 700px) {{
      .help-layout {{ grid-template-columns: 1fr; }}
      .help-sidebar {{ position: static; height: auto; }}
      .nav-links {{ display: none; }}
    }}
  </style>
</head>
<body>

  <nav>
    <div class="nav-inner">
      <a href="index.html" class="nav-logo">Redemption</a>
      <ul class="nav-links">
        <li><a href="index.html">Home</a></li>
        <li><a href="newbie.html">New Players</a></li>
        <li><a href="crafting.html">Crafting</a></li>
        <li><a href="announcements.html">News</a></li>
        <li><a href="index.html#play" class="nav-play-btn">Play Now</a></li>
      </ul>
    </div>
  </nav>

  <div class="page-hero">
    <p class="page-eyebrow">Redemption MUD</p>
    <h1 class="page-title">Help Files</h1>
    <p class="page-sub">Browse or search the in-game help system. The same information available via <code>help &lt;topic&gt;</code> in-game.</p>
    <div class="search-bar">
      <input type="text" id="help-search" placeholder="Search {player_count} help topics..." autocomplete="off" />
      <button onclick="doSearch()">Search</button>
    </div>
    <div class="search-controls">
      <label><input type="checkbox" id="imm-toggle" onchange="toggleImm()"> Show Immortal entries ({imm_count})</label>
    </div>
  </div>

  <div class="help-layout">
    <div class="help-sidebar">
      <div class="sidebar-filter">
        <input type="text" id="sidebar-search" placeholder="Filter menu..." oninput="filterSidebar()" />
      </div>

{sidebar_html}
    </div>

    <div class="help-main">
      <div id="search-results">
        <h2 id="search-heading"></h2>
        <div id="search-list"></div>
      </div>

{entries_html}
    </div>
  </div>

  <footer>
    <div class="footer-logo">Redemption MUD</div>
    <div class="footer-copy">&copy; Redemption MUD. Free to play. {total} help entries.</div>
  </footer>

  <script>
    function showEntry(id) {{
      document.querySelectorAll('.help-entry').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));
      document.getElementById('search-results').style.display = 'none';

      const entry = document.getElementById('entry-' + id);
      if (entry) {{
        entry.classList.add('active');
        entry.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}

      document.querySelectorAll('.sidebar-link').forEach(el => {{
        if (el.getAttribute('onclick') === "showEntry('" + id + "')") {{
          el.classList.add('active');
        }}
      }});
    }}

    function doSearch() {{
      const q = document.getElementById('help-search').value.toLowerCase().trim();
      if (!q) return;

      document.querySelectorAll('.help-entry').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));

      const results = [];
      document.querySelectorAll('.help-entry').forEach(el => {{
        // Skip imm entries if toggle is off
        if (el.classList.contains('imm-entry') && !document.body.classList.contains('show-imm')) return;
        const text = el.textContent.toLowerCase();
        if (text.includes(q)) {{
          const id = el.id.replace('entry-', '');
          results.push({{
            id,
            title: el.querySelector('.help-entry-title').textContent,
            preview: el.querySelector('pre') ? el.querySelector('pre').textContent.slice(0, 120) : ''
          }});
        }}
      }});

      const sr = document.getElementById('search-results');
      const sl = document.getElementById('search-list');
      document.getElementById('search-heading').textContent = results.length + ' result' + (results.length !== 1 ? 's' : '') + ' for "' + q + '"';
      sl.innerHTML = '';
      results.forEach(r => {{
        sl.innerHTML += '<div class="search-result-item" onclick="showEntry(\\'' + r.id + '\\')">' +
          '<div class="search-result-name">' + r.title + '</div>' +
          '<div class="search-result-preview">' + r.preview + '</div>' +
          '</div>';
      }});
      sr.style.display = 'block';
    }}

    document.getElementById('help-search').addEventListener('keydown', e => {{
      if (e.key === 'Enter') doSearch();
    }});

    function toggleImm() {{
      if (document.getElementById('imm-toggle').checked) {{
        document.body.classList.add('show-imm');
      }} else {{
        document.body.classList.remove('show-imm');
        // If current active entry is imm, deactivate it
        const active = document.querySelector('.help-entry.active.imm-entry');
        if (active) active.classList.remove('active');
      }}
    }}

    function filterSidebar() {{
      const q = document.getElementById('sidebar-search').value.toLowerCase().trim();
      document.querySelectorAll('.sidebar-link').forEach(el => {{
        if (!q || el.textContent.toLowerCase().includes(q)) {{
          el.style.display = '';
        }} else {{
          el.style.display = 'none';
        }}
      }});
    }}
  </script>

</body>
</html>'''

    return full_html


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("Parsing help_db.txt...")
    entries = parse_help_db(INPUT_FILE)
    print(f"Found {len(entries)} entries.")

    # Print category breakdown
    cats = {}
    for e in entries:
        cat, subcat = categorize_entry(e)
        key = f"{cat} > {subcat}"
        cats[key] = cats.get(key, 0) + 1

    print("\nCategory breakdown:")
    for k in sorted(cats.keys()):
        print(f"  {k}: {cats[k]}")

    print(f"\nGenerating {OUTPUT_FILE}...")
    html_content = generate_html(entries)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Done! Generated {len(html_content):,} bytes.")
