My personal website to advertise myself and keep track of all my work. This was forked (then detached) by [Stuart Geiger](https://github.com/staeiou) from the [Minimal Mistakes Jekyll Theme](https://mmistakes.github.io/minimal-mistakes/), which is © 2016 Michael Rose and released under the MIT License. See LICENSE.md.

## How to update content

The website and the CV share one source of truth. Everything below lives in `_data/*.yml`. Edit the YAML, commit, and push (from GitHub Desktop). The CV Action (`.github/workflows/build-cv.yml`) runs `scripts/build_from_data.py` to regenerate the page sections and the CV fragments, then recompiles `files/cv_kunkel.pdf`. 

Single sources:

- `_data/publications.yml` — Research cards (`_pages/research.md`) + CV `cv/pubs_papers.tex` and `cv/pubs_other.tex`
- `_data/presentations.yml` — Presentations page (`_pages/presentations.md`) + CV `cv/pubs_invited.tex` and `cv/pubs_conferences.tex`
- `_data/teaching.yml` — Teaching "Courses" (`_pages/teaching.md`) + CV `cv/pubs_teaching.tex`
- `_data/briefs.yml` — Policy briefs (`_pages/policy.md`) + CV `cv/pubs_briefs.tex`

The order of entries in each YAML is the order shown on both the website and the CV. The generated page sections are wrapped in `<!-- BUILD:name -->` markers and replaced in place, and `cv/cv.tex` already `\input`s each fragment, so the build is idempotent (running it twice changes nothing).
