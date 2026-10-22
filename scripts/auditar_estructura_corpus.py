#!/usr/bin/env python3
"""Cruza la auditoría visual del PDF con el corpus Markdown candidato."""

from __future__ import annotations
import argparse, json, re, unicodedata
from collections import defaultdict
from pathlib import Path

STOP={"de","la","el","los","las","un","una","y","o","a","en","del","al","por","para","con","the","of","and","or","to","in","a","an","on","for","with"}

def norm_tokens(s:str)->list[str]:
    s=unicodedata.normalize("NFKC",s).lower()
    s=re.sub(r"[^\wáéíóúüñ]+"," ",s,flags=re.UNICODE)
    return [x for x in s.split() if len(x)>=2 and x not in STOP]

def strip_md(s:str)->str:
    s=re.sub(r"^---\n[\s\S]*?\n---\n","",s)
    s=re.sub(r"!\[[^\]]*\]\([^)]*\)"," ",s)
    s=re.sub(r"\[([^\]]+)\]\([^)]*\)",r"\1",s)
    s=re.sub(r"\[\[([^\]|]+\|)?([^\]]+)\]\]",r"\2",s)
    s=re.sub(r"[#*_>~|]"," ",s)
    return s

def heading(s:str,fallback:str)->str:
    for line in s.splitlines():
        m=re.match(r"^#{1,6}\s+(.+?)\s*$",line)
        if m:return re.sub(r"[*_]","",m.group(1)).strip()
    return fallback

def grams(ts:list[str],n:int=4):
    return {tuple(ts[i:i+n]) for i in range(max(0,len(ts)-n+1))}

class Indice:
    def __init__(self,root:Path):
        self.root=root
        self.docs={}
        self.inv4=defaultdict(set)
        self.invtok=defaultdict(set)
        for p in sorted(root.rglob("*.md")):
            raw=p.read_text(encoding="utf-8")
            rel=str(p.relative_to(root))
            ts=norm_tokens(strip_md(raw))
            g4=grams(ts,4)
            toks={x for x in ts if len(x)>=3}
            self.docs[rel]={"titulo":heading(raw,p.stem),"g4":g4,"tokens":toks}
            for g in g4:self.inv4[g].add(rel)
            for t in toks:self.invtok[t].add(rel)

    def match_text(self,texto:str):
        ts=norm_tokens(texto)
        gs=grams(ts,4)
        scores=defaultdict(int)
        for g in gs:
            for f in self.inv4.get(g,()):scores[f]+=1
        denom=max(1,len(gs))
        ranked=sorted(((n/denom,f,n) for f,n in scores.items()),reverse=True)[:5]
        return [{"archivo":f,"score":round(sc,5),"coincidencias":n,"titulo":self.docs[f]["titulo"]} for sc,f,n in ranked]

    def match_tokens(self,texto:str):
        toks={x for x in norm_tokens(texto) if len(x)>=3}
        scores=defaultdict(int)
        for t in toks:
            for f in self.invtok.get(t,()):scores[f]+=1
        denom=max(1,len(toks))
        ranked=sorted(((n/denom,f,n) for f,n in scores.items()),reverse=True)[:5]
        return [{"archivo":f,"score":round(sc,5),"coincidencias":n,"titulo":self.docs[f]["titulo"]} for sc,f,n in ranked]

def flat_table(t:dict)->str:
    partes=[]
    if t.get("contexto_superior"):partes.append(t["contexto_superior"])
    for row in t.get("datos",[]):
        for c in row:
            if c:partes.append(str(c))
    return " ".join(partes)

def auditar_idioma(audit:dict,idx:Indice)->dict:
    callouts=[]
    for c in audit.get("callouts",[]):
        matches=idx.match_text(c.get("texto",""))
        best=matches[0] if matches else None
        score=best["score"] if best else 0
        if score>=0.60:
            tipo="localizado"
        elif score>=0.30:
            tipo="parcial"
        else:
            tipo="no_localizado"
        propio=False
        if best:
            propio=norm_tokens(c.get("titulo_candidato",""))==norm_tokens(best["titulo"])
        callouts.append({
            "pagina":c["pagina"],"titulo":c.get("titulo_candidato",""),
            "bbox":c["bbox"],"estado":tipo,"archivo_propio":propio,
            "mejores":matches[:3],
        })

    tablas=[]; por_id={}
    for t in audit.get("tablas",[]):
        matches=idx.match_tokens(flat_table(t))
        row={
            "id_local":t["id_local"],"pagina":t["pagina"],
            "filas":t["filas"],"columnas":t["columnas"],
            "contexto_superior":t.get("contexto_superior",""),
            "mejores":matches[:3],
        }
        tablas.append(row); por_id[t["id_local"]]=row

    continuaciones=[]
    for x in audit.get("continuaciones_tabla",[]):
        a=por_id.get(x.get("tabla_origen"))
        archivo_a=a["mejores"][0]["archivo"] if a and a["mejores"] else None
        archivo_b=None; match_b=[]
        if x["tipo"]=="tabla_a_tabla":
            b=por_id.get(x.get("tabla_destino"))
            if b and b["mejores"]:
                archivo_b=b["mejores"][0]["archivo"]; match_b=b["mejores"][:3]
        else:
            match_b=idx.match_tokens(" ".join(x.get("muestra_inicio",[])))
            archivo_b=match_b[0]["archivo"] if match_b else None
        estado="mismo_archivo" if archivo_a and archivo_a==archivo_b else "revisar"
        continuaciones.append({
            **x,
            "archivo_origen":archivo_a,
            "archivo_destino":archivo_b,
            "estado_corpus":estado,
            "matches_destino":match_b,
        })

    return {
      "callouts":callouts,
      "resumen_callouts":{
        "total":len(callouts),
        "localizados":sum(x["estado"]=="localizado" for x in callouts),
        "parciales":sum(x["estado"]=="parcial" for x in callouts),
        "no_localizados":sum(x["estado"]=="no_localizado" for x in callouts),
        "archivo_propio":sum(x["archivo_propio"] for x in callouts),
      },
      "tablas":tablas,
      "continuaciones":continuaciones,
      "continuaciones_a_revisar":[x for x in continuaciones if x["estado_corpus"]!="mismo_archivo"],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--auditoria",type=Path,required=True)
    ap.add_argument("--corpus",type=Path,required=True)
    ap.add_argument("--salida",type=Path,required=True)
    a=ap.parse_args()
    audit=json.loads(a.auditoria.read_text(encoding="utf-8"))
    out={}
    for lang in ("es","en"):
        out[lang]=auditar_idioma(audit[lang],Indice(a.corpus/lang))
    a.salida.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for lang in ("es","en"):
        print(lang,out[lang]["resumen_callouts"],"continuaciones revisar",len(out[lang]["continuaciones_a_revisar"]))
    return 0
if __name__=="__main__":raise SystemExit(main())
