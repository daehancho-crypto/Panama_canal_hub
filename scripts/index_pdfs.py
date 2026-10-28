#!/usr/bin/env python3
"""Bounded PDF text indexing. No AI, OCR, or paid API."""
import io,json,re,time,urllib.request
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlparse
from pypdf import PdfReader

SOURCE=Path("data/acp_documents.json")
OUT=Path("data/acp_pdf_index.json")
MAX_NEW=12
MAX_BYTES=8_000_000
MAX_PAGES=12
MAX_CHARS=16000
def download(url):
    host=urlparse(url).hostname or ""
    if not (host=="pancanal.com" or host.endswith(".pancanal.com")): raise ValueError("Unexpected host")
    req=urllib.request.Request(url,headers={"User-Agent":"PanamaCanalHub/1.0 (public document indexing)"})
    with urllib.request.urlopen(req,timeout=25) as r:
        if int(r.headers.get("Content-Length") or 0)>MAX_BYTES: raise ValueError("PDF too large")
        buf=bytearray()
        while True:
            block=r.read(65536)
            if not block: break
            buf.extend(block)
            if len(buf)>MAX_BYTES: raise ValueError("PDF exceeds size limit")
        if not bytes(buf).startswith(b"%PDF"): raise ValueError("Not a PDF")
        return bytes(buf)
def extract(url):
    reader=PdfReader(io.BytesIO(download(url)),strict=False)
    pages=[]
    for page in reader.pages[:MAX_PAGES]:
        pages.append(page.extract_text() or "")
    content=" ".join(" ".join(pages).split())[:MAX_CHARS]
    if not content: raise ValueError("No extractable text (possibly scanned PDF)")
    patterns=[r"(?i)effective (?:on|date|as of|from)\s*[:\-]?\s*([^.;\n]{5,85})",r"(?i)(?:shall|will) (?:become|take) effect\s*([^.;\n]{5,85})",r"(?i)effective immediately"]
    snippets=[]
    for pattern in patterns:
        for m in re.finditer(pattern,content):
            snippets.append(content[max(0,m.start()-70):min(len(content),m.end()+80)])
            if len(snippets)>=4:break
        if len(snippets)>=4:break
    return {"text":content,"effective_date_mentions":snippets,"pages_read":min(len(reader.pages),MAX_PAGES),"indexed_at":datetime.now(timezone.utc).isoformat(),"status":"indexed"}
def main():
    src=json.loads(SOURCE.read_text())
    old=json.loads(OUT.read_text()) if OUT.exists() else {}
    indexed=old.get("entries",{})
    docs=src.get("documents",[])
    # Newest years first, then newest first_seen; previously indexed documents stay cached.
    docs=sorted(docs,key=lambda d:(int((re.search(r"20\d{2}",d.get("title","")) or [0])[0]),d.get("first_seen","")),reverse=True)
    attempted=0
    for d in docs:
        url=d.get("url","")
        if not url or (url in indexed and indexed[url].get("status")=="indexed"):continue
        if attempted>=MAX_NEW:break
        attempted+=1
        try: indexed[url]=extract(url)
        except Exception as e: indexed[url]={"status":"error","error":str(e)[:140],"indexed_at":datetime.now(timezone.utc).isoformat()}
        print(attempted,indexed[url]["status"],d.get("title","")[:65])
        time.sleep(0.3)
    OUT.parent.mkdir(exist_ok=True,parents=True)
    OUT.write_text(json.dumps({"updated_at":datetime.now(timezone.utc).isoformat(),"limits":{"new_pdfs_per_run":MAX_NEW,"max_pages_per_pdf":MAX_PAGES},"entries":indexed},ensure_ascii=False,separators=(",",":"))+"\n")
    print("Index records:",len(indexed))
if __name__=="__main__":main()
