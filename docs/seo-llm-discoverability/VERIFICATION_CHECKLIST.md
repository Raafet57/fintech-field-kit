# Verification Checklist — SEO + LLM Discoverability Phase 1

Run after Replit AI implementation and deployment/preview. Use preview URL first, then production only after Raf approval.

Set target:

```bash
BASE="https://raafetchoukri.com"
# or Replit preview URL
```

## 1. Core crawl files

```bash
curl -I "$BASE/robots.txt"
curl -I "$BASE/sitemap.xml"
curl -I "$BASE/llms.txt"
curl -fsS "$BASE/llms.txt" | sed -n '1,80p'
```

Expected:
- robots.txt: 200 text/plain
- sitemap.xml: 200 XML
- llms.txt: 200 text/plain or text/markdown
- llms.txt begins with `# Raafet Choukri`, not `<!DOCTYPE html>`

## 2. Unknown route should not soft-404

```bash
curl -I "$BASE/definitely-not-a-real-page-20260522"
```

Expected: 404 or 410, not 200.

## 3. Raw route metadata/content sample

```bash
python3 - <<'PY'
import urllib.request, re
BASE='https://raafetchoukri.com'
paths=[
 '/',
 '/library',
 '/library/the-role-of-iso-20022',
 '/posts/vlei-auth-platform-launch',
 '/topics/iso20022',
 '/projects',
 '/projects/vlei-auth-platform',
 '/about',
 '/services',
]
for p in paths:
    url=BASE+p
    try:
        html=urllib.request.urlopen(url,timeout=20).read().decode('utf-8','replace')
    except Exception as e:
        print('
FAIL_FETCH',p,e); continue
    title=re.search(r'<title>(.*?)</title>',html,re.S|re.I)
    desc=re.search(r'<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)',html,re.S|re.I)
    canon=re.search(r'<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']*)',html,re.S|re.I)
    h1=bool(re.search(r'<h1[\s>]',html,re.I))
    ld=html.count('application/ld+json')
    shell_only=('<div id="root"></div>' in html and not h1 and ld==0)
    print('
PATH',p)
    print('title=',title.group(1).strip() if title else 'MISSING')
    print('desc=',desc.group(1).strip()[:180] if desc else 'MISSING')
    print('canonical=',canon.group(1).strip() if canon else 'MISSING')
    print('h1=',h1,'jsonld_count=',ld,'shell_only=',shell_only,'len=',len(html))
PY
```

Expected:
- each route has unique title/description/canonical
- representative routes have H1/content and JSON-LD
- `shell_only=False`

## 4. Check generic duplicate metadata is gone

```bash
python3 - <<'PY'
import urllib.request,re,collections
BASE='https://raafetchoukri.com'
paths=['/','/library','/posts/vlei-auth-platform-launch','/topics/iso20022','/projects/vlei-auth-platform']
titles=[]
for p in paths:
 html=urllib.request.urlopen(BASE+p,timeout=20).read().decode('utf-8','replace')
 m=re.search(r'<title>(.*?)</title>',html,re.S|re.I)
 titles.append((p,m.group(1).strip() if m else ''))
print('
'.join(f'{p}: {t}' for p,t in titles))
print('unique_titles',len(set(t for _,t in titles)),'of',len(titles))
PY
```

Expected: most/all sampled routes have distinct titles.

## 5. Validate JSON-LD parses

```bash
python3 - <<'PY'
import urllib.request,re,json
BASE='https://raafetchoukri.com'
paths=['/','/posts/vlei-auth-platform-launch','/library/the-role-of-iso-20022','/projects/vlei-auth-platform']
for p in paths:
 html=urllib.request.urlopen(BASE+p,timeout=20).read().decode('utf-8','replace')
 blocks=re.findall(r'<script[^>]+type=["']application/ld\+json["'][^>]*>(.*?)</script>',html,re.S|re.I)
 print('
PATH',p,'blocks',len(blocks))
 for i,b in enumerate(blocks):
  try:
   obj=json.loads(b.strip())
   print('  ok',i, obj.get('@type') if isinstance(obj,dict) else type(obj).__name__)
  except Exception as e:
   print('  JSON_ERROR',i,e)
PY
```

Expected: no JSON errors.

## 6. Claim-boundary checks

```bash
curl -fsS "$BASE/projects/vlei-auth-platform" | python3 - <<'PY'
import sys,re
html=sys.stdin.read().lower()
for phrase in ['reference demo','sanitized','not claim production readiness','live-vlei verification']:
 print(phrase, phrase in html)
PY
```

Expected: page includes clear reference-demo/sanitized/non-production boundary. Exact wording can differ, but boundary must be visible.

## 7. Robots policy check

```bash
curl -fsS "$BASE/robots.txt"
```

Expected for Phase 1: unchanged unless Raf explicitly approved crawler-policy change.

## Pass/fail summary

Phase 1 PASS requires:

- `/llms.txt` text file works.
- Unknown route no longer returns 200 shell.
- Representative route raw HTML has unique metadata and canonical.
- JSON-LD parses.
- vLEI project boundary preserved.
- Robots policy either unchanged or changed only with explicit Raf approval.
