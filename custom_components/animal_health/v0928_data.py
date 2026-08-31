from __future__ import annotations
import json,re,secrets,sqlite3
from datetime import UTC,datetime
from pathlib import Path
from typing import Any
from . import v0924_features
from .v0913_features import medication_snapshot_for_name as legacy_medication_snapshot_for_name

DATABASE_SWISSMEDIC="swissmedic_ch"
DATABASE_DEWORMERS="swissmedic_dewormers"
DATABASE_VACCINES="vaccines_ch"
DATABASE_SUPPLEMENTS="animal_health_supplements"
DATABASE_FEEDS="animal_health_feed_chicken"
DATABASE_USER="user_curated"
PRODUCT_KINDS=("medication","vaccination","deworming","supplement","feed")
_DEWORM=re.compile(r"fluben|flubend|fenbend|praziquant|pyrantel|milbem|moxidect|ivermect|selamect|emodepsid|anthelm|entwurm|worm",re.I)
_VACC=re.compile(r"impfstoff|vaccin|vaccine|nobivac|nobilis|poulvac|purevax|bultavo|protivity",re.I)

def connect(path:Path)->sqlite3.Connection:
 c=sqlite3.connect(path);c.row_factory=sqlite3.Row;c.execute("PRAGMA foreign_keys=ON");c.execute("PRAGMA busy_timeout=5000");return c

def text(v:Any)->str:return re.sub(r"\s+"," ",str(v or "").strip())
def norm(v:Any)->str:return text(v).casefold()
def now()->str:return datetime.now(UTC).replace(microsecond=0).isoformat()
def loads(v:Any,fallback:Any):
 if isinstance(v,(dict,list)):return v
 try:return json.loads(str(v or ""))
 except (TypeError,ValueError,json.JSONDecodeError):return fallback

def table(c,name):return c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(name,)).fetchone() is not None
def cols(c,name):return {str(r[1]) for r in c.execute(f"PRAGMA table_info({name})")} if table(c,name) else set()

def seeds():
 return(
 (DATABASE_SWISSMEDIC,"Swissmedic – Tierarzneimittel","Offizielle Schweizer Quelle zugelassener Tierarzneimittel.",["medication","vaccination","deworming"],"Swissmedic","official",100,"automatic",1,1,""),
 (DATABASE_DEWORMERS,"Swissmedic – Entwurmungsmittel","Gefilterte Ansicht der Swissmedic-Tierarzneimittel für Entwurmungsmittel.",["deworming"],"Swissmedic","official",100,"automatic",1,1,DATABASE_SWISSMEDIC),
 (DATABASE_VACCINES,"Animal Health – Impfstoffe Schweiz","Mitgelieferter kuratierter Schweizer Impfstoffkatalog.",["vaccination"],"Animal Health / Swissmedic-Referenzen","curated",80,"bundled",1,1,""),
 (DATABASE_SUPPLEMENTS,"Animal Health – Ergänzungspräparate","Kuratierte Ergänzungspräparate mit mehreren aktiven Bestandteilen.",["supplement"],"Animal Health – Herstellerdaten","curated",80,"bundled",1,1,""),
 (DATABASE_FEEDS,"Animal Health – Futtermittel Geflügel","Kuratierte Futtermittel mit Nährwerten und Fütterungshinweisen.",["feed"],"Animal Health – Herstellerdaten","curated",80,"bundled",1,1,""),
 (DATABASE_USER,"Meine Produktdatenbank","Eigene kuratierte Produkte.",list(PRODUCT_KINDS),"Benutzerdefiniert","user",120,"manual",1,1,""),
 )

