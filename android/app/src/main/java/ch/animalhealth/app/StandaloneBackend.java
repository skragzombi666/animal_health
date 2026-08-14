package ch.animalhealth.app;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.util.Base64;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

public final class StandaloneBackend extends SQLiteOpenHelper {
    public static final String VERSION = "0.9.0-alpha.2";
    private static final String DB_NAME = "animal_health_android.db";
    private static final int DB_VERSION = 2;
    private final Context context;

    public StandaloneBackend(Context context) {
        super(context, DB_NAME, null, DB_VERSION);
        this.context = context.getApplicationContext();
    }

    @Override
    public void onConfigure(SQLiteDatabase db) {
        super.onConfigure(db);
        db.setForeignKeyConstraintsEnabled(true);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE animals (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,species TEXT NOT NULL,breed TEXT,color TEXT,sex TEXT,birth_date TEXT,arrival_date TEXT,status TEXT NOT NULL DEFAULT 'active',is_archived INTEGER NOT NULL DEFAULT 0,distinctive_features TEXT,created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE groups (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE COLLATE NOCASE,species TEXT,description TEXT,is_archived INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE animal_group_memberships (animal_id INTEGER PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL)");
        db.execSQL("CREATE TABLE tags (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE COLLATE NOCASE,description TEXT,created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE animal_tag_memberships (animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,PRIMARY KEY(animal_id,tag_id))");
        db.execSQL("CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT,animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,type TEXT NOT NULL,occurred_at INTEGER NOT NULL,title TEXT NOT NULL,notes TEXT,value REAL,unit TEXT,medication_name TEXT,route TEXT,correction_of_id INTEGER REFERENCES events(id),batch_id TEXT,data_json TEXT NOT NULL DEFAULT '{}',created_at INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX idx_events_animal_time ON events(animal_id,occurred_at DESC)");
        db.execSQL("CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT,animal_id INTEGER REFERENCES animals(id) ON DELETE CASCADE,group_id INTEGER REFERENCES groups(id) ON DELETE CASCADE,title TEXT NOT NULL,description TEXT,due_at INTEGER NOT NULL,kind TEXT NOT NULL DEFAULT 'reminder',done INTEGER NOT NULL DEFAULT 0,recurrence_type TEXT NOT NULL DEFAULT 'once',recurrence_interval INTEGER NOT NULL DEFAULT 1,start_date TEXT,end_date TEXT,due_time TEXT,is_active INTEGER NOT NULL DEFAULT 1,planned_json TEXT NOT NULL DEFAULT '{}',created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE occurrences (id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,scheduled_at INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',completed_at INTEGER,notes TEXT,actual_json TEXT NOT NULL DEFAULT '{}',UNIQUE(task_id,scheduled_at))");
        db.execSQL("CREATE TABLE medications (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE COLLATE NOCASE,species TEXT,default_unit TEXT,default_route TEXT,created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE attachments (id INTEGER PRIMARY KEY AUTOINCREMENT,animal_id INTEGER REFERENCES animals(id) ON DELETE CASCADE,event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,filename TEXT NOT NULL,media_type TEXT NOT NULL,title TEXT,size_bytes INTEGER NOT NULL,content BLOB NOT NULL,created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE profiles (animal_id INTEGER PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,attachment_id INTEGER REFERENCES attachments(id) ON DELETE SET NULL)");
        db.execSQL("CREATE TABLE group_events (id INTEGER PRIMARY KEY AUTOINCREMENT,group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,event_type TEXT NOT NULL,occurred_at INTEGER NOT NULL,title TEXT NOT NULL,notes TEXT,value REAL,unit TEXT,data_json TEXT NOT NULL DEFAULT '{}',created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE settings (key TEXT PRIMARY KEY,value TEXT)");
        db.execSQL("CREATE TABLE custom_values (id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,species_id TEXT NOT NULL DEFAULT '',breed_context TEXT NOT NULL DEFAULT '',value TEXT NOT NULL,UNIQUE(kind,species_id,breed_context,value COLLATE NOCASE))");
        db.execSQL("CREATE TABLE group_metadata (group_id INTEGER PRIMARY KEY REFERENCES groups(id) ON DELETE CASCADE,breed TEXT)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
        if (oldVersion < 2) {
            addColumn(db, "animals", "birth_date TEXT");
            addColumn(db, "animals", "arrival_date TEXT");
            addColumn(db, "animals", "status TEXT NOT NULL DEFAULT 'active'");
            addColumn(db, "animals", "is_archived INTEGER NOT NULL DEFAULT 0");
            addColumn(db, "animals", "distinctive_features TEXT");
            addColumn(db, "events", "data_json TEXT NOT NULL DEFAULT '{}'");
            addColumn(db, "tasks", "group_id INTEGER");
            addColumn(db, "tasks", "description TEXT");
            addColumn(db, "tasks", "recurrence_type TEXT NOT NULL DEFAULT 'once'");
            addColumn(db, "tasks", "recurrence_interval INTEGER NOT NULL DEFAULT 1");
            addColumn(db, "tasks", "start_date TEXT");
            addColumn(db, "tasks", "end_date TEXT");
            addColumn(db, "tasks", "due_time TEXT");
            addColumn(db, "tasks", "is_active INTEGER NOT NULL DEFAULT 1");
            addColumn(db, "tasks", "planned_json TEXT NOT NULL DEFAULT '{}'");
            db.execSQL("CREATE TABLE IF NOT EXISTS groups (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE COLLATE NOCASE,species TEXT,description TEXT,is_archived INTEGER NOT NULL DEFAULT 0,created_at INTEGER NOT NULL)");
            db.execSQL("CREATE TABLE IF NOT EXISTS animal_group_memberships (animal_id INTEGER PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,group_id INTEGER REFERENCES groups(id) ON DELETE SET NULL)");
            db.execSQL("CREATE TABLE IF NOT EXISTS tags (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE COLLATE NOCASE,description TEXT,created_at INTEGER NOT NULL)");
            db.execSQL("CREATE TABLE IF NOT EXISTS animal_tag_memberships (animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,PRIMARY KEY(animal_id,tag_id))");
            db.execSQL("CREATE TABLE IF NOT EXISTS occurrences (id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,scheduled_at INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',completed_at INTEGER,notes TEXT,actual_json TEXT NOT NULL DEFAULT '{}',UNIQUE(task_id,scheduled_at))");
            db.execSQL("CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY AUTOINCREMENT,animal_id INTEGER REFERENCES animals(id) ON DELETE CASCADE,event_id INTEGER REFERENCES events(id) ON DELETE CASCADE,filename TEXT NOT NULL,media_type TEXT NOT NULL,title TEXT,size_bytes INTEGER NOT NULL,content BLOB NOT NULL,created_at INTEGER NOT NULL)");
            db.execSQL("CREATE TABLE IF NOT EXISTS profiles (animal_id INTEGER PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,attachment_id INTEGER REFERENCES attachments(id) ON DELETE SET NULL)");
            db.execSQL("CREATE TABLE IF NOT EXISTS group_events (id INTEGER PRIMARY KEY AUTOINCREMENT,group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,event_type TEXT NOT NULL,occurred_at INTEGER NOT NULL,title TEXT NOT NULL,notes TEXT,value REAL,unit TEXT,data_json TEXT NOT NULL DEFAULT '{}',created_at INTEGER NOT NULL)");
            db.execSQL("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT)");
            db.execSQL("CREATE TABLE IF NOT EXISTS custom_values (id INTEGER PRIMARY KEY AUTOINCREMENT,kind TEXT NOT NULL,species_id TEXT NOT NULL DEFAULT '',breed_context TEXT NOT NULL DEFAULT '',value TEXT NOT NULL,UNIQUE(kind,species_id,breed_context,value COLLATE NOCASE))");
            db.execSQL("CREATE TABLE IF NOT EXISTS group_metadata (group_id INTEGER PRIMARY KEY REFERENCES groups(id) ON DELETE CASCADE,breed TEXT)");
            try { db.execSQL("UPDATE tasks SET start_date=date(due_at/1000,'unixepoch','localtime') WHERE start_date IS NULL"); } catch (Exception ignored) {}
        }
    }

    private static void addColumn(SQLiteDatabase db, String table, String column) {
        try { db.execSQL("ALTER TABLE " + table + " ADD COLUMN " + column); } catch (Exception ignored) {}
    }

    public synchronized String handle(String raw) {
        try {
            JSONObject msg = new JSONObject(raw == null ? "{}" : raw);
            Object result = dispatch(msg);
            return result == null ? "{}" : result.toString();
        } catch (Exception error) {
            try { return new JSONObject().put("__error", String.valueOf(error.getMessage() == null ? error : error.getMessage())).toString(); }
            catch (JSONException ignored) { return "{\"__error\":\"Unknown error\"}"; }
        }
    }

    private Object dispatch(JSONObject msg) throws Exception {
        String type = msg.optString("type", "");
        switch (type) {
            case "animal_health/dashboard": return dashboard();
            case "animal_health/catalog": return catalog();
            case "animal_health/features": return features();
            case "animal_health/animal_detail": return animalDetail(msg.getString("animal_id"));
            case "call_service": return callService(msg.optString("service"), msg.optJSONObject("service_data") == null ? new JSONObject() : msg.optJSONObject("service_data"));
            case "animal_health/groups/create": return createGroup(msg);
            case "animal_health/groups/update": return updateGroup(msg);
            case "animal_health/groups/delete": return deleteGroup(msg);
            case "animal_health/animal_group/set": return setAnimalGroup(msg);
            case "animal_health/attachments/list": return attachmentList(msg);
            case "animal_health/attachments/delete": return deleteAttachment(msg);
            case "animal_health/attachments/upload_direct": return uploadDirect(msg);
            case "animal_health/download": return new JSONObject().put("url", "https://app.local/export/" + msg.optString("kind") + "/" + msg.optString("resource_id"));
            case "animal_health/v080/state": return v080State();
            case "animal_health/tags/create": return createTag(msg);
            case "animal_health/tags/update": return updateTag(msg);
            case "animal_health/tags/delete": return deleteTag(msg);
            case "animal_health/tags/set": return setTags(msg);
            case "animal_health/animal_photo/set": return setPhoto(msg);
            case "animal_health/animal_photo/remove": return removePhoto(msg);
            case "animal_health/v082/attachment/preview": return previewAttachment(msg);
            case "animal_health/v081/state": return v081State();
            case "animal_health/v081/settings/update": return updateV081Settings(msg);
            case "animal_health/v081/product/record": return recordProduct(msg);
            case "animal_health/v081/weight/correct": return correctWeight(msg);
            case "animal_health/v081/group_event/create":
            case "animal_health/v081/group_event/create_safe": return createGroupEvent(msg);
            case "animal_health/v081/group_task/create": return createGroupTask(msg);
            case "animal_health/v081/group_task/execute": return executeGroupTask(msg);
            case "animal_health/v081/group_pdf": return new JSONObject().put("url", "https://app.local/export/group_pdf/" + msg.optString("group_id"));
            case "animal_health/v083/state": return v083State();
            case "animal_health/v083/animal_metadata/set": return setAnimalMetadata(msg);
            case "animal_health/v083/group_metadata/set": return setGroupMetadata(msg);
            case "animal_health/v083/custom_value/remember": return rememberCustom(msg);
            case "animal_health/v084/history_suggestions": return historySuggestions();
            case "animal_health/v084/diagnostics": return diagnostics();
            case "animal_health/v084/reset_activity": return resetActivity();
            case "animal_health/v0817/state": return v0817State();
            case "animal_health/v0817/settings/update": return update0817Settings(msg);
            case "animal_health/v0817/medications/record": return recordMedicationPreset(msg);
            case "animal_health/v0817/medications/delete": return deleteMedicationPreset(msg);
            case "animal_health/v0817/medications/batch_record": return recordMedicationBatch(msg);
            case "animal_health/ai/status": return aiStatus();
            case "animal_health/ai/upload_direct": return new JSONObject().put("upload_id", "android-local").put("filename", msg.optString("filename"));
            case "animal_health/v084/reset_all": return resetAll();
            default:
                if (type.contains("/ai/analyze") || type.endsWith("/transcribe")) throw new IllegalStateException("Für KI-Erfassung muss in der Standalone-App zuerst ein KI-Provider konfiguriert werden.");
                return new JSONObject();
        }
    }

    private JSONObject callService(String service, JSONObject p) throws Exception {
        switch (service) {
            case "create_animal": return serviceCreateAnimal(p);
            case "update_animal": return serviceUpdateAnimal(p);
            case "archive_animal": return serviceArchiveAnimal(p, true);
            case "restore_animal": return serviceArchiveAnimal(p, false);
            case "set_animal_status": return serviceStatus(p);
            case "record_weight": return serviceWeight(p);
            case "create_event": return serviceEvent(p);
            case "record_symptom": return serviceSymptom(p);
            case "create_record_task": return serviceCreateTask(p);
            case "set_task_active": return serviceTaskActive(p);
            case "record_task_reminder":
            case "record_task_weight":
            case "record_task_medication":
            case "record_task_vaccination":
            case "record_task_health_check":
            case "record_task_care":
            case "record_task_veterinary_visit": return serviceExecuteOccurrence(service, p);
            case "skip_task_occurrence": return resolveOccurrence(p, "skipped");
            case "cancel_task_occurrence": return resolveOccurrence(p, "cancelled");
            default: return new JSONObject().put("service", service).put("ok", true);
        }
    }

    private JSONObject dashboard() throws Exception {
        SQLiteDatabase db = getWritableDatabase();
        ensureOccurrences(db);
        JSONArray animals = animalsJson(db);
        JSONArray tasks = tasksJson(db, null);
        JSONArray occurrences = occurrencesJson(db, null);
        JSONArray events = eventsJson(db, null, 250);
        LocalDate today = LocalDate.now();
        int active = 0, archived = 0, pending = 0, overdue = 0, todayCount = 0, upcoming = 0;
        for (int i = 0; i < animals.length(); i++) {
            JSONObject a = animals.getJSONObject(i);
            if (a.optBoolean("is_archived")) archived++; else if ("active".equals(a.optString("status"))) active++;
        }
        for (int i = 0; i < occurrences.length(); i++) {
            JSONObject o = occurrences.getJSONObject(i);
            if (!"pending".equals(o.optString("status"))) continue;
            pending++;
            if (o.optBoolean("is_overdue")) overdue++;
            if (o.optBoolean("is_today")) todayCount++;
            if (o.optBoolean("is_upcoming")) upcoming++;
        }
        JSONObject summary = new JSONObject().put("active_animals", active).put("archived_animals", archived).put("pending_tasks", pending).put("overdue_tasks", overdue).put("today_tasks", todayCount).put("upcoming_tasks", upcoming);
        return new JSONObject().put("version", VERSION).put("generated_at", Instant.now().toString()).put("time_zone", ZoneId.systemDefault().getId()).put("today", today.toString()).put("summary", summary).put("animals", animals).put("tasks", tasks).put("occurrences", occurrences).put("events", events);
    }

    private JSONObject animalDetail(String publicId) throws Exception {
        long animalId = animalPk(publicId);
        SQLiteDatabase db = getWritableDatabase();
        ensureOccurrences(db);
        JSONObject animal = animalJson(db, animalId);
        if (animal == null) throw new IllegalArgumentException("Tier nicht gefunden");
        return new JSONObject().put("animal", animal).put("tasks", tasksJson(db, animalId)).put("occurrences", occurrencesJson(db, animalId)).put("events", eventsJson(db, animalId, 500));
    }

    private JSONObject catalog() throws Exception {
        JSONArray species = assetItems("species.json");
        JSONArray breeds = combine(assetItems("breeds.json"), assetItems("breeds_supplement.json"));
        JSONArray meds = assetItems("medicines_ch.json"), vaccines = assetItems("vaccines_ch.json");
        JSONArray medNames = new JSONArray(), vaccineNames = new JSONArray();
        for (int i=0;i<meds.length();i++) medNames.put(nameOf(meds.getJSONObject(i)));
        for (int i=0;i<vaccines.length();i++) vaccineNames.put(nameOf(vaccines.getJSONObject(i)));
        return new JSONObject()
            .put("animal_statuses", arr("active","missing","sold","rehomed","deceased","other_departure"))
            .put("animal_sexes", arr("male","female","other"))
            .put("event_types", arr("observation","symptom","weight","diagnosis","treatment","medication","vaccination","veterinary_visit","care","other"))
            .put("weight_units", arr("kg","g","mg"))
            .put("dose_units", arr("mcg","mg","g","ul","ml","drop","tablet","dose"))
            .put("administration_routes", arr("oral","topical","subcutaneous","intramuscular","intravenous","ocular","otic","inhalation","other"))
            .put("symptoms", arr("reduced_appetite","lethargy","diarrhea","coughing","sneezing","lameness","weight_loss","other"))
            .put("symptom_severities", arr("mild","moderate","severe","critical"))
            .put("vaccination_targets", arr("routine","rabies","newcastle","marek","other"))
            .put("task_kinds", arr("reminder","weight","medication","vaccination","health_check","care","veterinary_visit"))
            .put("health_check_results", arr("normal","symptom"))
            .put("medicine_names", medNames).put("vaccine_names", vaccineNames).put("species", species).put("breeds", breeds);
    }

    private JSONObject features() throws Exception {
        SQLiteDatabase db = getReadableDatabase();
        JSONArray groups = groupsJson(db, false);
        JSONObject memberships = new JSONObject();
        try (Cursor c = db.rawQuery("SELECT animal_id,group_id FROM animal_group_memberships WHERE group_id IS NOT NULL", null)) {
            while (c.moveToNext()) memberships.put(animalId(c.getLong(0)), groupId(c.getLong(1)));
        }
        return new JSONObject().put("storage","local_android").put("max_attachment_size_bytes",15728640).put("groups",groups).put("memberships",memberships).put("exports",new JSONObject().put("json","android").put("backup","android").put("animal_pdf","android"));
    }

    private JSONObject v080State() throws Exception {
        SQLiteDatabase db=getReadableDatabase(); JSONArray tags=new JSONArray(); JSONObject memberships=new JSONObject(),profiles=new JSONObject();
        try(Cursor c=db.rawQuery("SELECT t.id,t.name,t.description,COUNT(m.animal_id) FROM tags t LEFT JOIN animal_tag_memberships m ON m.tag_id=t.id GROUP BY t.id ORDER BY t.name COLLATE NOCASE",null)){while(c.moveToNext())tags.put(new JSONObject().put("id",tagId(c.getLong(0))).put("name",c.getString(1)).put("description",nullable(c,2)).put("animal_count",c.getInt(3))));}
        try(Cursor c=db.rawQuery("SELECT animal_id,tag_id FROM animal_tag_memberships ORDER BY animal_id,tag_id",null)){while(c.moveToNext()){String a=animalId(c.getLong(0));JSONArray list=memberships.optJSONArray(a);if(list==null){list=new JSONArray();memberships.put(a,list);}list.put(tagId(c.getLong(1)));}}
        try(Cursor c=db.rawQuery("SELECT animal_id,attachment_id FROM profiles",null)){while(c.moveToNext())profiles.put(animalId(c.getLong(0)),c.isNull(1)?JSONObject.NULL:attachmentId(c.getLong(1)));}
        return new JSONObject().put("primary_group_required",false).put("tags",tags).put("tag_memberships",memberships).put("profiles",profiles);
    }

    private JSONObject v081State() throws Exception {
        SQLiteDatabase db=getReadableDatabase(); JSONObject settings=new JSONObject().put("ai_task_entity_id",setting(db,"ai_task_entity_id","")).put("stt_entity_id",setting(db,"stt_entity_id","")); JSONArray groupEvents=new JSONArray(),groupTasks=new JSONArray();
        try(Cursor c=db.rawQuery("SELECT ge.id,ge.group_id,g.name,ge.event_type,ge.occurred_at,ge.title,ge.notes,ge.value,ge.unit,ge.data_json FROM group_events ge JOIN groups g ON g.id=ge.group_id ORDER BY ge.occurred_at DESC,ge.id DESC",null)){while(c.moveToNext())groupEvents.put(new JSONObject().put("id","GE-A"+c.getLong(0)).put("group_id",groupId(c.getLong(1))).put("group_name",c.getString(2)).put("event_type",c.getString(3)).put("occurred_at",iso(c.getLong(4))).put("title",c.getString(5)).put("notes",nullable(c,6)).put("value",c.isNull(7)?JSONObject.NULL:c.getDouble(7)).put("unit",nullable(c,8)).put("data",json(c.getString(9)))));}
        try(Cursor c=db.rawQuery("SELECT t.id,t.group_id,g.name,t.kind,t.planned_json FROM tasks t JOIN groups g ON g.id=t.group_id WHERE t.group_id IS NOT NULL",null)){while(c.moveToNext())groupTasks.put(new JSONObject().put("task_id",taskId(c.getLong(0))).put("group_id",groupId(c.getLong(1))).put("group_name",c.getString(2)).put("task_kind",c.getString(3)).put("planned",json(c.getString(4)))));}
        return new JSONObject().put("settings",settings).put("group_events",groupEvents).put("group_tasks",groupTasks);
    }

