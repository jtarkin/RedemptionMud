#!/usr/bin/env python3
"""
Migrate help entries from helpfiles.html into separate fragment files
under website/entries/
"""
import re
import os

SRC = r'C:\Users\Fahmie\Documents\rdm\website\helpfiles.html'
ENTRIES_DIR = r'C:\Users\Fahmie\Documents\rdm\website\entries'

# Mapping from entry id prefix -> fragment file name
def categorize(entry_id, entry_classes):
    if 'imm-entry' in entry_classes:
        return 'immortals'
    if entry_id.startswith('entry-gs-'):
        return 'getting-started'
    if entry_id.startswith('entry-combat-') or entry_id == 'entry-consider':
        return 'combat'
    if entry_id.startswith('entry-skills-'):
        return 'skills'
    if entry_id.startswith('entry-spells-'):
        return 'spells'
    if entry_id.startswith('entry-character-'):
        return 'character'
    if entry_id.startswith('entry-world-'):
        return 'world'
    if entry_id.startswith('entry-clans-'):
        return 'clans'
    if entry_id.startswith('entry-imm-'):
        return 'immortals'
    if entry_id.startswith('entry-race-'):
        return 'races'
    if entry_id.startswith('entry-class-'):
        return 'classes'
    if entry_id.startswith('entry-misc-'):
        return 'misc'
    return 'misc'

with open(SRC, 'r', encoding='utf-8') as f:
    content = f.read()

# Strip carriage returns
content = content.replace('\r', '')

lines = content.split('\n')

# Find the range of the help-main content: from first help-entry to closing </div> of help-main
# We'll extract the block between line 596 (first entry) and line 7244 (last </div> before </div></div>)
# Strategy: parse line by line, extract all help-entry divs with proper nesting

# Collect entries: list of (category, full_html_block)
entries_by_category = {}
CATEGORIES = ['getting-started','combat','skills','spells','character',
               'world','clans','races','classes','misc','immortals']
for c in CATEGORIES:
    entries_by_category[c] = []

# We'll scan for <div class="help-entry..." id="entry-..."> blocks
# Track nesting depth to find the matching closing </div>
in_entry = False
depth = 0
current_lines = []
current_id = ''
current_classes = ''

# Lines to keep in the main file (non-entry content inside help-main)
# We want to remove entry divs but keep search-results and help-landing
entries_start_line = None
entries_end_line = None

i = 0
while i < len(lines):
    line = lines[i]

    if not in_entry:
        # Look for start of a help-entry div
        m = re.match(r'\s*<div class="(help-entry[^"]*)"[^>]*id="(entry-[^"]+)"', line)
        if m:
            current_classes = m.group(1)
            current_id = m.group(2)
            in_entry = True
            depth = line.count('<div') - line.count('</div')
            current_lines = [line]
            if entries_start_line is None:
                entries_start_line = i
    else:
        current_lines.append(line)
        depth += line.count('<div') - line.count('</div')
        if depth <= 0:
            # Entry complete
            block = '\n'.join(current_lines)
            cat = categorize(current_id, current_classes)
            entries_by_category[cat].append(block)
            entries_end_line = i
            in_entry = False
            current_lines = []
            current_id = ''

    i += 1

print(f"Entry range: lines {entries_start_line}–{entries_end_line}")
for cat, blocks in entries_by_category.items():
    print(f"  {cat}: {len(blocks)} entries")

# Create entries directory
os.makedirs(ENTRIES_DIR, exist_ok=True)

# Write fragment files
for cat, blocks in entries_by_category.items():
    out_path = os.path.join(ENTRIES_DIR, f'{cat}.html')
    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n\n'.join(blocks) + '\n')
    print(f"Wrote {out_path} ({len(blocks)} entries)")

# Build new helpfiles.html: replace the entries block with a comment
# Keep everything up to (and including) help-landing closing </div>,
# then insert a loader comment, then keep everything from the </div></div> onward

# The entries in the file go from entries_start_line to entries_end_line (inclusive)
# Lines before entries_start_line: keep as-is
# Lines entries_start_line..entries_end_line: replace with comment
# Lines after entries_end_line: keep as-is

# Find the JS back-link injection block to replace with the new loader version
new_content_lines = (
    lines[:entries_start_line]
    + ['      <!-- entries loaded dynamically by JS loader below -->']
    + lines[entries_end_line + 1:]
)

new_content = '\n'.join(new_content_lines)

# Replace the static back-link injection with one that runs after fetch
OLD_BACKLINK = """    // Inject "back to help" link into every help entry
    document.querySelectorAll('.help-entry').forEach(el => {
      const back = document.createElement('div');
      back.className = 'entry-back';
      back.textContent = '\\u2190 Back to Help';
      back.onclick = showLanding;
      el.prepend(back);
    });"""

NEW_LOADER = """    // Load entry fragments then inject back-to-help links
    const _sections = ['getting-started','combat','skills','spells','character',
                       'world','clans','races','classes','misc','immortals'];
    const _helpMain = document.querySelector('.help-main');
    function _injectBackLinks() {
      document.querySelectorAll('.help-entry').forEach(el => {
        if (el.querySelector('.entry-back')) return;
        const back = document.createElement('div');
        back.className = 'entry-back';
        back.textContent = '\\u2190 Back to Help';
        back.onclick = showLanding;
        el.prepend(back);
      });
    }
    Promise.all(_sections.map(s =>
      fetch('entries/' + s + '.html').then(r => r.text()).catch(() => '')
    )).then(chunks => {
      chunks.forEach(html => _helpMain.insertAdjacentHTML('beforeend', html));
      _injectBackLinks();
    });"""

new_content = new_content.replace(OLD_BACKLINK, NEW_LOADER)

with open(SRC, 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_content)

print(f"\nDone. helpfiles.html rewritten. Entries extracted to {ENTRIES_DIR}/")
