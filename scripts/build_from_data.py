#!/usr/bin/env python3
"""Generate the website pages AND the CV entry fragments from the single-source
data files in _data/.  Run from the repo root:

    python3 scripts/build_from_data.py

Source -> outputs:
  _data/publications.yml  -> research.md cards   + cv/pubs_papers.tex, pubs_other.tex
  _data/presentations.yml -> presentations.md    + cv/pubs_invited.tex, pubs_conferences.tex
  _data/teaching.yml      -> teaching.md courses + cv/pubs_teaching.tex
  _data/briefs.yml        -> policy.md briefs     + cv/pubs_briefs.tex

Page sections are wrapped in <!-- BUILD:name --> ... <!-- /BUILD:name --> markers
and replaced in place (idempotent). cv.tex \\input's the fragments (wired once).
"""
import os, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(ROOT, *a)
def load(name): return yaml.safe_load(open(P("_data", name)))

# ---------- shared helpers ----------
def surname(n): return n.split()[-1]
def research_authors(co):
    if not co: return None
    if len(co) == 1: return co[0]
    s = [surname(c) for c in co]
    return (s[0]+" &amp; "+s[1]) if len(s) == 2 else (", ".join(s[:-1])+" &amp; "+s[-1])
def cv_authors(co):
    if not co: return None
    if len(co) == 1: return co[0]
    return (co[0]+" and "+co[1]) if len(co) == 2 else (", ".join(co[:-1])+", and "+co[-1])
def join_and(names):  # "A, B, and C" (HTML/plain)
    if len(names) == 1: return names[0]
    if len(names) == 2: return names[0]+" and "+names[1]
    return ", ".join(names[:-1])+", and "+names[-1]

def inject(text, name, start_anchor, end_anchor, generated):
    """Replace a page section between BUILD markers; on first run, find it by
    start_anchor .. end_anchor (next heading, or None for end-of-file)."""
    ms, me = "<!-- BUILD:%s -->" % name, "<!-- /BUILD:%s -->" % name
    block = ms + "\n" + generated.strip() + "\n" + me
    if ms in text and me in text:
        a = text.index(ms); b = text.index(me)+len(me)
        return text[:a]+block+text[b:]
    a = text.index(start_anchor)
    b = text.index(end_anchor, a) if end_anchor else len(text)
    tail = ("\n\n"+text[b:]) if end_anchor else "\n"
    return text[:a]+block+tail

def wire_input(cv, inputname, start_anchor, end_anchor):
    """One-time: replace cv.tex content between start_anchor (kept) and end_anchor
    (kept) with \\input{inputname}."""
    inc = "\\input{%s}" % inputname
    if inc in cv: return cv
    a = cv.index(start_anchor)+len(start_anchor)
    b = cv.index(end_anchor, a)
    return cv[:a]+"\n"+inc+"\n\n"+cv[b:]

# ====================== PUBLICATIONS ======================
RES_STATUS = {"published":("Published",4),"forthcoming":("Forthcoming",4),"rr":("R&amp;R",3),
              "cond_accept":("Conditionally accepted",4),
              "under_review":("Under review",2),"working":("Working paper",1),"wip":("Work in progress",1)}
TOPIC_LABEL = {"pk":"Peacekeeping","gender":"Gender","pmsc":"PMSCs","methods":"Methods"}
def track(n):
    o=[]
    for i in range(1,5):
        o.append('<span class="dot on"></span>' if i<=n else '<span class="dot"></span>')
        if i<4: o.append('<span class="ln on"></span>' if i<n else '<span class="ln"></span>')
    return "".join(o)
def pub_card(e):
    dt=" ".join(e["topics"]); pills="".join('<span class="pill %s">%s</span>'%(t,TOPIC_LABEL[t]) for t in e["topics"])
    label,stage=RES_STATUS[e["status"]]
    dtag='<span class="dtag">%s</span>'%e["dtag"] if e.get("dtag") else ""
    stat='<div class="stat"><span class="stagelbl">%s</span><div class="track" role="img" aria-label="Stage %d of 4">%s</div>%s</div>'%(label,stage,track(stage),dtag)
    tags='<div class="tags"><div class="topics">%s</div>%s</div>'%(pills,stat)
    co=e.get("coauthors") or []
    mauth='<span class="m-auth">with %s</span>'%research_authors(co) if co else ""
    mven='<span class="m-ven">%s</span>'%e["venue"] if e.get("venue") else ""
    meta='<div class="meta">%s%s</div>'%(mauth,mven) if (mauth or mven) else ""
    awards=""
    if e.get("awards"):
        chips="".join('<span class="aw"><i class="fas fa-%s" aria-hidden="true"></i> %s</span>'%(a.get("icon","award"),a["text"]) for a in e["awards"])
        awards='<div class="awards">%s</div>'%chips
    ablabel='<span class="lbl">Abstract</span>' if e.get("abstract") else ""
    text=e.get("abstract") or e.get("desc") or ""
    links=""
    if e.get("links"):
        la="".join('<a href="%s" target="_blank" rel="noopener">%s</a>'%(l["url"],l["label"]) for l in e["links"])
        links='<div class="links">%s</div>'%la
    detail='<div class="detail"><div class="ab">%s%s%s</div></div>'%(ablabel,text,links)
    banner='\n      <div class="jmp-banner">&#9733; Job market paper</div>' if e.get("jmp") else ""
    jmpcls=" card--jmp" if e.get("jmp") else ""
    return ('    <div class="card%s" data-topic="%s">\n      <span class="chev">&#9662;</span>\n      %s\n      <h3>%s</h3>\n      %s%s%s%s\n    </div>'
            %(jmpcls,dt,tags,e["title"],meta,awards,detail,banner))