    private JSONObject v083State() throws Exception {
        SQLiteDatabase db=getReadableDatabase(); JSONObject animalMeta=new JSONObject(),groupMeta=new JSONObject(); JSONArray custom=new JSONArray(),medicines=assetItems("medicines_ch.json");
        try(Cursor c=db.rawQuery("SELECT id,distinctive_features FROM animals",null)){while(c.moveToNext())animalMeta.put(animalId(c.getLong(0)),new JSONObject().put("distinctive_features",nullable(c,1)) );}
        try(Cursor c=db.rawQuery("SELECT group_id,breed FROM group_metadata",null)){while(c.moveToNext())groupMeta.put(groupId(c.getLong(0)),new JSONObject().put("breed",nullable(c,1)) );}
        try(Cursor c=db.rawQuery("SELECT id,kind,species_id,breed_context,value FROM custom_values ORDER BY value COLLATE NOCASE",null)){while(c.moveToNext())custom.put(new JSONObject().put("id",c.getLong(0)).put("kind",c.getString(1)).put("species_id",c.getString(2)).put("breed_context",c.getString(3)).put("value",c.getString(4)));}
        JSONArray normalized=new JSONArray(); for(int i=0;i<medicines.length();i++){JSONObject src=medicines.getJSONObject(i);normalized.put(new JSONObject().put("id",src.optString("id","med-"+i)).put("name",nameOf(src)).put("active_ingredients",src.optJSONArray("active_ingredients")!=null?src.optJSONArray("active_ingredients"):new JSONArray()).put("target_species",src.optJSONArray("target_species")!=null?src.optJSONArray("target_species"):new JSONArray()).put("aliases",src.optJSONArray("aliases")!=null?src.optJSONArray("aliases"):new JSONArray()).put("authorisation_number",src.has("authorisation_number")?src.opt("authorisation_number"):JSONObject.NULL).put("catalog_source","standard"));}
        return new JSONObject().put("animal_metadata",animalMeta).put("group_metadata",groupMeta).put("custom_values",custom).put("medicines",normalized);
    }

