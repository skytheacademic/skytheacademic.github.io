#!/usr/bin/env python3
"""Generate the Research page cards and the CV entry fragments from the single
source of truth at _data/publications.yml.

Run from the repo root:  python3 scripts/build_publications.py

Writes:
  _pages/research.md         (replaces the #grid block)
  cv/pubs_papers.tex         (Peer-Reviewed + In-Progress entries)
  cv/pubs_other.tex          (Other Publications / book chapters)
and, one time, rewrites cv.tex to \\input those fragments.
"""
import os, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)

RES_STATUS = {  # status -> (card label, stage 1-4)
    "published": ("Published", 4), "forthcoming": ("Forthcoming", 4),
    "rr": ("R&amp;R", 3), "under_review": ("Under review", 2),
    "working": ("Working paper", 1), "wip": ("Work in progress", 1),
}
TOPIC_LABEL = {"pk": "Peacekeeping", "gender": "Gender", "pmsc": "PMSCs", "methods": "Methods"}

def surname(n): return n.split()[-1]

def research_authors(co):
    if not co: return None
    if len(co) == 1: return co[0]                      # 1 coauthor -> full name
    s = [surname(c) for c in co]                       # 2+ -> surnames
    return (s[0] + " &amp; " + s[1]) if len(s) == 2 else (", ".join(s[:-1]) + " &amp; " + s[-1])

def cv_authors(co):
    if not co: return None
    if len(co) == 1: return co[0]
    return (co[0] + " and " + co[1]) if len(co) == 2 else (", ".join(co[:-1]) + ", and " + co[-1])

def track(n):
    out = []
    for i in range(1, 5):
        out.append('<span class="dot on"></span>' if i <= n else '<span class="dot"></span>')
        if i < 4:
            out.append('<span class="ln on"></span>' if i < n else '<span class="ln"></span>')
    return "".join(out)

def card(e):
    dt = " ".join(e["topics"])
    pills = "".join('<span class="pill %s">%s</span>' % (t, TOPIC_LABEL[t]) for t in e["topics"])
    label, stage = RES_STATUS[e["status"]]
    dtag = '<span class="dtag">%s</span>' % e["dtag"] if e.get("dtag") else ""
    stat = ('<div class="stat"><span class="stagelbl">%s</span>'
            '<div class="track" role="img" aria-label="Stage %d of 4">%s</div>%s</div>' % (label, stage, track(stage), dtag))
    tags = '<div class="tags"><div class="topics">%s</div>%s</div>' % (pills, stat)
    co = e.get("coauthors") or []
    mauth = '<span class="m-auth">with %s</span>' % research_authors(co) if co else ""
    mven = '<span class="m-ven">%s</span>' % e["venue"] if e.get("venue") else ""
    meta = '<div class="meta">%s%s</div>' % (mauth, mven) if (mauth or mven) else ""
    awards = ""
    if e.get("awards"):
        chips = "".join('<span class="aw"><i class="fas fa-%s" aria-hidden="true"></i> %s</span>'
                        % (a.get("icon", "award"), a["text"]) for a in e["awards"])
        awards = '<div class="awards">%s</div>' % chips
    ablabel = '<span class="lbl">Abstract</span>' if e.get("abstract") else ""
    text = e.get("abstract") or e.get("desc") or ""
    links = ""
    if e.get("links"):
        la = "".join('<a href="%s" target="_blank" rel="noopener">%s</a>' % (l["url"], l["label"]) for l in e["links"])
        links = '<div class="links">%s</div>' % la
    detail = '<div class="detail"><div class="ab">%s%s%s</div></div>' % (ablabel, text, links)
    banner = '\n      <div class="jmp-banner">&#9733; Job market paper</div>' if e.get("jmp") else ""
    jmpcls = " card--jmp" if e.get("jmp") else ""
    return ('    <div class="card%s" data-topic="%s">\n'
            '      <span class="chev">&#9662;</span>\n'
            '      %s\n      <h3>%s</h3>\n      %s%s%s%s\n    </div>'
            % (jmpcls, dt, tags, e["title"], meta, awards, detail, banner))