def pub_cv(e):
    grad="T" if e.get("grad") else "F"; ext="T" if e.get("ext") else "F"
    title=e.get("title_cv",e["title"]); co=e.get("coauthors") or []; cv=e["cv"]
    auth=" (with %s)"%cv_authors(co) if co else ""
    if cv["section"]=="other":
        body="``%s,''%s in the \\textit{%s}, Edited by %s. Forthcoming %s, %s."%(title,auth,cv["book"],cv["editors"],cv["year"],cv["publisher"])
    else:
        st,venue=e["status"],e.get("venue","")
        if st=="published": stext=("\\textit{%s}. %s"%(venue,cv.get("pages",""))).rstrip()
        elif st=="forthcoming": stext="\\textit{%s, %s}."%(cv.get("forthcoming_word","Forthcoming"),venue)
        elif st=="cond_accept": stext="\\textit{Conditionally Accepted, %s}."%venue
        elif st=="rr": stext="\\textit{R\\&R, %s}."%venue
        elif st=="under_review": stext="\\textit{Under Review, %s}."%venue
        elif st=="working": stext="\\textit{Working Paper}."
        else: stext="\\textit{Work in progress}."
        link=" \\href{%s}\\faFilePdf"%e["links"][0]["url"] if e.get("links") else ""
        body="``%s”%s. %s%s"%(title,auth,stext,link)
        if cv.get("items"):
            items="".join("\n    \\item %s"%it for it in cv["items"])
            body+="\n\\begin{itemize}[nosep]%s\n\\end{itemize}\n\\eatvspace"%items
    return "\\autoentry{%s}{%s}{%%\n%s\n}\n"%(grad,ext,body)

# ====================== PRESENTATIONS ======================
def featured_html(items):
    cards=[]
    for f in items:
        alt = "%s presentation slide"%f["venue"] if f["kind"]=="Talk" else "%s poster"%f["venue"]
        cards.append('  <article class="featcard">\n'
            '    <a class="thumb" href="%s" target="_blank" rel="noopener"><img src="%s" alt="%s"></a>\n'
            '    <div class="body">\n      <div class="k">%s &middot; %s</div>\n      <h4>%s</h4>\n'
            '      <a class="pdf" href="%s" target="_blank" rel="noopener"><i class="fas fa-file-pdf" aria-hidden="true"></i> %s</a>\n'
            '    </div>\n  </article>'%(f["pdf"],f["image"],alt,f["venue"],f["kind"],f["title"],f["pdf"],f["pdf_label"]))
    return '<h3 class="psec">Featured</h3>\n<div class="feat">\n'+"\n".join(cards)+'\n</div>'
def invited_html(items):
    rows=[]
    for t in items:
        host='<div class="host">%s</div>'%t["host"] if t.get("host") else ""
        pdf='<a class="pdf" href="%s" target="_blank" rel="noopener"><i class="fas fa-file-pdf" aria-hidden="true"></i> Archived presentation (PDF)</a>'%t["pdf"] if t.get("pdf") else ""
        rows.append('  <div class="italk"><div class="when">%s</div><div class="what"><h4>%s</h4>%s%s</div></div>'%(t["when"],t["title"],host,pdf))
    return '<h3 class="psec">Invited talks and workshops</h3>\n<div class="invited">\n'+"\n".join(rows)+'\n</div>'
def conferences_html(items):
    legend=('  <p class="legend"><b>C</b> Chair &middot; <b>D</b> Discussant &middot; <b>O</b> Panel organizer &middot; '
            '<b>P</b> Panel participant &middot; <b>R</b> Roundtable &middot; <b>Wo</b> Workshop organizer &middot; <b>Wp</b> Workshop participant</p>')
    rows=[]
    for c in items:
        sub='<small>%s</small>'%c["full"] if c.get("full") else ""
        chips="".join('<span class="yr"><b>%s</b> <i>%s</i></span>'%(y,r) for y,r in c["years"])
        rows.append('  <div class="conf"><div class="nm">%s%s</div><div class="yrs">%s</div></div>'%(c["name"],sub,chips))
    return '<h3 class="psec">Conference participation</h3>\n<div class="confs">\n'+legend+"\n"+"\n".join(rows)+'\n</div>'
