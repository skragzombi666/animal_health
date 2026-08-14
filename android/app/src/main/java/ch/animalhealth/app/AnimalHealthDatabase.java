package ch.animalhealth.app;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public final class AnimalHealthDatabase extends SQLiteOpenHelper {
    private static final String DB_NAME = "animal_health_android.db";
    private static final int DB_VERSION = 1;

    public static final class Animal {
        public long id;
        public String name;
        public String species;
        public String breed;
        public String color;
        public String sex;
    }

    public static final class Event {
        public long id;
        public long animalId;
        public String animalName;
        public String type;
        public long occurredAt;
        public String title;
        public String notes;
        public Double value;
        public String unit;
        public String medicationName;
        public String route;
        public Long correctionOfId;
        public String batchId;
    }

    public static final class Task {
        public long id;
        public Long animalId;
        public String animalName;
        public String title;
        public long dueAt;
        public String kind;
        public boolean done;
    }

    public static final class MedicationPreset {
        public long id;
        public String name;
        public String species;
        public String defaultUnit;
        public String defaultRoute;
    }

    public static final class MedicationInput {
        public String name;
        public double dose;
        public String unit;
        public String route;
        public String notes;

        public MedicationInput(String name, double dose, String unit, String route, String notes) {
            this.name = name;
            this.dose = dose;
            this.unit = unit;
            this.route = route;
            this.notes = notes;
        }
    }

    public AnimalHealthDatabase(Context context) {
        super(context, DB_NAME, null, DB_VERSION);
    }

    @Override
    public void onCreate(SQLiteDatabase db) {
        db.execSQL("CREATE TABLE animals (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, species TEXT NOT NULL, breed TEXT, color TEXT, sex TEXT, created_at INTEGER NOT NULL)");
        db.execSQL("CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE, type TEXT NOT NULL, occurred_at INTEGER NOT NULL, title TEXT NOT NULL, notes TEXT, value REAL, unit TEXT, medication_name TEXT, route TEXT, correction_of_id INTEGER REFERENCES events(id), batch_id TEXT, created_at INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX idx_events_animal_time ON events(animal_id, occurred_at DESC)");
        db.execSQL("CREATE INDEX idx_events_correction ON events(correction_of_id)");
        db.execSQL("CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, animal_id INTEGER REFERENCES animals(id) ON DELETE CASCADE, title TEXT NOT NULL, due_at INTEGER NOT NULL, kind TEXT NOT NULL DEFAULT 'reminder', done INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL)");
        db.execSQL("CREATE INDEX idx_tasks_due ON tasks(done, due_at)");
        db.execSQL("CREATE TABLE medications (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE COLLATE NOCASE, species TEXT, default_unit TEXT, default_route TEXT, created_at INTEGER NOT NULL)");
    }

    @Override
    public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
    }

    @Override
    public void onConfigure(SQLiteDatabase db) {
        super.onConfigure(db);
        db.setForeignKeyConstraintsEnabled(true);
    }

    public long addAnimal(String name, String species, String breed, String color, String sex) {
        ContentValues values = new ContentValues();
        values.put("name", name.trim());
        values.put("species", species.trim());
        values.put("breed", clean(breed));
        values.put("color", clean(color));
        values.put("sex", clean(sex));
        values.put("created_at", System.currentTimeMillis());
        return getWritableDatabase().insertOrThrow("animals", null, values);
    }

    public List<Animal> animals() {
        List<Animal> result = new ArrayList<>();
        try (Cursor cursor = getReadableDatabase().rawQuery("SELECT id,name,species,breed,color,sex FROM animals ORDER BY name COLLATE NOCASE", null)) {
            while (cursor.moveToNext()) result.add(animal(cursor));
        }
        return result;
    }

    public Animal animal(long id) {
        try (Cursor cursor = getReadableDatabase().rawQuery("SELECT id,name,species,breed,color,sex FROM animals WHERE id=?", new String[]{String.valueOf(id)})) {
            return cursor.moveToFirst() ? animal(cursor) : null;
        }
    }

    public long addWeight(long animalId, double value, String unit, long occurredAt, String notes) {
        return insertEvent(getWritableDatabase(), animalId, "weight", occurredAt, "Gewicht", notes, value, unit, null, null, null, null);
    }

    public int addMedicationBatch(long animalId, long occurredAt, List<MedicationInput> inputs, String commonNotes) {
        SQLiteDatabase db = getWritableDatabase();
        String batchId = UUID.randomUUID().toString();
        db.beginTransaction();
        try {
            for (MedicationInput input : inputs) {
                String notes = joinNotes(commonNotes, input.notes);
                insertEvent(db, animalId, "medication", occurredAt, input.name, notes, input.dose, input.unit, input.name, input.route, null, batchId);
            }
            db.setTransactionSuccessful();
            return inputs.size();
        } finally {
            db.endTransaction();
        }
    }

    public long correctMedication(long sourceEventId, long animalId, long occurredAt, MedicationInput input) {
        return insertEvent(getWritableDatabase(), animalId, "medication", occurredAt, input.name, input.notes, input.dose, input.unit, input.name, input.route, sourceEventId, UUID.randomUUID().toString());
    }

    public long addGeneralEvent(long animalId, String type, String title, long occurredAt, String notes) {
        return insertEvent(getWritableDatabase(), animalId, type, occurredAt, title, notes, null, null, null, null, null, null);
    }

    private long insertEvent(SQLiteDatabase db, long animalId, String type, long occurredAt, String title, String notes, Double value, String unit, String medicationName, String route, Long correctionOfId, String batchId) {
        if (animal(animalId) == null) throw new IllegalArgumentException("Tier nicht gefunden");
        ContentValues values = new ContentValues();
        values.put("animal_id", animalId);
        values.put("type", type);
        values.put("occurred_at", occurredAt);
        values.put("title", title.trim());
        values.put("notes", clean(notes));
        if (value != null) values.put("value", value); else values.putNull("value");
        values.put("unit", clean(unit));
        values.put("medication_name", clean(medicationName));
        values.put("route", clean(route));
        if (correctionOfId != null) values.put("correction_of_id", correctionOfId); else values.putNull("correction_of_id");
        values.put("batch_id", clean(batchId));
        values.put("created_at", System.currentTimeMillis());
        return db.insertOrThrow("events", null, values);
    }

    public List<Event> events() {
        return queryEvents("", new String[0]);
    }

    public List<Event> eventsForAnimal(long animalId) {
        return queryEvents("AND e.animal_id=?", new String[]{String.valueOf(animalId)});
    }

    public List<Event> eventsBetween(long startInclusive, long endExclusive) {
        return queryEvents("AND e.occurred_at>=? AND e.occurred_at<?", new String[]{String.valueOf(startInclusive), String.valueOf(endExclusive)});
    }

    public Event event(long eventId) {
        String sql = eventSelect() + " WHERE e.id=?";
        try (Cursor cursor = getReadableDatabase().rawQuery(sql, new String[]{String.valueOf(eventId)})) {
            return cursor.moveToFirst() ? event(cursor) : null;
        }
    }

    private List<Event> queryEvents(String extraWhere, String[] args) {
        List<Event> result = new ArrayList<>();
        String sql = eventSelect() + " WHERE NOT EXISTS (SELECT 1 FROM events c WHERE c.correction_of_id=e.id) " + extraWhere + " ORDER BY e.occurred_at DESC,e.created_at DESC,e.id DESC";
        try (Cursor cursor = getReadableDatabase().rawQuery(sql, args)) {
            while (cursor.moveToNext()) result.add(event(cursor));
        }
        return result;
    }

    private String eventSelect() {
        return "SELECT e.id,e.animal_id,a.name,e.type,e.occurred_at,e.title,e.notes,e.value,e.unit,e.medication_name,e.route,e.correction_of_id,e.batch_id FROM events e JOIN animals a ON a.id=e.animal_id";
    }

    public long addTask(Long animalId, String title, long dueAt, String kind) {
        ContentValues values = new ContentValues();
        if (animalId != null) values.put("animal_id", animalId); else values.putNull("animal_id");
        values.put("title", title.trim());
        values.put("due_at", dueAt);
        values.put("kind", clean(kind) == null ? "reminder" : kind);
        values.put("done", 0);
        values.put("created_at", System.currentTimeMillis());
        return getWritableDatabase().insertOrThrow("tasks", null, values);
    }

    public void completeTask(long taskId) {
        ContentValues values = new ContentValues();
        values.put("done", 1);
        getWritableDatabase().update("tasks", values, "id=?", new String[]{String.valueOf(taskId)});
    }

    public List<Task> tasks(boolean includeDone) {
        List<Task> result = new ArrayList<>();
        String where = includeDone ? "" : "WHERE t.done=0";
        String sql = "SELECT t.id,t.animal_id,a.name,t.title,t.due_at,t.kind,t.done FROM tasks t LEFT JOIN animals a ON a.id=t.animal_id " + where + " ORDER BY t.done,t.due_at,t.id";
        try (Cursor cursor = getReadableDatabase().rawQuery(sql, null)) {
            while (cursor.moveToNext()) {
                Task task = new Task();
                task.id = cursor.getLong(0);
                task.animalId = cursor.isNull(1) ? null : cursor.getLong(1);
                task.animalName = cursor.isNull(2) ? null : cursor.getString(2);
                task.title = cursor.getString(3);
                task.dueAt = cursor.getLong(4);
                task.kind = cursor.getString(5);
                task.done = cursor.getInt(6) != 0;
                result.add(task);
            }
        }
        return result;
    }

    public void upsertMedicationPreset(String name, String species, String unit, String route) {
        ContentValues values = new ContentValues();
        values.put("name", name.trim());
        values.put("species", clean(species));
        values.put("default_unit", clean(unit));
        values.put("default_route", clean(route));
        values.put("created_at", System.currentTimeMillis());
        getWritableDatabase().insertWithOnConflict("medications", null, values, SQLiteDatabase.CONFLICT_REPLACE);
    }

    public List<MedicationPreset> medicationPresets() {
        List<MedicationPreset> result = new ArrayList<>();
        try (Cursor cursor = getReadableDatabase().rawQuery("SELECT id,name,species,default_unit,default_route FROM medications ORDER BY name COLLATE NOCASE", null)) {
            while (cursor.moveToNext()) {
                MedicationPreset preset = new MedicationPreset();
                preset.id = cursor.getLong(0);
                preset.name = cursor.getString(1);
                preset.species = cursor.isNull(2) ? null : cursor.getString(2);
                preset.defaultUnit = cursor.isNull(3) ? null : cursor.getString(3);
                preset.defaultRoute = cursor.isNull(4) ? null : cursor.getString(4);
                result.add(preset);
            }
        }
        return result;
    }

    public MedicationPreset medicationPreset(String name) {
        try (Cursor cursor = getReadableDatabase().rawQuery("SELECT id,name,species,default_unit,default_route FROM medications WHERE name=? COLLATE NOCASE", new String[]{name})) {
            if (!cursor.moveToFirst()) return null;
            MedicationPreset preset = new MedicationPreset();
            preset.id = cursor.getLong(0);
            preset.name = cursor.getString(1);
            preset.species = cursor.isNull(2) ? null : cursor.getString(2);
            preset.defaultUnit = cursor.isNull(3) ? null : cursor.getString(3);
            preset.defaultRoute = cursor.isNull(4) ? null : cursor.getString(4);
            return preset;
        }
    }

    public String exportJson() throws JSONException {
        JSONObject root = new JSONObject();
        root.put("format", "animal-health-android-alpha");
        root.put("version", "0.9.0-alpha.1");
        root.put("exported_at", System.currentTimeMillis());
        JSONArray animalsJson = new JSONArray();
        for (Animal item : animals()) {
            JSONObject o = new JSONObject();
            o.put("id", item.id); o.put("name", item.name); o.put("species", item.species); o.put("breed", nullable(item.breed)); o.put("color", nullable(item.color)); o.put("sex", nullable(item.sex));
            animalsJson.put(o);
        }
        root.put("animals", animalsJson);
        JSONArray eventsJson = new JSONArray();
        try (Cursor c = getReadableDatabase().rawQuery("SELECT id,animal_id,type,occurred_at,title,notes,value,unit,medication_name,route,correction_of_id,batch_id,created_at FROM events ORDER BY occurred_at,id", null)) {
            while (c.moveToNext()) {
                JSONObject o = new JSONObject();
                o.put("id", c.getLong(0)); o.put("animal_id", c.getLong(1)); o.put("type", c.getString(2)); o.put("occurred_at", c.getLong(3)); o.put("title", c.getString(4));
                o.put("notes", nullable(c.isNull(5) ? null : c.getString(5))); o.put("value", c.isNull(6) ? JSONObject.NULL : c.getDouble(6)); o.put("unit", nullable(c.isNull(7) ? null : c.getString(7)));
                o.put("medication_name", nullable(c.isNull(8) ? null : c.getString(8))); o.put("route", nullable(c.isNull(9) ? null : c.getString(9))); o.put("correction_of_id", c.isNull(10) ? JSONObject.NULL : c.getLong(10)); o.put("batch_id", nullable(c.isNull(11) ? null : c.getString(11))); o.put("created_at", c.getLong(12));
                eventsJson.put(o);
            }
        }
        root.put("events", eventsJson);
        JSONArray tasksJson = new JSONArray();
        for (Task task : tasks(true)) {
            JSONObject o = new JSONObject();
            o.put("id", task.id); o.put("animal_id", task.animalId == null ? JSONObject.NULL : task.animalId); o.put("title", task.title); o.put("due_at", task.dueAt); o.put("kind", task.kind); o.put("done", task.done);
            tasksJson.put(o);
        }
        root.put("tasks", tasksJson);
        JSONArray medsJson = new JSONArray();
        for (MedicationPreset preset : medicationPresets()) {
            JSONObject o = new JSONObject();
            o.put("name", preset.name); o.put("species", nullable(preset.species)); o.put("default_unit", nullable(preset.defaultUnit)); o.put("default_route", nullable(preset.defaultRoute));
            medsJson.put(o);
        }
        root.put("medications", medsJson);
        return root.toString(2);
    }

    private Animal animal(Cursor cursor) {
        Animal animal = new Animal();
        animal.id = cursor.getLong(0);
        animal.name = cursor.getString(1);
        animal.species = cursor.getString(2);
        animal.breed = cursor.isNull(3) ? null : cursor.getString(3);
        animal.color = cursor.isNull(4) ? null : cursor.getString(4);
        animal.sex = cursor.isNull(5) ? null : cursor.getString(5);
        return animal;
    }

    private Event event(Cursor cursor) {
        Event event = new Event();
        event.id = cursor.getLong(0);
        event.animalId = cursor.getLong(1);
        event.animalName = cursor.getString(2);
        event.type = cursor.getString(3);
        event.occurredAt = cursor.getLong(4);
        event.title = cursor.getString(5);
        event.notes = cursor.isNull(6) ? null : cursor.getString(6);
        event.value = cursor.isNull(7) ? null : cursor.getDouble(7);
        event.unit = cursor.isNull(8) ? null : cursor.getString(8);
        event.medicationName = cursor.isNull(9) ? null : cursor.getString(9);
        event.route = cursor.isNull(10) ? null : cursor.getString(10);
        event.correctionOfId = cursor.isNull(11) ? null : cursor.getLong(11);
        event.batchId = cursor.isNull(12) ? null : cursor.getString(12);
        return event;
    }

    private static String clean(String value) {
        if (value == null) return null;
        String text = value.trim();
        return text.isEmpty() ? null : text;
    }

    private static Object nullable(String value) {
        return value == null ? JSONObject.NULL : value;
    }

    private static String joinNotes(String common, String individual) {
        String a = clean(common); String b = clean(individual);
        if (a == null) return b;
        if (b == null) return a;
        return a + "\n" + b;
    }
}