    private JSONObject v0817State() throws Exception {
        SQLiteDatabase db=getReadableDatabase(); JSONArray meds=new JSONArray();
        try(Cursor c=db.rawQuery("SELECT id,name,species,default_unit,default_route FROM medications ORDER BY name COLLATE NOCASE",null)){while(c.moveToNext())meds.put(new JSONObject().put("id",c.getLong(0)).put("name",c.getString(1)).put("species_id",nullable(c,2)).put("default_unit",nullable(c,3)).put("default_route",nullable(c,4)) );}
        return new JSONObject().put("off_label_enabled","1".equals(setting(db,"off_label_enabled","0"))).put("medications",meds);
    }

    private JSONObject aiStatus() throws Exception {
        SQLiteDatabase db=getReadableDatabase(); boolean configured=!setting(db,"ai_provider_url","").isEmpty();
        return new JSONObject().put("available",configured).put("entities",configured?arr("android.ai"):new JSONArray()).put("stt_available",true).put("stt_entities",arr("android.speech"));
    }

    private JSONObject historySuggestions() throws Exception {
        SQLiteDatabase db=getReadableDatabase(); JSONArray meds=new JSONArray();
        try(Cursor c=db.rawQuery("SELECT medication_name,COUNT(*) n FROM events WHERE medication_name IS NOT NULL GROUP BY medication_name ORDER BY n DESC,medication_name LIMIT 30",null)){while(c.moveToNext())meds.put(c.getString(0));}
        return new JSONObject().put("medication_name",meds).put("vaccine_name",new JSONArray()).put("provider",new JSONArray()).put("visit_reason",new JSONArray());
    }

    private JSONObject diagnostics() throws Exception {
        SQLiteDatabase db=getReadableDatabase(); return new JSONObject().put("storage","Android SQLite").put("version",VERSION).put("animals",count(db,"animals")).put("groups",count(db,"groups")).put("events",count(db,"events")).put("tasks",count(db,"tasks")).put("attachments",count(db,"attachments")).put("errors",new JSONArray());
    }

