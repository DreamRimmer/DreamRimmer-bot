# Author: [[:en:User:DreamRimmer]] © 2026
# Script to update entries at https://ur.wikiquote.org/wiki/سانچہ:New_pages
import pywikibot
from pywikibot import pagegenerators

site = pywikibot.Site("wikiquote:ur")
gen = pagegenerators.NewpagesPageGenerator(site=site, namespaces=(0,), total=15)
pages = []
image_map = {}

for page in gen:
    pages.append(page.title())
    for filepage in page.imagelinks():
        title = filepage.title()
        if "Wikipedia-logo" in title:
            continue
        image_map.setdefault(page.title(), []).append(title.replace("فائل:", "").replace("File:", ""))

template = pywikibot.Page(site, "Template:New pages")
old_text = template.text

page_lines = "\n".join(f":[[{p}]]" for p in pages)
new_list_block = f"<!-- List Top -->\n{page_lines}\n<!-- List Bottom -->"

img_data = next(((p, image_map[p][0]) for p in pages if p in image_map and image_map[p]), (None, None))

if img_data[0] and img_data[1]:
    new_img_block = f"<!-- Image start -->\n[[File:{img_data[1]}|thumb|ویکی اقتباس میں نیا: [[{img_data[0]}]]]]\n<!-- Image end -->"
    text = old_text.split("<!-- List Top -->", 1)[0] + new_list_block + old_text.split("<!-- List Bottom -->", 1)[1]
    text = text.split("<!-- Image start -->", 1)[0] + new_img_block + text.split("<!-- Image end -->", 1)[1]
else:
    text = old_text.split("<!-- List Top -->", 1)[0] + new_list_block + old_text.split("<!-- List Bottom -->", 1)[1]

#pywikibot.showDiff(old_text, text)
template.text = text
print(text)
template.save(summary="update list (bot)")