def initialize_product_databases_sync(path:Path)->None:
 stamp=now()
 with connect(path) as c:
  c.executescript("""CREATE TABLE IF NOT EXISTS v0928_product_databases(database_id TEXT PRIMARY KEY,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',product_types_json TEXT NOT NULL DEFAULT '[]',source_name TEXT NOT NULL DEFAULT '',source_type TEXT NOT NULL DEFAULT 'user',version TEXT NOT NULL DEFAULT '',data_as_of TEXT NOT NULL DEFAULT '',priority INTEGER NOT NULL DEFAULT 50,update_mode TEXT NOT NULL DEFAULT 'manual',license_notice TEXT NOT NULL DEFAULT '',source_url TEXT NOT NULL DEFAULT '',enabled INTEGER NOT NULL DEFAULT 1,is_system INTEGER NOT NULL DEFAULT 0,supports_local_overrides INTEGER NOT NULL DEFAULT 0,view_of TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,updated_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS v0928_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);""")
  for i in seeds():
   did,name,desc,kinds,source,stype,priority,mode,enabled,system,view=i
   c.execute("""INSERT INTO v0928_product_databases(database_id,name,description,product_types_json,source_name,source_type,priority,update_mode,enabled,is_system,supports_local_overrides,view_of,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(database_id) DO UPDATE SET name=excluded.name,description=excluded.description,product_types_json=excluded.product_types_json,source_name=excluded.source_name,source_type=excluded.source_type,priority=excluded.priority,update_mode=excluded.update_mode,is_system=excluded.is_system,supports_local_overrides=excluded.supports_local_overrides,view_of=excluded.view_of,updated_at=excluded.updated_at""",(did,name,desc,json.dumps(kinds),source,stype,priority,mode,enabled,system,0 if stype=="user" else 1,view,stamp,stamp))
  if table(c,"v0927_products"):
   if "database_id" not in cols(c,"v0927_products"):c.execute("ALTER TABLE v0927_products ADD COLUMN database_id TEXT")
   c.execute("UPDATE v0927_products SET database_id=CASE WHEN kind='vaccination' THEN ? WHEN kind='supplement' AND is_custom=0 THEN ? WHEN kind='feed' AND is_custom=0 THEN ? ELSE ? END WHERE database_id IS NULL OR database_id=''",(DATABASE_VACCINES,DATABASE_SUPPLEMENTS,DATABASE_FEEDS,DATABASE_USER))
  _seed_bundled(c,stamp);_migrate_manual(c,stamp);_sync_source_meta(c)

def _seed_bundled(c,stamp):
 if not table(c,"v0927_products"):return
 p=Path(__file__).with_name("catalogs")/"product_databases_0928.json"
 try:doc=json.loads(p.read_text(encoding="utf-8"))
 except (OSError,json.JSONDecodeError):return
 for db in doc.get("databases",[]):
  did=text(db.get("id"))
  for raw in db.get("products",[]):
   name=text(raw.get("name"));kind=text(raw.get("kind"));sid=text(raw.get("id"))
   if not name or kind not in PRODUCT_KINDS:continue
   pid=f"{did}:{sid}";species=list(raw.get("target_species") or []);meta={k:v for k,v in raw.items() if k not in {"id","kind","name","target_species"}}
   c.execute("""INSERT INTO v0927_products(id,kind,source,source_id,name,normalized_name,species_json,metadata_json,override_json,is_hidden,is_custom,created_at,updated_at,database_id) VALUES(?,?,?,?,?,?,?,?,?,0,0,?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,normalized_name=excluded.normalized_name,species_json=excluded.species_json,metadata_json=excluded.metadata_json,database_id=excluded.database_id,updated_at=excluded.updated_at""",(pid,kind,did,sid,name,norm(name),json.dumps(species,ensure_ascii=False),json.dumps(meta,ensure_ascii=False),"{}",stamp,stamp,did))

def _migrate_manual(c,stamp):
 marker=c.execute("SELECT value FROM v0928_meta WHERE key='legacy_manual_migrated'").fetchone()
 if marker or not table(c,"v0817_medications") or not table(c,"v0927_products"):return
 cc=cols(c,"v0817_medications")
 if not {"id","name"}<=cc:return
 for r in c.execute("SELECT * FROM v0817_medications").fetchall():
  name=text(r["name"]);pid=f"legacy-medication:{r['id']}";meta={"active_ingredient":text(r["active_ingredient"]) if "active_ingredient" in cc else "","concentration":text(r["concentration"]) if "concentration" in cc else "","dosage_form":text(r["dosage_form"]) if "dosage_form" in cc else "","default_unit":text(r["default_unit"]) if "default_unit" in cc else "dose","default_route":text(r["default_route"]) if "default_route" in cc else ""};species=[text(r["species_id"])] if "species_id" in cc and text(r["species_id"]) else []
  c.execute("""INSERT OR IGNORE INTO v0927_products(id,kind,source,source_id,name,normalized_name,species_json,metadata_json,override_json,is_hidden,is_custom,created_at,updated_at,database_id) VALUES(?,?,?,?,?,?,?,?,?,0,1,?,?,?)""",(pid,"medication",DATABASE_USER,pid,name,norm(name),json.dumps(species),json.dumps(meta),"{}",stamp,stamp,DATABASE_USER))
 c.execute("INSERT OR REPLACE INTO v0928_meta(key,value,updated_at) VALUES('legacy_manual_migrated','1',?)",(stamp,))