    private JSONObject serviceCreateAnimal(JSONObject p) throws Exception {
        SQLiteDatabase db=getWritableDatabase(); ContentValues v=new ContentValues(); v.put("name",required(p,"name"));v.put("species",required(p,"species"));put(v,"breed",p.optString("breed",null));put(v,"color",p.optString("color",null));put(v,"sex",p.optString("sex",null));put(v,"birth_date",p.optString("birth_date",null));put(v,"arrival_date",p.optString("arrival_date",null));v.put("status","active");v.put("created_at",System.currentTimeMillis());long id=db.insertOrThrow("animals",null,v);return new JSONObject().put("id",animalId(id)).put("event_id",JSONObject.NULL).put("animal",animalJson(db,id));
    }

    private JSONObject serviceUpdateAnimal(JSONObject p) throws Exception {long id=devicePk(p.getString("device_id"));SQLiteDatabase db=getWritableDatabase();ContentValues v=new ContentValues();for(String k:new String[]{"name","species","breed","color","sex","birth_date","arrival_date"})if(p.has(k)){if(p.isNull(k)||p.optString(k).isBlank())v.putNull(k);else v.put(k,p.optString(k));}db.update("animals",v,"id=?",args(id));return new JSONObject().put("id",animalId(id)).put("animal",animalJson(db,id));}
    private JSONObject serviceArchiveAnimal(JSONObject p,boolean archived)throws Exception{long id=devicePk(p.getString("device_id"));ContentValues v=new ContentValues();v.put("is_archived",archived?1:0);getWritableDatabase().update("animals",v,"id=?",args(id));return new JSONObject().put("id",animalId(id));}
    private JSONObject serviceStatus(JSONObject p)throws Exception{long id=devicePk(p.getString("device_id"));ContentValues v=new ContentValues();v.put("status",p.getString("status"));getWritableDatabase().update("animals",v,"id=?",args(id));return new JSONObject().put("id",animalId(id));}
    private JSONObject serviceWeight(JSONObject p)throws Exception{long id=devicePk(p.getString("device_id"));double value=p.getDouble("weight");String unit=p.optString("weight_unit","kg");long when=parseDateTime(p.optString("occurred_at",null),System.currentTimeMillis());long event=insertEvent(getWritableDatabase(),id,"weight",when,"weight_measurement",empty(p.optString("notes",null)),value,unit,null,null,null,new JSONObject());return new JSONObject().put("event_id",eventId(event)).put("id",eventId(event));}
    private JSONObject serviceEvent(JSONObject p)throws Exception{long id=devicePk(p.getString("device_id"));long when=parseDateTime(p.optString("occurred_at",null),System.currentTimeMillis());long event=insertEvent(getWritableDatabase(),id,p.optString("event_type","observation"),when,required(p,"title"),empty(p.optString("notes",null)),null,null,null,null,null,new JSONObject());return new JSONObject().put("event_id",eventId(event)).put("id",eventId(event));}
    private JSONObject serviceSymptom(JSONObject p)throws Exception{long id=devicePk(p.getString("device_id"));String symptom=p.optString("symptom","other");if("other".equals(symptom)&&!p.optString("custom_symptom","").isBlank())symptom=p.optString("custom_symptom");JSONObject data=new JSONObject().put("symptom",symptom).put("severity",p.optString("severity","mild"));long event=insertEvent(getWritableDatabase(),id,"symptom",parseDateTime(p.optString("occurred_at",null),System.currentTimeMillis()),symptom,empty(p.optString("notes",null)),null,null,null,null,null,data);return new JSONObject().put("event_id",eventId(event)).put("id",eventId(event));}

    private JSONObject serviceCreateTask(JSONObject p)throws Exception{SQLiteDatabase db=getWritableDatabase();JSONArray deviceIds=p.optJSONArray("device_ids");List<Long> ids=new ArrayList<>();if("animal".equals(p.optString("task_scope"))&&deviceIds!=null){for(int i=0;i<deviceIds.length();i++)ids.add(devicePk(deviceIds.getString(i)));}else ids.add(null);JSONArray created=new JSONArray();for(Long animal:ids){long id=createTask(db,animal,null,p);created.put(new JSONObject().put("id",taskId(id)));}ensureOccurrences(db);return new JSONObject().put("tasks",created).put("id",created.length()>0?created.getJSONObject(0).getString("id"):JSONObject.NULL);}
    private JSONObject serviceTaskActive(JSONObject p)throws Exception{long id=taskPk(p.getString("task_id"));ContentValues v=new ContentValues();v.put("is_active",p.optBoolean("is_active",true)?1:0);getWritableDatabase().update("tasks",v,"id=?",args(id));return new JSONObject().put("id",taskId(id));}

    private JSONObject serviceExecuteOccurrence(String service,JSONObject p)throws Exception{long occ=occurrencePk(p.getString("occurrence_id"));SQLiteDatabase db=getWritableDatabase();JSONObject actual=new JSONObject();for(String k:new String[]{"weight","weight_unit","medication_name","dose","dose_unit","route","vaccine_name","antigen","batch_number","check_result","symptom","custom_symptom","severity","care_action","outcome","visit_reason","provider","diagnosis"})if(p.has(k))actual.put(k,p.get(k));return completeOccurrence(db,occ,actual,p.optString("performed_at",null),p.optString("notes",null),service);}
    private JSONObject resolveOccurrence(JSONObject p,String status)throws Exception{long id=occurrencePk(p.getString("occurrence_id"));SQLiteDatabase db=getWritableDatabase();ContentValues v=new ContentValues();v.put("status",status);v.put("completed_at",System.currentTimeMillis());put(v,"notes",p.optString("notes",null));db.update("occurrences",v,"id=?",args(id));ensureOccurrences(db);return new JSONObject().put("id",occurrenceId(id)).put("status",status);}

    private JSONObject createGroup(JSONObject p)throws Exception{SQLiteDatabase db=getWritableDatabase();ContentValues v=new ContentValues();v.put("name",required(p,"name"));put(v,"species",p.optString("species",null));put(v,"description",p.optString("description",null));v.put("created_at",System.currentTimeMillis());long id=db.insertOrThrow("groups",null,v);return groupJson(db,id);}
    private JSONObject updateGroup(JSONObject p)throws Exception{long id=groupPk(p.getString("group_id"));ContentValues v=new ContentValues();v.put("name",required(p,"name"));put(v,"species",p.optString("species",null));put(v,"description",p.optString("description",null));getWritableDatabase().update("groups",v,"id=?",args(id));return groupJson(getReadableDatabase(),id);}
    private JSONObject deleteGroup(JSONObject p)throws Exception{long id=groupPk(p.getString("group_id"));SQLiteDatabase db=getWritableDatabase();db.delete("animal_group_memberships","group_id=?",args(id));db.delete("groups","id=?",args(id));return new JSONObject().put("deleted",groupId(id));}
    private JSONObject setAnimalGroup(JSONObject p)throws Exception{long animal=animalPk(p.getString("animal_id"));SQLiteDatabase db=getWritableDatabase();db.delete("animal_group_memberships","animal_id=?",args(animal));if(p.has("group_id")&&!p.isNull("group_id")&&!p.optString("group_id").isBlank()){ContentValues v=new ContentValues();v.put("animal_id",animal);v.put("group_id",groupPk(p.getString("group_id")));db.insertOrThrow("animal_group_memberships",null,v);}return new JSONObject().put("animal_id",animalId(animal));}

    private JSONObject createTag(JSONObject p)throws Exception{ContentValues v=new ContentValues();v.put("name",required(p,"name"));put(v,"description",p.optString("description",null));v.put("created_at",System.currentTimeMillis());long id=getWritableDatabase().insertOrThrow("tags",null,v);return new JSONObject().put("id",tagId(id)).put("name",p.getString("name")).put("description",p.opt("description")).put("animal_count",0);}
    private JSONObject updateTag(JSONObject p)throws Exception{long id=tagPk(p.getString("tag_id"));ContentValues v=new ContentValues();v.put("name",required(p,"name"));put(v,"description",p.optString("description",null));getWritableDatabase().update("tags",v,"id=?",args(id));return new JSONObject().put("id",tagId(id)).put("name",p.getString("name")).put("description",p.opt("description"));}
    private JSONObject deleteTag(JSONObject p)throws Exception{long id=tagPk(p.getString("tag_id"));getWritableDatabase().delete("tags","id=?",args(id));return new JSONObject().put("deleted",tagId(id));}
    private JSONObject setTags(JSONObject p)throws Exception{long animal=animalPk(p.getString("animal_id"));JSONArray list=p.optJSONArray("tag_ids");SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{db.delete("animal_tag_memberships","animal_id=?",args(animal));if(list!=null)for(int i=0;i<list.length();i++){ContentValues v=new ContentValues();v.put("animal_id",animal);v.put("tag_id",tagPk(list.getString(i)));db.insertOrThrow("animal_tag_memberships",null,v);}db.setTransactionSuccessful();}finally{db.endTransaction();}return new JSONObject().put("animal_id",animalId(animal));}