def cv_invited(items):
    out=[]
    for t in items:
        body=t["title"]+(" (\\textit{Host:} %s)"%t["host"] if t.get("host") else "")
        out.append("\\begin{datetabular}{6em}\n\\dateentry{%s}{\n%s\n}\n\\end{datetabular}"%(t["when"],body))
    return "\n\n".join(out)+"\n"
def cv_conferences(items):
    out=[]
    for c in items:
        years=", ".join("%s (%s)"%(y,r) for y,r in c["years"])
        out.append("\\begin{datetabular}{6em}\n\\dateentry{%s}{%s}\n\\end{datetabular}"%(c["name"],years))
    # Leading blank line forces a \par so the first table doesn't run into the
    # preceding legend paragraph (the section's \vspace{1em} alone doesn't break it).
    return "\n"+"\n\n".join(out)+"\n"

# ====================== TEACHING ======================
def teaching_courses_html(courses):
    def dedupe(role):
        seen={}; order=[]
        for c in courses:
            if c["role"]!=role or not c.get("code"): continue
            k=c["code"]
            if k not in seen: seen[k]=dict(code=c["code"], title=c["title"], grad=False); order.append(k)
            if role=="ta" and c.get("level")=="grad": seen[k]["grad"]=True
        return [seen[k] for k in order]
    def li(c):
        star='<span class="grad-star">*</span>' if c.get("grad") else ""
        return "      <li>%s - %s%s</li>"%(c["code"],c["title"],star)
    inst="\n".join(li(c) for c in dedupe("instructor"))
    ta="\n".join(li(c) for c in dedupe("ta"))
    return ('<h3 class="psec">Courses <span class="psec-note">(<span class="grad-star">*</span> indicates graduate-level teaching)</span></h3>\n'
            '<div class="courses">\n  <article class="course">\n    <span class="role">Instructor of record</span>\n    <ul>\n%s\n    </ul>\n  </article>\n'
            '  <article class="course">\n    <span class="role">Teaching assistant</span>\n    <ul>\n%s\n    </ul>\n  </article>\n</div>'%(inst,ta))
def cv_teaching(courses):
    def entry(c, bold_prof=True):
        name=c.get("title_cv", c["title"]); name=("%s - %s"%(c["code"],name)) if c.get("code") else name
        prof=" (%s)"%c["prof"] if c.get("prof") else ""
        inner=("\\textbf{%s}%s"%(name,prof))
        return "\\begin{datetabular}{6em}\n\\dateentry{%s}{\n%s}\n\\end{datetabular}"%(c["when"],inner)
    inst=[c for c in courses if c["role"]=="instructor"]
    tg=[c for c in courses if c["role"]=="ta" and c.get("level")=="grad"]
    tu=[c for c in courses if c["role"]=="ta" and c.get("level")=="undergrad"]
    def block(title, items): return "\\subsubsection*{\\textit{%s}}\n\n"%title + "\n\n".join(entry(c) for c in items) + "\n\n\\eatvspace\n"
    return (block("Instructor of Record", inst) + "\n" + block("Teaching Assistant - Graduate Courses/Workshops", tg)
            + "\n" + block("Teaching Assistant - Undergraduate Courses", tu))

# ====================== BRIEFS ======================
def briefs_html(items):
    arts=[]
    for b in items:
        others=[a for a in b["authors"] if a!="Sky Kunkel"]
        arts.append('  <article class="brief">\n    <h4>%s</h4>\n'
            '    <p class="bmeta"><span class="b-auth">with %s</span><span class="b-year">%s</span></p>\n'
            '    <a class="brief-link" href="%s"><i class="fas fa-file-pdf" aria-hidden="true"></i> Read the brief</a>\n  </article>'
            %(b["title"], join_and(others), b["year"], b["link"]))
    return '<h3 class="psec">Policy briefs</h3>\n<div class="briefs">\n'+"\n".join(arts)+'\n</div>'
def cv_briefs(items):
    out=[]
    for b in items:
        auth=", ".join(("\\textbf{Sky Kunkel}" if a=="Sky Kunkel" else a) for a in b["authors"][:-1])
        last=b["authors"][-1]; last="\\textbf{Sky Kunkel}" if last=="Sky Kunkel" else last
        authstr=auth+", and "+last
        out.append('\\autoentry{T}{T}{%%\n``%s," %s. %s. \\textit{GSS Lab Policy Brief.} \\href{%s}\\faFilePdf\n}'
                   %(b["title"], b["year"], authstr, b["link"]))
    return "\n\n".join(out)+"\n"