def _sync_source_meta(c):
 if table(c,"v0920_catalog_sources"):
  r=c.execute("SELECT snapshot_date FROM v0920_catalog_sources WHERE source_id=?",(DATABASE_SWISSMEDIC,)).fetchone()
  if r:c.execute("UPDATE v0928_product_databases SET data_as_of=?,updated_at=? WHERE database_id IN (?,?)",(text(r["snapshot_date"]),now(),DATABASE_SWISSMEDIC,DATABASE_DEWORMERS))

def classification(p):
 vals=list(p.get("classifications") or []);hay=" ".join(text(p.get(k)) for k in("name","active_ingredient","application_area","dosage_form"))
 if _DEWORM.search(hay):vals.append("deworming")
 if _VACC.search(hay):vals.append("vaccination")
 return list(dict.fromkeys(vals))

def local_products(c):
 if not table(c,"v0927_products"):return[]
 out=[]
 for r in c.execute("SELECT * FROM v0927_products ORDER BY normalized_name").fetchall():
  meta=loads(r["metadata_json"],{});over=loads(r["override_json"],{});did=text(r["database_id"]) if "database_id" in r.keys() else "";did=did or (DATABASE_VACCINES if r["kind"]=="vaccination" else DATABASE_SUPPLEMENTS if r["kind"]=="supplement" and not r["is_custom"] else DATABASE_FEEDS if r["kind"]=="feed" and not r["is_custom"] else DATABASE_USER)
  base={"id":str(r["id"]),"database_id":did,"kind":str(r["kind"]),"name":str(r["name"]),"target_species":loads(r["species_json"],[]),**(meta if isinstance(meta,dict) else {})};item={**base,**(over if isinstance(over,dict) else {})};item.update(is_hidden=bool(r["is_hidden"]),is_custom=bool(r["is_custom"]),is_modified=bool(over),original=base);item["classifications"]=classification(item);out.append(item)
 return out

def swiss_products(path):
 try:items=v0924_features._catalog_state_sync(path)
 except Exception:return[]
 out=[]
 for raw in items:
  item={**raw,"id":f"{DATABASE_SWISSMEDIC}:{raw.get('id')}","catalog_item_id":raw.get("id"),"database_id":DATABASE_SWISSMEDIC,"kind":"medication","is_custom":False};item["classifications"]=classification(item);out.append(item)
 return out

def state_sync(path:Path)->dict[str,Any]:
 with connect(path) as c:
  _sync_source_meta(c);products=local_products(c);dbrows=c.execute("SELECT * FROM v0928_product_databases ORDER BY priority DESC,name COLLATE NOCASE").fetchall()
 products+=swiss_products(path);counts={};mods={}
 for p in products:
  did=p["database_id"];counts[did]=counts.get(did,0)+1;mods[did]=mods.get(did,0)+int(bool(p.get("is_modified") or p.get("is_hidden")))
 counts[DATABASE_DEWORMERS]=sum(1 for p in products if p["database_id"]==DATABASE_SWISSMEDIC and "deworming" in p.get("classifications",[]))
 dbs=[]
 for r in dbrows:
  dbs.append({"id":r["database_id"],"name":r["name"],"description":r["description"],"product_types":loads(r["product_types_json"],[]),"source_name":r["source_name"],"source_type":r["source_type"],"version":r["version"],"data_as_of":r["data_as_of"],"priority":r["priority"],"update_mode":r["update_mode"],"license_notice":r["license_notice"],"source_url":r["source_url"],"enabled":bool(r["enabled"]),"is_system":bool(r["is_system"]),"supports_local_overrides":bool(r["supports_local_overrides"]),"view_of":r["view_of"],"item_count":counts.get(r["database_id"],0),"modified_count":mods.get(r["database_id"],0)})
 enabled={d["id"]:d for d in dbs if d["enabled"]};ordered=sorted((p for p in products if p["database_id"] in enabled),key=lambda p:(-int(enabled[p["database_id"]]["priority"]),p["name"].casefold()));merged=[];seen=set()
 for p in ordered:
  key=(text(p.get("authorisation_number")) or re.sub(r"[^a-z0-9äöüß]+"," ",norm(p["name"]))).casefold()
  if key in seen:continue
  seen.add(key);merged.append(p)
 return{"databases":dbs,"products":products,"merged_products":merged,"views":{"deworming_database_id":DATABASE_DEWORMERS,"swissmedic_database_id":DATABASE_SWISSMEDIC}}

def dbrow(c,did):
 r=c.execute("SELECT * FROM v0928_product_databases WHERE database_id=?",(did,)).fetchone()
 if not r:raise KeyError(did)
 return r