    private JSONObject uploadDirect(JSONObject p)throws Exception{byte[] bytes=Base64.decode(p.getString("content_base64"),Base64.DEFAULT);if(bytes.length>15728640)throw new IllegalArgumentException("Datei zu gross");ContentValues v=new ContentValues();if(p.has("animal_id")&&!p.optString("animal_id").isBlank())v.put("animal_id",animalPk(p.getString("animal_id")));if(p.has("event_id")&&!p.optString("event_id").isBlank())v.put("event_id",eventPk(p.getString("event_id")));v.put("filename",p.optString("filename","document"));v.put("media_type",p.optString("media_type","application/octet-stream"));put(v,"title",p.optString("title",null));v.put("size_bytes",bytes.length);v.put("content",bytes);v.put("created_at",System.currentTimeMillis());long id=getWritableDatabase().insertOrThrow("attachments",null,v);return attachmentJson(getReadableDatabase(),id);}
    private JSONObject attachmentList(JSONObject p)throws Exception{long animal=animalPk(p.getString("animal_id"));SQLiteDatabase db=getReadableDatabase();JSONArray list=new JSONArray();try(Cursor c=db.rawQuery("SELECT id FROM attachments WHERE animal_id=? ORDER BY created_at DESC,id DESC",args(animal))){while(c.moveToNext())list.put(attachmentJson(db,c.getLong(0)));}return new JSONObject().put("attachments",list);}
    private JSONObject deleteAttachment(JSONObject p)throws Exception{long id=attachmentPk(p.getString("attachment_id"));getWritableDatabase().delete("attachments","id=?",args(id));return new JSONObject().put("deleted",attachmentId(id));}
    private JSONObject setPhoto(JSONObject p)throws Exception{long animal=animalPk(p.getString("animal_id")),attachment=attachmentPk(p.getString("attachment_id"));SQLiteDatabase db=getWritableDatabase();ContentValues v=new ContentValues();v.put("animal_id",animal);v.put("attachment_id",attachment);db.insertWithOnConflict("profiles",null,v,SQLiteDatabase.CONFLICT_REPLACE);return new JSONObject().put("animal_id",animalId(animal)).put("attachment_id",attachmentId(attachment));}
    private JSONObject removePhoto(JSONObject p)throws Exception{long animal=animalPk(p.getString("animal_id"));getWritableDatabase().delete("profiles","animal_id=?",args(animal));return new JSONObject().put("animal_id",animalId(animal));}
    private JSONObject previewAttachment(JSONObject p)throws Exception{return new JSONObject().put("url","https://app.local/attachment/"+p.getString("attachment_id")).put("attachment_id",p.getString("attachment_id"));}

    private JSONObject updateV081Settings(JSONObject p)throws Exception{SQLiteDatabase db=getWritableDatabase();setSetting(db,"ai_task_entity_id",p.isNull("ai_task_entity_id")?"":p.optString("ai_task_entity_id"));setSetting(db,"stt_entity_id",p.isNull("stt_entity_id")?"":p.optString("stt_entity_id"));return new JSONObject().put("ok",true);}
    private JSONObject recordProduct(JSONObject p)throws Exception{long animal=animalPk(p.getString("animal_id"));String name=required(p,"product_name"),type=p.optString("product_type","medication"),eventType="medication".equals(type)?"medication":"treatment";JSONObject data=new JSONObject().put("product_type",type).put("medication_name",name);if(p.has("route"))data.put("route",p.optString("route"));long id=insertEvent(getWritableDatabase(),animal,eventType,parseDateTime(p.optString("occurred_at",null),System.currentTimeMillis()),name,empty(p.optString("notes",null)),p.getDouble("dose"),p.optString("dose_unit","dose"),name,p.optString("route",null),null,data);return new JSONObject().put("id",eventId(id)).put("event_id",eventId(id));}
    private JSONObject correctWeight(JSONObject p)throws Exception{long source=eventPk(p.getString("event_id"));SQLiteDatabase db=getWritableDatabase();long animal;try(Cursor c=db.rawQuery("SELECT animal_id,occurred_at FROM events WHERE id=?",args(source))){if(!c.moveToFirst())throw new IllegalArgumentException("Eintrag nicht gefunden");animal=c.getLong(0);}long id=insertEvent(db,animal,"weight",parseDateTime(p.optString("occurred_at",null),System.currentTimeMillis()),"weight_measurement",empty(p.optString("notes",null)),p.getDouble("weight"),p.optString("weight_unit","kg"),null,null,source,new JSONObject());return new JSONObject().put("id",eventId(id));}
    private JSONObject createGroupEvent(JSONObject p)throws Exception{long group=groupPk(p.getString("group_id"));ContentValues v=new ContentValues();v.put("group_id",group);v.put("event_type",p.optString("event_type","observation"));v.put("occurred_at",parseDateTime(p.optString("occurred_at",null),System.currentTimeMillis()));v.put("title",required(p,"title"));put(v,"notes",p.optString("notes",null));if(p.has("value"))v.put("value",p.optDouble("value"));put(v,"unit",p.optString("unit",null));v.put("data_json",p.optJSONObject("data")!=null?p.optJSONObject("data").toString():"{}");v.put("created_at",System.currentTimeMillis());long id=getWritableDatabase().insertOrThrow("group_events",null,v);return new JSONObject().put("id","GE-A"+id);}
    private JSONObject createGroupTask(JSONObject p)throws Exception{long group=groupPk(p.getString("group_id"));JSONObject task=new JSONObject(p.toString());task.put("task_scope","group");task.put("task_kind",p.optString("task_kind","reminder"));long id=createTask(getWritableDatabase(),null,group,task);ensureOccurrences(getWritableDatabase());return new JSONObject().put("id",taskId(id));}
    private JSONObject executeGroupTask(JSONObject p)throws Exception{return completeOccurrence(getWritableDatabase(),occurrencePk(p.getString("occurrence_id")),p.optJSONObject("actual")!=null?p.optJSONObject("actual"):new JSONObject(),p.optString("performed_at",null),p.optString("notes",null),"group");}

    private JSONObject setAnimalMetadata(JSONObject p)throws Exception{long id=animalPk(p.getString("animal_id"));ContentValues v=new ContentValues();put(v,"distinctive_features",p.optString("distinctive_features",null));getWritableDatabase().update("animals",v,"id=?",args(id));return new JSONObject().put("animal_id",animalId(id));}
    private JSONObject setGroupMetadata(JSONObject p)throws Exception{long id=groupPk(p.getString("group_id"));ContentValues v=new ContentValues();v.put("group_id",id);put(v,"breed",p.optString("breed",null));getWritableDatabase().insertWithOnConflict("group_metadata",null,v,SQLiteDatabase.CONFLICT_REPLACE);return new JSONObject().put("group_id",groupId(id));}
    private JSONObject rememberCustom(JSONObject p)throws Exception{ContentValues v=new ContentValues();v.put("kind",required(p,"kind"));v.put("species_id",p.optString("species_id",""));v.put("breed_context",p.optString("breed_context",""));v.put("value",required(p,"value"));long id=getWritableDatabase().insertWithOnConflict("custom_values",null,v,SQLiteDatabase.CONFLICT_IGNORE);return new JSONObject().put("id",id).put("value",p.getString("value"));}