# ====================== MAIN ======================
def main():
    pubs=load("publications.yml"); pres=load("presentations.yml"); teach=load("teaching.yml")["courses"]; briefs=load("briefs.yml")["briefs"]

    # --- research.md grid ---
    rm=open(P("_pages","research.md")).read()
    s=rm.index('<div class="grid" id="grid">'); fig=rm.index('<h3 class="psec">Selected figures</h3>')
    ge=rm.rindex("</div>",s,fig)+len("</div>")
    grid='<div class="grid" id="grid">\n'+"\n".join(pub_card(e) for e in pubs if e.get("show_on_research",True))+"\n</div>"
    open(P("_pages","research.md"),"w").write(rm[:s]+grid+rm[ge:])

    # --- presentations.md ---
    pm=open(P("_pages","presentations.md")).read()
    pm=inject(pm,"featured",'<h3 class="psec">Featured</h3>','<h3 class="psec">Invited talks and workshops</h3>',featured_html(pres["featured"]))
    pm=inject(pm,"invited",'<h3 class="psec">Invited talks and workshops</h3>','<h3 class="psec">Conference participation</h3>',invited_html(pres["invited_talks"]))
    pm=inject(pm,"conferences",'<h3 class="psec">Conference participation</h3>',None,conferences_html(pres["conferences"]))
    open(P("_pages","presentations.md"),"w").write(pm)

    # --- teaching.md ---
    tm=open(P("_pages","teaching.md")).read()
    tm=inject(tm,"courses",'<h3 class="psec">Courses','<h3 class="psec">Student feedback</h3>',teaching_courses_html(teach))
    open(P("_pages","teaching.md"),"w").write(tm)

    # --- policy.md ---
    po=open(P("_pages","policy.md")).read()
    po=inject(po,"briefs",'<h3 class="psec">Policy briefs</h3>',None,briefs_html(briefs))
    open(P("_pages","policy.md"),"w").write(po)

    # --- CV fragments ---
    def sec(name): return sorted([e for e in pubs if e["cv"]["section"]==name], key=lambda e:e["cv"]["order"])
    papers=("\\subsubsection*{Peer-Reviewed Journal Articles}\n\n"+"\n".join(pub_cv(e) for e in sec("journal"))
            +"\n\\setcounter{inprog}{1} \n\\subsubsection*{\\textit{In-Progress}}\n\n"+"\n".join(pub_cv(e) for e in sec("inprogress")))
    open(P("cv","pubs_papers.tex"),"w").write(papers+"\n")
    open(P("cv","pubs_other.tex"),"w").write("\\subsubsection*{\\textit{Other Publications}}\n\\setcounter{inprog}{1} \n\n"+"\n".join(pub_cv(e) for e in sec("other"))+"\n")
    open(P("cv","pubs_invited.tex"),"w").write(cv_invited(pres["invited_talks"]))
    open(P("cv","pubs_conferences.tex"),"w").write(cv_conferences(pres["conferences"]))
    open(P("cv","pubs_teaching.tex"),"w").write(cv_teaching(teach))
    open(P("cv","pubs_briefs.tex"),"w").write(cv_briefs(briefs))

    # --- wire cv.tex (idempotent) ---
    cv=open(P("cv","cv.tex")).read()
    cv=wire_input(cv,"pubs_invited.tex","\\section{Invited Talks and Workshops}","%%%%%%%%%%%%%%%%%%%%%%%%%%%% Teaching")
    cv=wire_input(cv,"pubs_teaching.tex","\\section{Teaching Experience, Training, and Awards}\n\\vspace{-0.5em}","\\subsubsection*{\\textit{Pedagogical Training}}")
    cv=wire_input(cv,"pubs_conferences.tex","(Wp)=Workshop Participant. %(S)=Section Chair.\n\\vspace{1em}","%%%%%%%%%%%%%%%%%%%%%%%%%%%% Certificates")
    cv=wire_input(cv,"pubs_briefs.tex","\\subsubsection*{\\textit{Non Peer-Reviewed Publications}}\n%%% Need to add this to reset the counter after sections\n\\setcounter{inprog}{1} ","\\input{pubs_other.tex}")
    open(P("cv","cv.tex"),"w").write(cv)

    print("OK  research:%d  invited:%d  conferences:%d  courses:%d  briefs:%d"
          %(len([e for e in pubs if e.get("show_on_research",True)]), len(pres["invited_talks"]), len(pres["conferences"]), len(teach), len(briefs)))
    print("cv.tex inputs:", [k for k in ["pubs_invited.tex","pubs_teaching.tex","pubs_conferences.tex","pubs_briefs.tex"] if "\\input{%s}"%k in cv])

if __name__ == "__main__":
    main()