def cv_entry(e):
    grad = "T" if e.get("grad") else "F"
    ext = "T" if e.get("ext") else "F"
    title = e.get("title_cv", e["title"])
    co = e.get("coauthors") or []
    cv = e["cv"]
    auth = " (with %s)" % cv_authors(co) if co else ""
    if cv["section"] == "other":
        body = "``%s,''%s in the \\textit{%s}, Edited by %s. Forthcoming %s, %s." % (
            title, auth, cv["book"], cv["editors"], cv["year"], cv["publisher"])
    else:
        st, venue = e["status"], e.get("venue", "")
        if st == "published":      stext = ("\\textit{%s}. %s" % (venue, cv.get("pages", ""))).rstrip()
        elif st == "forthcoming":  stext = "\\textit{%s, %s}." % (cv.get("forthcoming_word", "Forthcoming"), venue)
        elif st == "rr":           stext = "\\textit{R\\&R, %s}." % venue
        elif st == "under_review": stext = "\\textit{Under Review, %s}." % venue
        elif st == "working":      stext = "\\textit{Working Paper}."
        else:                      stext = "\\textit{Work in progress}."
        link = " \\href{%s}\\faFilePdf" % e["links"][0]["url"] if e.get("links") else ""
        body = "``%s”%s. %s%s" % (title, auth, stext, link)
        if cv.get("items"):
            items = "".join("\n    \\item %s" % it for it in cv["items"])
            body += "\n\\begin{itemize}[nosep]%s\n\\end{itemize}\n\\eatvspace" % items
    return "\\autoentry{%s}{%s}{%%\n%s\n}\n" % (grad, ext, body)

def main():
    pubs = yaml.safe_load(open(p("_data", "publications.yml")))
    shown = [e for e in pubs if e.get("show_on_research", True)]

    # --- Research page: replace the #grid block ---
    rm = open(p("_pages", "research.md")).read()
    start = rm.index('<div class="grid" id="grid">')
    fig = rm.index('<h3 class="psec">Selected figures</h3>')
    grid_end = rm.rindex("</div>", start, fig) + len("</div>")
    new_grid = '<div class="grid" id="grid">\n' + "\n".join(card(e) for e in shown) + "\n</div>"
    open(p("_pages", "research.md"), "w").write(rm[:start] + new_grid + rm[grid_end:])

    # --- CV fragments ---
    def sec(name): return sorted([e for e in pubs if e["cv"]["section"] == name], key=lambda e: e["cv"]["order"])
    papers = ("\\subsubsection*{Peer-Reviewed Journal Articles}\n\n"
              + "\n".join(cv_entry(e) for e in sec("journal"))
              + "\n\\setcounter{inprog}{1} \n\\subsubsection*{\\textit{In-Progress}}\n\n"
              + "\n".join(cv_entry(e) for e in sec("inprogress")))
    other = ("\\subsubsection*{\\textit{Other Publications}}\n\\setcounter{inprog}{1} \n\n"
             + "\n".join(cv_entry(e) for e in sec("other")))
    open(p("cv", "pubs_papers.tex"), "w").write(papers + "\n")
    open(p("cv", "pubs_other.tex"), "w").write(other + "\n")

    # --- wire cv.tex once ---
    cv = open(p("cv", "cv.tex")).read()
    if "\\input{pubs_papers.tex}" not in cv:
        a = cv.index("\\subsubsection*{Peer-Reviewed Journal Articles}")
        b = cv.index("\\subsubsection*{\\textit{Non Peer-Reviewed Publications}}")
        cv = cv[:a] + "\\input{pubs_papers.tex}\n\n" + cv[b:]
        c = cv.index("\\subsubsection*{\\textit{Other Publications}}")
        d = cv.index("% \\nocite{*}")
        cv = cv[:c] + "\\input{pubs_other.tex}\n\n" + cv[d:]
        open(p("cv", "cv.tex"), "w").write(cv)
        wired = True
    else:
        wired = False

    print("research cards: %d  | journal: %d  in-progress: %d  other: %d  | cv.tex wired: %s"
          % (len(shown), len(sec("journal")), len(sec("inprogress")), len(sec("other")), wired))

if __name__ == "__main__":
    main()