    private JSONObject update0817Settings(JSONObject p)throws Exception{setSetting(getWritableDatabase(),"off_label_enabled",p.optBoolean("off_label_enabled",false)?"1":"0");return v0817State();}
    private JSONObject recordMedicationPreset(JSONObject p)throws Exception{ContentValues v=new ContentValues();v.put("name",required(p,"name"));put(v,"species",p.optString("species_id",null));put(v,"default_unit",p.optString("default_unit",null));put(v,"default_route",p.optString("default_route",null));v.put("created_at",System.currentTimeMillis());getWritableDatabase().insertWithOnConflict("medications",null,v,SQLiteDatabase.CONFLICT_REPLACE);return v0817State();}
    private JSONObject deleteMedicationPreset(JSONObject p)throws Exception{if(p.has("id"))getWritableDatabase().delete("medications","id=?",args(p.optLong("id")));else getWritableDatabase().delete("medications","name=?",new String[]{p.optString("name")});return v0817State();}
    private JSONObject recordMedicationBatch(JSONObject p)throws Exception{long animal=animalPk(p.getString("animal_id"));long when=parseDateTime(p.optString("occurred_at",null),System.currentTimeMillis());JSONArray items=p.optJSONArray("items");if(items==null)items=p.optJSONArray("medications");if(items==null)throw new IllegalArgumentException("Keine Medikamente");SQLiteDatabase db=getWritableDatabase();db.beginTransaction();JSONArray ids=new JSONArray();try{for(int i=0;i<items.length();i++){JSONObject item=items.getJSONObject(i);String name=item.optString("product_name",item.optString("medication_name",""));JSONObject data=new JSONObject().put("product_type",item.optString("product_type","medication")).put("medication_name",name).put("route",item.optString("route",""));Long correction=null;if(!item.optString("correction_event_id","").isBlank())correction=eventPk(item.optString("correction_event_id"));long id=insertEvent(db,animal,"medication",when,name,empty(p.optString("notes",null)),item.optDouble("dose",1),item.optString("dose_unit","dose"),name,item.optString("route",null),correction,data);ids.put(eventId(id));}db.setTransactionSuccessful();}finally{db.endTransaction();}return new JSONObject().put("event_ids",ids).put("count",ids.length());}

    private JSONObject resetActivity() throws Exception {SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{db.delete("occurrences",null,null);db.delete("tasks",null,null);db.delete("group_events",null,null);db.delete("events",null,null);db.delete("attachments",null,null);db.delete("profiles",null,null);db.setTransactionSuccessful();}finally{db.endTransaction();}return new JSONObject().put("ok",true);}
    private JSONObject resetAll() throws Exception {SQLiteDatabase db=getWritableDatabase();db.beginTransaction();try{for(String t:new String[]{"occurrences","tasks","group_events","events","profiles","attachments","animal_tag_memberships","tags","animal_group_memberships","group_metadata","groups","medications","custom_values","settings","animals"})db.delete(t,null,null);db.setTransactionSuccessful();}finally{db.endTransaction();}return new JSONObject().put("ok",true);}

    private long createTask(SQLiteDatabase db,Long animal,Long group,JSONObject p)throws Exception{String kind=p.optString("task_kind",p.optString("kind","reminder"));String start=p.optString("start_date",LocalDate.now().toString());String dueTime=p.optString("due_time","");long due=localDateTimeMillis(start,dueTime);ContentValues v=new ContentValues();if(animal!=null)v.put("animal_id",animal);if(group!=null)v.put("group_id",group);v.put("title",required(p,"title"));put(v,"description",p.optString("description",null));v.put("due_at",due);v.put("kind",kind);v.put("done",0);v.put("recurrence_type",p.optString("recurrence_type","once"));v.put("recurrence_interval",Math.max(1,p.optInt("recurrence_interval",1)));v.put("start_date",start);put(v,"end_date",p.optString("end_date",null));put(v,"due_time",dueTime);v.put("is_active",1);JSONObject planned=p.optJSONObject("planned");if(planned==null){planned=new JSONObject();for(String key:new String[]{"planned_medication_name","planned_dose","planned_dose_unit","planned_route","planned_vaccine_name","planned_vaccination_dose","planned_vaccination_dose_unit","planned_vaccination_route","planned_check_focus","planned_care_action","planned_visit_reason","planned_provider"})if(p.has(key)){String out=key.replace("planned_","").replace("vaccination_dose","dose").replace("vaccination_route","route").replace("vaccination_dose_unit","dose_unit");planned.put(out,p.get(key));}}v.put("planned_json",planned.toString());v.put("created_at",System.currentTimeMillis());return db.insertOrThrow("tasks",null,v);}

    private void ensureOccurrences(SQLiteDatabase db)throws Exception{try(Cursor c=db.rawQuery("SELECT id,recurrence_type,recurrence_interval,start_date,end_date,due_time,is_active FROM tasks",null)){while(c.moveToNext()){long task=c.getLong(0);if(c.getInt(6)==0)continue;try(Cursor pending=db.rawQuery("SELECT id FROM occurrences WHERE task_id=? AND status='pending' LIMIT 1",args(task))){if(pending.moveToFirst())continue;}String recurrence=c.getString(1);int interval=Math.max(1,c.getInt(2));LocalDate start=parseDate(c.getString(3),LocalDate.now());String endText=nullable(c,4);LocalDate end=endText==null?null:LocalDate.parse(endText);String time=nullable(c,5);long next=nextScheduled(db,task,recurrence,interval,start,end,time);if(next>0){ContentValues v=new ContentValues();v.put("task_id",task);v.put("scheduled_at",next);v.put("status","pending");v.put("actual_json","{}");db.insertWithOnConflict("occurrences",null,v,SQLiteDatabase.CONFLICT_IGNORE);}}}}

    private long nextScheduled(SQLiteDatabase db,long task,String recurrence,int interval,LocalDate start,LocalDate end,String time)throws Exception{LocalDate candidate=start;try(Cursor c=db.rawQuery("SELECT MAX(scheduled_at) FROM occurrences WHERE task_id=?",args(task))){if(c.moveToFirst()&&!c.isNull(0)){LocalDate last=Instant.ofEpochMilli(c.getLong(0)).atZone(ZoneId.systemDefault()).toLocalDate();if("once".equals(recurrence))return -1;if("daily".equals(recurrence))candidate=last.plusDays(interval);else if("weekly".equals(recurrence))candidate=last.plusWeeks(interval);else if("monthly".equals(recurrence))candidate=last.plusMonths(interval);}}
        if(end!=null&&candidate.isAfter(end))return -1;return localDateTimeMillis(candidate.toString(),time==null?"":time);}

    private JSONObject completeOccurrence(SQLiteDatabase db,long occ,JSONObject actual,String performedText,String notes,String service)throws Exception{long task,animal=0,group=0;String kind,title,plannedText;try(Cursor c=db.rawQuery("SELECT o.task_id,t.animal_id,t.group_id,t.kind,t.title,t.planned_json FROM occurrences o JOIN tasks t ON t.id=o.task_id WHERE o.id=?",args(occ))){if(!c.moveToFirst())throw new IllegalArgumentException("Termin nicht gefunden");task=c.getLong(0);animal=c.isNull(1)?0:c.getLong(1);group=c.isNull(2)?0:c.getLong(2);kind=c.getString(3);title=c.getString(4);plannedText=c.getString(5);}long performed=parseDateTime(performedText,System.currentTimeMillis());ContentValues o=new ContentValues();o.put("status","completed");o.put("completed_at",performed);put(o,"notes",notes);o.put("actual_json",actual.toString());db.update("occurrences",o,"id=?",args(occ));JSONObject planned=json(plannedText),merged=new JSONObject(planned.toString());for(String key:keys(actual))merged.put(key,actual.get(key));String eventPublic=null;if(animal>0){String eventType=kind;String eventTitle=title;Double value=null;String unit=null,med=null,route=null;if("weight".equals(kind)){value=numberOrNull(merged,"weight");unit=merged.optString("weight_unit","kg");eventTitle="weight_measurement";}else if("medication".equals(kind)){value=numberOrNull(merged,"dose");unit=merged.optString("dose_unit","dose");med=merged.optString("medication_name",title);route=merged.optString("route",null);eventTitle=med;}else if("vaccination".equals(kind)){value=numberOrNull(merged,"dose");unit=merged.optString("dose_unit","ml");eventTitle=merged.optString("vaccine_name",title);}JSONObject data=new JSONObject().put("task_execution",new JSONObject().put("planned",planned).put("actual",actual));long event=insertEvent(db,animal,eventType,performed,eventTitle,empty(notes),value,unit,med,route,null,data);eventPublic=eventId(event);}else if(group>0){JSONObject gp=new JSONObject().put("group_id",groupId(group)).put("event_type",kind).put("title",title).put("occurred_at",iso(performed)).put("data",merged);createGroupEvent(gp);}ensureOccurrences(db);return new JSONObject().put("id",occurrenceId(occ)).put("event_id",eventPublic==null?JSONObject.NULL:eventPublic).put("status","completed");}