def save_database_sync(path,payload):
 did=text(payload.get("database_id"));fields=dict(payload.get("fields") or {});name=text(payload.get("name") or fields.get("name"));kinds=[x for x in(payload.get("product_types") or fields.get("product_types") or PRODUCT_KINDS) if x in PRODUCT_KINDS]
 if not name:raise ValueError("Database name is required")
 stamp=now()
 with connect(path) as c:
  if did and dbrow(c,did)["is_system"]:raise ValueError("System databases cannot be structurally edited")
  did=did or f"custom_{secrets.token_hex(6)}"
  c.execute("""INSERT INTO v0928_product_databases(database_id,name,description,product_types_json,source_name,source_type,version,data_as_of,priority,update_mode,license_notice,source_url,enabled,is_system,supports_local_overrides,view_of,created_at,updated_at) VALUES(?,?,?,?,?,'user',?,?,?,'manual',?,?,1,0,0,'',?,?) ON CONFLICT(database_id) DO UPDATE SET name=excluded.name,description=excluded.description,product_types_json=excluded.product_types_json,source_name=excluded.source_name,version=excluded.version,data_as_of=excluded.data_as_of,priority=excluded.priority,license_notice=excluded.license_notice,source_url=excluded.source_url,updated_at=excluded.updated_at""",(did,name,text(fields.get("description")),json.dumps(kinds),text(fields.get("source_name") or "Benutzerdefiniert"),text(fields.get("version") or "1"),text(fields.get("data_as_of")),int(fields.get("priority") or 50),text(fields.get("license_notice")),text(fields.get("source_url")),stamp,stamp))
 return next(d for d in state_sync(path)["databases"] if d["id"]==did)

def toggle_database_sync(path,did,enabled):
 with connect(path) as c:dbrow(c,did);c.execute("UPDATE v0928_product_databases SET enabled=?,updated_at=? WHERE database_id=?",(int(enabled),now(),did))
 return next(d for d in state_sync(path)["databases"] if d["id"]==did)

def delete_database_sync(path,did):
 with connect(path) as c:
  if dbrow(c,did)["is_system"]:raise ValueError("System databases cannot be deleted")
  c.execute("DELETE FROM v0927_products WHERE database_id=?",(did,));c.execute("DELETE FROM v0928_product_databases WHERE database_id=?",(did,))

def save_product_sync(path,payload):
 kind=text(payload.get("kind"));did=text(payload.get("database_id")) or DATABASE_USER;pid=text(payload.get("item_id"));fields=dict(payload.get("fields") or {});name=text(fields.get("name") or payload.get("name"));species=fields.pop("target_species",payload.get("target_species") or []);species=[text(x) for x in(species if isinstance(species,list) else [species]) if text(x)]
 if kind not in PRODUCT_KINDS or not name:raise ValueError("Valid product kind and name are required")
 if pid.startswith(DATABASE_SWISSMEDIC+":"):
  rawid=pid.split(":",1)[1];allowed={k:v for k,v in fields.items() if k in {"name","active_ingredient","active_ingredients","active_ingredient_details","concentration","dosage_form","target_species","aliases","default_route"}};allowed.update(name=name,target_species=species);v0924_features._save_catalog_override_sync(path,DATABASE_SWISSMEDIC,rawid,False,allowed)
  return next(p for p in state_sync(path)["products"] if p["id"]==pid)
 stamp=now()
 with connect(path) as c:
  if pid:
   r=c.execute("SELECT * FROM v0927_products WHERE id=?",(pid,)).fetchone()
   if not r:raise KeyError(pid)
   if r["is_custom"]:
    meta=loads(r["metadata_json"],{});meta.update({k:v for k,v in fields.items() if k not in {"name","target_species"}});c.execute("UPDATE v0927_products SET kind=?,name=?,normalized_name=?,species_json=?,metadata_json=?,database_id=?,updated_at=? WHERE id=?",(kind,name,norm(name),json.dumps(species),json.dumps(meta,ensure_ascii=False),did,stamp,pid))
   else:
    over={**fields,"name":name,"target_species":species};c.execute("UPDATE v0927_products SET override_json=?,updated_at=? WHERE id=?",(json.dumps(over,ensure_ascii=False),stamp,pid))
  else:
   if dbrow(c,did)["source_type"]!="user":raise ValueError("New products can only be added to a user database")
   pid=f"custom:{did}:{secrets.token_hex(8)}";meta={k:v for k,v in fields.items() if k not in {"name","target_species"}};c.execute("INSERT INTO v0927_products(id,kind,source,source_id,name,normalized_name,species_json,metadata_json,override_json,is_hidden,is_custom,created_at,updated_at,database_id) VALUES(?,?,?,?,?,?,?,?,?,0,1,?,?,?)",(pid,kind,did,pid,name,norm(name),json.dumps(species),json.dumps(meta,ensure_ascii=False),"{}",stamp,stamp,did))
 return next(p for p in state_sync(path)["products"] if p["id"]==pid)