    private long insertEvent(SQLiteDatabase db,long animal,String type,long when,String title,String notes,Double value,String unit,String medication,String route,Long correction,JSONObject data){ContentValues v=new ContentValues();v.put("animal_id",animal);v.put("type",type);v.put("occurred_at",when);v.put("title",title==null||title.isBlank()?type:title);put(v,"notes",notes);if(value!=null)v.put("value",value);put(v,"unit",unit);put(v,"medication_name",medication);put(v,"route",route);if(correction!=null)v.put("correction_of_id",correction);v.put("data_json",data==null?"{}":data.toString());v.put("created_at",System.currentTimeMillis());return db.insertOrThrow("events",null,v);}

    private JSONArray animalsJson(SQLiteDatabase db)throws Exception{JSONArray out=new JSONArray();try(Cursor c=db.rawQuery("SELECT id FROM animals ORDER BY name COLLATE NOCASE,id",null)){while(c.moveToNext())out.put(animalJson(db,c.getLong(0)));}return out;}
    private JSONObject animalJson(SQLiteDatabase db,long id)throws Exception{try(Cursor c=db.rawQuery("SELECT id,name,species,breed,color,sex,birth_date,arrival_date,status,is_archived,distinctive_features FROM animals WHERE id=?",args(id))){if(!c.moveToFirst())return null;JSONObject o=new JSONObject().put("id",animalId(id)).put("device_id",deviceId(id)).put("name",c.getString(1)).put("species",c.getString(2)).put("breed",nullable(c,3)).put("color",nullable(c,4)).put("sex",nullable(c,5)).put("birth_date",nullable(c,6)).put("arrival_date",nullable(c,7)).put("status",c.getString(8)).put("is_archived",c.getInt(9)!=0).put("distinctive_features",nullable(c,10));try(Cursor g=db.rawQuery("SELECT group_id FROM animal_group_memberships WHERE animal_id=?",args(id))){if(g.moveToFirst()&&!g.isNull(0)){long gid=g.getLong(0);o.put("group_id",groupId(gid));JSONObject gg=groupJson(db,gid);o.put("group_name",gg==null?JSONObject.NULL:gg.optString("name"));}}
            JSONArray tagIds=new JSONArray(),tags=new JSONArray();try(Cursor t=db.rawQuery("SELECT t.id,t.name FROM tags t JOIN animal_tag_memberships m ON m.tag_id=t.id WHERE m.animal_id=? ORDER BY t.name",args(id))){while(t.moveToNext()){tagIds.put(tagId(t.getLong(0)));tags.put(new JSONObject().put("id",tagId(t.getLong(0))).put("name",t.getString(1)));}}o.put("tag_ids",tagIds).put("tags",tags);try(Cursor p=db.rawQuery("SELECT attachment_id FROM profiles WHERE animal_id=?",args(id))){if(p.moveToFirst()&&!p.isNull(0))o.put("profile_image_id",attachmentId(p.getLong(0)));}try(Cursor w=db.rawQuery("SELECT id,value,unit,occurred_at FROM events e WHERE animal_id=? AND type='weight' AND NOT EXISTS(SELECT 1 FROM events c WHERE c.correction_of_id=e.id) ORDER BY occurred_at DESC,id DESC LIMIT 1",args(id))){if(w.moveToFirst())o.put("latest_weight",new JSONObject().put("event_id",eventId(w.getLong(0))).put("value_kg",weightKg(w.getDouble(1),w.getString(2))).put("original_value",w.getDouble(1)).put("original_unit",w.getString(2)).put("occurred_at",iso(w.getLong(3))));else o.put("latest_weight",JSONObject.NULL);}return o;}}

    private JSONArray groupsJson(SQLiteDatabase db,boolean archived)throws Exception{JSONArray out=new JSONArray();try(Cursor c=db.rawQuery("SELECT g.id FROM groups g WHERE g.is_archived=? ORDER BY g.name COLLATE NOCASE",args(archived?1:0))){while(c.moveToNext())out.put(groupJson(db,c.getLong(0)));}return out;}
    private JSONObject groupJson(SQLiteDatabase db,long id)throws Exception{try(Cursor c=db.rawQuery("SELECT g.id,g.name,g.species,g.description,g.is_archived,(SELECT COUNT(*) FROM animal_group_memberships m WHERE m.group_id=g.id) FROM groups g WHERE g.id=?",args(id))){if(!c.moveToFirst())return null;return new JSONObject().put("id",groupId(id)).put("name",c.getString(1)).put("species",nullable(c,2)).put("description",nullable(c,3)).put("is_archived",c.getInt(4)!=0).put("animal_count",c.getInt(5));}}

    private JSONArray tasksJson(SQLiteDatabase db,Long animalFilter)throws Exception{JSONArray out=new JSONArray();String where=animalFilter==null?"":" WHERE t.animal_id=?";String[] a=animalFilter==null?null:args(animalFilter);try(Cursor c=db.rawQuery("SELECT t.id,t.animal_id,t.group_id,t.title,t.description,t.kind,t.recurrence_type,t.recurrence_interval,t.start_date,t.end_date,t.due_time,t.is_active,t.planned_json,a.name,g.name FROM tasks t LEFT JOIN animals a ON a.id=t.animal_id LEFT JOIN groups g ON g.id=t.group_id"+where+" ORDER BY t.title COLLATE NOCASE,t.id",a)){while(c.moveToNext()){JSONObject o=new JSONObject().put("id",taskId(c.getLong(0))).put("animal_id",c.isNull(1)?JSONObject.NULL:animalId(c.getLong(1))).put("group_id",c.isNull(2)?JSONObject.NULL:groupId(c.getLong(2))).put("title",c.getString(3)).put("description",nullable(c,4)).put("task_kind",c.getString(5)).put("recurrence_type",c.getString(6)).put("recurrence_interval",c.getInt(7)).put("start_date",nullable(c,8)).put("end_date",nullable(c,9)).put("due_time",nullable(c,10)).put("is_active",c.getInt(11)!=0).put("planned",json(c.getString(12))).put("animal_name",c.isNull(13)?(c.isNull(14)?JSONObject.NULL:c.getString(14)):c.getString(13)).put("group_name",nullable(c,14)).put("entity_id",JSONObject.NULL);out.put(o);}}return out;}

    private JSONArray occurrencesJson(SQLiteDatabase db,Long animalFilter)throws Exception{JSONArray out=new JSONArray();String where=animalFilter==null?"":" AND t.animal_id=?";String[] a=animalFilter==null?null:args(animalFilter);try(Cursor c=db.rawQuery("SELECT o.id,o.task_id,o.scheduled_at,o.status,o.completed_at,o.notes,o.actual_json,t.animal_id,t.group_id,t.title,t.kind,t.planned_json,a.name,g.name FROM occurrences o JOIN tasks t ON t.id=o.task_id LEFT JOIN animals a ON a.id=t.animal_id LEFT JOIN groups g ON g.id=t.group_id WHERE 1=1"+where+" ORDER BY o.scheduled_at DESC,o.id DESC",a)){LocalDate today=LocalDate.now();while(c.moveToNext()){long scheduled=c.getLong(2);LocalDate day=Instant.ofEpochMilli(scheduled).atZone(ZoneId.systemDefault()).toLocalDate();String status=c.getString(3);JSONObject o=new JSONObject().put("id",occurrenceId(c.getLong(0))).put("task_id",taskId(c.getLong(1))).put("scheduled_for",iso(scheduled)).put("scheduled_local",localIso(scheduled)).put("scheduled_date",day.toString()).put("status",status).put("completed_at",c.isNull(4)?JSONObject.NULL:iso(c.getLong(4))).put("notes",nullable(c,5)).put("actual",json(c.getString(6))).put("animal_id",c.isNull(7)?JSONObject.NULL:animalId(c.getLong(7))).put("group_id",c.isNull(8)?JSONObject.NULL:groupId(c.getLong(8))).put("task_title",c.getString(9)).put("task_kind",c.getString(10)).put("planned",json(c.getString(11))).put("animal_name",c.isNull(12)?(c.isNull(13)?JSONObject.NULL:c.getString(13)):c.getString(12)).put("group_name",nullable(c,13)).put("is_overdue","pending".equals(status)&&day.isBefore(today)).put("is_today","pending".equals(status)&&day.equals(today)).put("is_upcoming","pending".equals(status)&&day.isAfter(today));out.put(o);}}return out;}