def archive_product_sync(path,pid,hidden):
 if pid.startswith(DATABASE_SWISSMEDIC+":"):
  rawid=pid.split(":",1)[1];v0924_features._save_catalog_override_sync(path,DATABASE_SWISSMEDIC,rawid,bool(hidden),{})
 else:
  with connect(path) as c:
   if not c.execute("UPDATE v0927_products SET is_hidden=?,updated_at=? WHERE id=?",(int(hidden),now(),pid)).rowcount:raise KeyError(pid)
 return next(p for p in state_sync(path)["products"] if p["id"]==pid)

def reset_product_sync(path,pid):
 if pid.startswith(DATABASE_SWISSMEDIC+":"):
  rawid=pid.split(":",1)[1];v0924_features._reset_catalog_override_sync(path,DATABASE_SWISSMEDIC,rawid)
 else:
  with connect(path) as c:
   r=c.execute("SELECT is_custom FROM v0927_products WHERE id=?",(pid,)).fetchone()
   if not r:raise KeyError(pid)
   if r["is_custom"]:raise ValueError("Custom products have no source version")
   c.execute("UPDATE v0927_products SET override_json='{}',is_hidden=0,updated_at=? WHERE id=?",(now(),pid))
 return next(p for p in state_sync(path)["products"] if p["id"]==pid)

def delete_product_sync(path,pid):
 with connect(path) as c:
  r=c.execute("SELECT is_custom FROM v0927_products WHERE id=?",(pid,)).fetchone()
  if not r or not r["is_custom"]:raise ValueError("Only custom products can be deleted")
  c.execute("DELETE FROM v0927_products WHERE id=?",(pid,))

def import_database_sync(path,payload):
 doc=payload.get("document")
 if not isinstance(doc,dict):raise ValueError("Invalid import document")
 meta=doc.get("database") or {};db=save_database_sync(path,{"name":text(meta.get("name")) or "Importierte Produktdatenbank","product_types":meta.get("product_types") or PRODUCT_KINDS,"fields":meta});ok=bad=0
 for raw in doc.get("products") or []:
  if not isinstance(raw,dict) or raw.get("kind") not in PRODUCT_KINDS or not text(raw.get("name")):bad+=1;continue
  fields={k:v for k,v in raw.items() if k not in {"id","database_id","is_hidden","is_custom","is_modified","original"}};save_product_sync(path,{"database_id":db["id"],"kind":raw["kind"],"name":raw["name"],"target_species":raw.get("target_species") or [],"fields":fields});ok+=1
 return{"database":next(d for d in state_sync(path)["databases"] if d["id"]==db["id"]),"imported":ok,"invalid":bad}

def load_product_snapshot(c,pid):
 if not pid:return None
 if pid.startswith(DATABASE_SWISSMEDIC+":"):
  rawid=pid.split(":",1)[1];dbpath=Path(c.execute('PRAGMA database_list').fetchone()[2]);item=next((x for x in v0924_features._catalog_state_sync(dbpath) if str(x.get('id'))==rawid),None)
  return {**item,"id":pid,"database_id":DATABASE_SWISSMEDIC} if item else None
 if not table(c,"v0927_products"):return None
 r=c.execute("SELECT * FROM v0927_products WHERE id=?",(pid,)).fetchone()
 if not r:return None
 meta=loads(r["metadata_json"],{});over=loads(r["override_json"],{});return{"id":pid,"database_id":text(r["database_id"]) if "database_id" in r.keys() else text(r["source"]),"kind":r["kind"],"name":r["name"],"target_species":loads(r["species_json"],[]),**meta,**over}

def medication_snapshot_for_name(c,product_name):
 needle=norm(product_name)
 if table(c,"v0927_products"):
  r=c.execute("SELECT id FROM v0927_products WHERE normalized_name=? AND kind IN ('medication','deworming') ORDER BY is_custom DESC,id LIMIT 1",(needle,)).fetchone()
  if r:
   s=load_product_snapshot(c,str(r["id"]));return{"source":s.get("database_id"),"catalog_id":s.get("id"),"product_name":s.get("name"),**{k:s.get(k) for k in("active_ingredient","active_ingredients","active_ingredient_details","concentration","dosage_form","default_route") if s.get(k) not in(None,"",[])}}
 return legacy_medication_snapshot_for_name(c,product_name)