    private JSONArray eventsJson(SQLiteDatabase db,Long animalFilter,int limit)throws Exception{JSONArray out=new JSONArray();String where=animalFilter==null?"":" AND e.animal_id=?";List<String> params=new ArrayList<>();if(animalFilter!=null)params.add(String.valueOf(animalFilter));params.add(String.valueOf(limit));String sql="SELECT e.id,e.animal_id,a.name,e.type,e.occurred_at,e.title,e.notes,e.value,e.unit,e.medication_name,e.route,e.correction_of_id,e.data_json,e.created_at FROM events e JOIN animals a ON a.id=e.animal_id WHERE 1=1"+where+" ORDER BY e.occurred_at DESC,e.created_at DESC,e.id DESC LIMIT ?";try(Cursor c=db.rawQuery(sql,params.toArray(new String[0]))){while(c.moveToNext()){JSONObject data=json(c.getString(12));if(!c.isNull(9)&&!data.has("medication_name"))data.put("medication_name",c.getString(9));if(!c.isNull(10)&&!data.has("route"))data.put("route",c.getString(10));out.put(new JSONObject().put("id",eventId(c.getLong(0))).put("animal_id",animalId(c.getLong(1))).put("animal_name",c.getString(2)).put("event_type",c.getString(3)).put("occurred_at",iso(c.getLong(4))).put("title",c.getString(5)).put("notes",nullable(c,6)).put("value",c.isNull(7)?JSONObject.NULL:c.getDouble(7)).put("unit",nullable(c,8)).put("correction_of_event_id",c.isNull(11)?JSONObject.NULL:eventId(c.getLong(11))).put("data",data).put("created_at",iso(c.getLong(13))));}}return out;}

    private JSONObject attachmentJson(SQLiteDatabase db,long id)throws Exception{try(Cursor c=db.rawQuery("SELECT id,animal_id,event_id,filename,media_type,title,size_bytes,created_at FROM attachments WHERE id=?",args(id))){if(!c.moveToFirst())throw new IllegalArgumentException("Anhang nicht gefunden");return new JSONObject().put("id",attachmentId(id)).put("animal_id",c.isNull(1)?JSONObject.NULL:animalId(c.getLong(1))).put("event_id",c.isNull(2)?JSONObject.NULL:eventId(c.getLong(2))).put("filename",c.getString(3)).put("media_type",c.getString(4)).put("title",nullable(c,5)).put("size_bytes",c.getLong(6)).put("created_at",iso(c.getLong(7))).put("url","https://app.local/attachment/"+attachmentId(id));}}

    public synchronized byte[] attachmentBytes(String publicId){long id=attachmentPk(publicId);try(Cursor c=getReadableDatabase().rawQuery("SELECT content FROM attachments WHERE id=?",args(id))){return c.moveToFirst()?c.getBlob(0):null;}}
    public synchronized String attachmentMediaType(String publicId){long id=attachmentPk(publicId);try(Cursor c=getReadableDatabase().rawQuery("SELECT media_type FROM attachments WHERE id=?",args(id))){return c.moveToFirst()?c.getString(0):"application/octet-stream";}}
    public synchronized String exportJson(){try{return exportJsonObject().toString(2);}catch(Exception error){return "{}";}}
    public synchronized JSONObject exportJsonObject()throws Exception{return new JSONObject().put("format","animal-health-standalone").put("version",VERSION).put("exported_at",Instant.now().toString()).put("dashboard",dashboard()).put("features",features()).put("v080",v080State()).put("v081",v081State()).put("v083",v083State()).put("v0817",v0817State());}

    private JSONArray assetItems(String filename)throws Exception{try(InputStream in=context.getAssets().open(filename)){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))>0)out.write(buffer,0,n);JSONObject root=new JSONObject(out.toString(StandardCharsets.UTF_8));return root.optJSONArray("items")!=null?root.optJSONArray("items"):new JSONArray();}}
    private static JSONArray combine(JSONArray a,JSONArray b)throws Exception{JSONArray out=new JSONArray();for(int i=0;i<a.length();i++)out.put(a.get(i));for(int i=0;i<b.length();i++)out.put(b.get(i));return out;}
    private static String nameOf(JSONObject o){return o.optString("name",o.optString("name_de",o.optString("name_en",o.optString("id",""))));}
    private static JSONArray arr(Object...items){JSONArray a=new JSONArray();for(Object item:items)a.put(item);return a;}
    private static JSONObject json(String text){try{return new JSONObject(text==null||text.isBlank()?"{}":text);}catch(Exception ignored){return new JSONObject();}}
    private static List<String> keys(JSONObject o){List<String> keys=new ArrayList<>();o.keys().forEachRemaining(keys::add);return keys;}
    private static Double numberOrNull(JSONObject o,String key){return o.has(key)&&!o.isNull(key)?o.optDouble(key):null;}
    private static String required(JSONObject p,String key)throws Exception{String v=p.optString(key,"").trim();if(v.isEmpty())throw new IllegalArgumentException(key+" ist erforderlich");return v;}
    private static String empty(String v){if(v==null)return null;String x=v.trim();return x.isEmpty()?null:x;}
    private static void put(ContentValues v,String key,String value){if(value==null||value.trim().isEmpty())v.putNull(key);else v.put(key,value.trim());}
    private static Object nullable(Cursor c,int index){return c.isNull(index)?JSONObject.NULL:c.getString(index);}
    private static String[] args(long value){return new String[]{String.valueOf(value)};}
    private static String iso(long ms){return Instant.ofEpochMilli(ms).toString();}
    private static String localIso(long ms){return Instant.ofEpochMilli(ms).atZone(ZoneId.systemDefault()).toLocalDateTime().toString();}
    private static LocalDate parseDate(String value,LocalDate fallback){try{return value==null||value.isBlank()?fallback:LocalDate.parse(value);}catch(Exception error){return fallback;}}
    private static long parseDateTime(String value,long fallback){if(value==null||value.isBlank())return fallback;try{return Instant.parse(value).toEpochMilli();}catch(Exception ignored){}try{return LocalDateTime.parse(value).atZone(ZoneId.systemDefault()).toInstant().toEpochMilli();}catch(Exception ignored){}try{return LocalDate.parse(value).atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli();}catch(Exception ignored){}return fallback;}
    private static long localDateTimeMillis(String date,String time){LocalDate d=parseDate(date,LocalDate.now());LocalTime t=LocalTime.MIDNIGHT;try{if(time!=null&&!time.isBlank())t=LocalTime.parse(time);}catch(Exception ignored){}return ZonedDateTime.of(d,t,ZoneId.systemDefault()).toInstant().toEpochMilli();}
    private static double weightKg(double value,String unit){if("g".equals(unit))return value/1000.0;if("mg".equals(unit))return value/1_000_000.0;return value;}
    private static int count(SQLiteDatabase db,String table){try(Cursor c=db.rawQuery("SELECT COUNT(*) FROM "+table,null)){return c.moveToFirst()?c.getInt(0):0;}}
    private static String setting(SQLiteDatabase db,String key,String fallback){try(Cursor c=db.rawQuery("SELECT value FROM settings WHERE key=?",new String[]{key})){return c.moveToFirst()&&!c.isNull(0)?c.getString(0):fallback;}}
    private static void setSetting(SQLiteDatabase db,String key,String value){ContentValues v=new ContentValues();v.put("key",key);v.put("value",value);db.insertWithOnConflict("settings",null,v,SQLiteDatabase.CONFLICT_REPLACE);}

    private static long pk(String value){if(value==null)throw new IllegalArgumentException("ID fehlt");String digits=value.replaceAll("[^0-9]","");if(digits.isEmpty())throw new IllegalArgumentException("Ungültige ID: "+value);return Long.parseLong(digits);}
    private static long animalPk(String id){return pk(id);} private static long devicePk(String id){return pk(id);} private static long groupPk(String id){return pk(id);} private static long tagPk(String id){return pk(id);} private static long eventPk(String id){return pk(id);} private static long taskPk(String id){return pk(id);} private static long occurrencePk(String id){return pk(id);} private static long attachmentPk(String id){return pk(id);}
    private static String animalId(long id){return "AH-A"+id;} private static String deviceId(long id){return "android-animal-"+id;} private static String groupId(long id){return "GR-A"+id;} private static String tagId(long id){return "TG-A"+id;} private static String eventId(long id){return "EV-A"+id;} private static String taskId(long id){return "TK-A"+id;} private static String occurrenceId(long id){return "OC-A"+id;} private static String attachmentId(long id){return "AT-A"+id;}
}
