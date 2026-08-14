package ch.animalhealth.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public final class MainActivity extends Activity {
    private static final int BLUE = Color.rgb(37, 99, 235);
    private static final int BG = Color.rgb(245, 247, 248);
    private static final int CARD = Color.WHITE;
    private static final int TEXT = Color.rgb(31, 41, 55);
    private static final int MUTED = Color.rgb(107, 114, 128);
    private static final int BORDER = Color.rgb(226, 232, 240);
    private static final int EXPORT_REQUEST = 4817;
    private static final DateTimeFormatter INPUT_TIME = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm", Locale.GERMANY);
    private static final DateTimeFormatter DISPLAY_TIME = DateTimeFormatter.ofPattern("dd.MM.yyyy HH:mm", Locale.GERMANY);
    private static final DateTimeFormatter DISPLAY_DATE = DateTimeFormatter.ofPattern("dd.MM.yyyy", Locale.GERMANY);
    private static final String[] UNIT_VALUES = {"mcg", "mg", "g", "ul", "ml", "drop", "tablet", "dose"};
    private static final String[] UNIT_LABELS = {"µg", "mg", "g", "µl", "ml", "Tropfen", "Tablette", "Dosis"};

    private AnimalHealthDatabase db;
    private LinearLayout content;
    private String view = "overview";
    private Long detailAnimalId;
    private String pendingExport;

    private static final class MedicationRow {
        LinearLayout root;
        AutoCompleteTextView medication;
        EditText dose;
        Spinner unit;
        EditText route;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        db = new AnimalHealthDatabase(this);
        getWindow().setStatusBarColor(Color.WHITE);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR);
        buildShell();
        render();
    }

    @Override
    protected void onDestroy() {
        db.close();
        super.onDestroy();
    }

    private void buildShell() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(BG);

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(16), dp(12), dp(16), dp(10));
        header.setBackgroundColor(Color.WHITE);
        ImageView logo = new ImageView(this);
        logo.setImageResource(ch.animalhealth.app.R.drawable.ic_paw);
        header.addView(logo, new LinearLayout.LayoutParams(dp(38), dp(38)));
        LinearLayout titles = new LinearLayout(this);
        titles.setOrientation(LinearLayout.VERTICAL);
        titles.setPadding(dp(10), 0, 0, 0);
        TextView title = text("Animal Health", 20, true);
        TextView alpha = text("0.9.0-alpha.1 · Standalone Android", 11, false);
        alpha.setTextColor(BLUE);
        titles.addView(title);
        titles.addView(alpha);
        header.addView(titles, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        Button refresh = compactButton("↻");
        refresh.setOnClickListener(v -> render());
        header.addView(refresh);
        root.addView(header);

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(12), dp(12), dp(12), dp(20));
        scroll.addView(content);
        root.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));

        HorizontalScrollView navScroll = new HorizontalScrollView(this);
        navScroll.setHorizontalScrollBarEnabled(false);
        navScroll.setBackgroundColor(Color.WHITE);
        LinearLayout nav = new LinearLayout(this);
        nav.setOrientation(LinearLayout.HORIZONTAL);
        nav.setPadding(dp(6), dp(6), dp(6), dp(8));
        nav.addView(navButton("Übersicht", "overview"));
        nav.addView(navButton("Tiere", "animals"));
        nav.addView(navButton("Chronik", "timeline"));
        nav.addView(navButton("Aufgaben", "tasks"));
        nav.addView(navButton("Einstellungen", "settings"));
        navScroll.addView(nav);
        root.addView(navScroll);
        setContentView(root);
    }

    private Button navButton(String label, String target) {
        Button button = compactButton(label);
        button.setAllCaps(false);
        button.setOnClickListener(v -> {
            view = target;
            detailAnimalId = null;
            render();
        });
        return button;
    }

    private void render() {
        content.removeAllViews();
        if (detailAnimalId != null) {
            renderAnimalDetail(detailAnimalId);
            return;
        }
        switch (view) {
            case "animals" -> renderAnimals();
            case "timeline" -> renderTimeline();
            case "tasks" -> renderTasks();
            case "settings" -> renderSettings();
            default -> renderOverview();
        }
    }

    private void renderOverview() {
        addHeading("Übersicht", "Lokale Daten auf diesem Gerät");
        LinearLayout alpha = card();
        TextView badge = text("ANDROID ALPHA", 11, true);
        badge.setTextColor(BLUE);
        alpha.addView(badge);
        alpha.addView(text("Diese App funktioniert ohne Home Assistant. Die Daten bleiben lokal auf diesem Android-Gerät, bis du sie exportierst.", 14, false));
        content.addView(alpha);

        List<AnimalHealthDatabase.Animal> animals = db.animals();
        List<AnimalHealthDatabase.Task> tasks = db.tasks(false);
        List<AnimalHealthDatabase.Event> events = db.events();
        LinearLayout stats = new LinearLayout(this);
        stats.setOrientation(LinearLayout.HORIZONTAL);
        stats.addView(stat("Tiere", String.valueOf(animals.size())), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        stats.addView(stat("Offene Aufgaben", String.valueOf(tasks.size())), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        stats.addView(stat("Chronikeinträge", String.valueOf(events.size())), new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        content.addView(stats);

        LinearLayout quick = card();
        quick.addView(sectionTitle("Schnell erfassen"));
        LinearLayout row1 = horizontal();
        row1.addView(actionButton("Tier anlegen", v -> showAnimalDialog()), weighted());
        row1.addView(actionButton("Gewicht", v -> showWeightDialog(null)), weighted());
        quick.addView(row1);
        LinearLayout row2 = horizontal();
        row2.addView(actionButton("Medikament(e)", v -> showMedicationDialog(null, null, null)), weighted());
        row2.addView(actionButton("Aufgabe", v -> showTaskDialog()), weighted());
        quick.addView(row2);
        content.addView(quick);

        LinearLayout today = card();
        today.addView(sectionTitle("Heute relevant"));
        long endToday = LocalDate.now().plusDays(1).atStartOfDay(ZoneId.systemDefault()).toInstant().toEpochMilli();
        long now = System.currentTimeMillis();
        int shown = 0;
        for (AnimalHealthDatabase.Task task : tasks) {
            if (task.dueAt <= endToday) {
                today.addView(taskRow(task));
                shown++;
            }
        }
        if (shown == 0) today.addView(empty("Heute sind keine offenen Aufgaben fällig."));
        content.addView(today);

        LinearLayout recent = card();
        recent.addView(sectionTitle("Letzte Gesundheitsdaten"));
        if (events.isEmpty()) recent.addView(empty("Noch keine Gesundheitsdaten erfasst."));
        else for (int i = 0; i < Math.min(6, events.size()); i++) recent.addView(eventRow(events.get(i)));
        content.addView(recent);
    }

    private void renderAnimals() {
        addHeading("Tiere", "Stammdaten und Gesundheitschronik");
        Button add = primaryButton("+ Tier anlegen");
        add.setOnClickListener(v -> showAnimalDialog());
        content.addView(add);
        List<AnimalHealthDatabase.Animal> animals = db.animals();
        if (animals.isEmpty()) {
            content.addView(empty("Noch keine Tiere angelegt."));
            return;
        }
        for (AnimalHealthDatabase.Animal animal : animals) {
            LinearLayout item = card();
            TextView name = text(animal.name, 18, true);
            item.addView(name);
            String meta = animal.species + (animal.breed == null ? "" : " · " + animal.breed);
            TextView info = text(meta, 13, false);
            info.setTextColor(MUTED);
            item.addView(info);
            item.setClickable(true);
            item.setOnClickListener(v -> {
                detailAnimalId = animal.id;
                render();
            });
            content.addView(item);
        }
    }

    private void renderAnimalDetail(long animalId) {
        AnimalHealthDatabase.Animal animal = db.animal(animalId);
        if (animal == null) {
            detailAnimalId = null;
            renderAnimals();
            return;
        }
        Button back = compactButton("← Tiere");
        back.setOnClickListener(v -> {
            detailAnimalId = null;
            view = "animals";
            render();
        });
        content.addView(back);
        addHeading(animal.name, animal.species + (animal.breed == null ? "" : " · " + animal.breed));
        LinearLayout master = card();
        master.addView(sectionTitle("Stammdaten"));
        master.addView(keyValue("Tierart", animal.species));
        master.addView(keyValue("Rasse", animal.breed));
        master.addView(keyValue("Farbe", animal.color));
        master.addView(keyValue("Geschlecht", animal.sex));
        content.addView(master);

        LinearLayout quick = card();
        quick.addView(sectionTitle("Schnell erfassen"));
        LinearLayout row = horizontal();
        row.addView(actionButton("Gewicht", v -> showWeightDialog(animal.id)), weighted());
        row.addView(actionButton("Medikament(e)", v -> showMedicationDialog(animal.id, null, null)), weighted());
        quick.addView(row);
        content.addView(quick);

        LinearLayout history = card();
        history.addView(sectionTitle("Gesundheitschronik"));
        List<AnimalHealthDatabase.Event> events = db.eventsForAnimal(animal.id);
        if (events.isEmpty()) history.addView(empty("Noch keine Einträge."));
        else {
            String lastDay = null;
            for (AnimalHealthDatabase.Event event : events) {
                String day = dateKey(event.occurredAt);
                if (!day.equals(lastDay)) {
                    TextView header = text(formatDate(event.occurredAt), 14, true);
                    header.setTextColor(BLUE);
                    header.setPadding(0, dp(10), 0, dp(4));
                    history.addView(header);
                    lastDay = day;
                }
                history.addView(eventRow(event));
            }
        }
        content.addView(history);
    }

    private void renderTimeline() {
        addHeading("Chronik", "Neuester Eintrag zuerst · nach Tagen gruppiert");
        List<AnimalHealthDatabase.Event> events = db.events();
        if (events.isEmpty()) {
            content.addView(empty("Noch keine Gesundheitsdaten erfasst."));
            return;
        }
        Map<String, List<AnimalHealthDatabase.Event>> grouped = new LinkedHashMap<>();
        for (AnimalHealthDatabase.Event event : events) grouped.computeIfAbsent(dateKey(event.occurredAt), k -> new ArrayList<>()).add(event);
        for (Map.Entry<String, List<AnimalHealthDatabase.Event>> entry : grouped.entrySet()) {
            List<AnimalHealthDatabase.Event> dayEvents = entry.getValue();
            LinearLayout dayCard = card();
            Button day = compactButton(formatDate(dayEvents.get(0).occurredAt) + "  ·  " + daySummary(dayEvents));
            day.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
            day.setOnClickListener(v -> showDayDetail(dayEvents));
            dayCard.addView(day);
            for (AnimalHealthDatabase.Event event : dayEvents) dayCard.addView(eventRow(event));
            content.addView(dayCard);
        }
    }

    private void renderTasks() {
        addHeading("Aufgaben", "Einfache lokale Erinnerungen für die Android-Alpha");
        Button add = primaryButton("+ Aufgabe anlegen");
        add.setOnClickListener(v -> showTaskDialog());
        content.addView(add);
        List<AnimalHealthDatabase.Task> tasks = db.tasks(true);
        if (tasks.isEmpty()) {
            content.addView(empty("Noch keine Aufgaben angelegt."));
            return;
        }
        LinearLayout open = card();
        open.addView(sectionTitle("Offen"));
        int openCount = 0;
        for (AnimalHealthDatabase.Task task : tasks) {
            if (!task.done) {
                open.addView(taskRow(task));
                openCount++;
            }
        }
        if (openCount == 0) open.addView(empty("Keine offenen Aufgaben."));
        content.addView(open);
        LinearLayout done = card();
        done.addView(sectionTitle("Erledigt"));
        int doneCount = 0;
        for (AnimalHealthDatabase.Task task : tasks) {
            if (task.done) {
                TextView t = text("✓ " + task.title + " · " + formatDateTime(task.dueAt), 13, false);
                t.setTextColor(MUTED);
                t.setPadding(0, dp(6), 0, dp(6));
                done.addView(t);
                doneCount++;
            }
        }
        if (doneCount == 0) done.addView(empty("Noch keine erledigten Aufgaben."));
        content.addView(done);
    }

    private void renderSettings() {
        addHeading("Einstellungen", "Standalone Android Alpha");
        LinearLayout medCard = card();
        medCard.addView(sectionTitle("Medikamente verwalten"));
        medCard.addView(text("Eigene Präparate können mit einer bevorzugten Dosiseinheit und einem Standard-Applikationsweg hinterlegt werden.", 13, false));
        Button addMed = primaryButton("+ Medikament hinzufügen");
        addMed.setOnClickListener(v -> showMedicationPresetDialog());
        medCard.addView(addMed);
        List<AnimalHealthDatabase.MedicationPreset> presets = db.medicationPresets();
        if (presets.isEmpty()) medCard.addView(empty("Noch keine eigenen Medikamente hinterlegt."));
        else for (AnimalHealthDatabase.MedicationPreset preset : presets) {
            String detail = unitLabel(preset.defaultUnit) + (preset.defaultRoute == null ? "" : " · " + preset.defaultRoute) + (preset.species == null ? "" : " · " + preset.species);
            medCard.addView(keyValue(preset.name, detail));
        }
        content.addView(medCard);

        LinearLayout offLabel = card();
        offLabel.addView(sectionTitle("Off-Label-Auswahl"));
        Switch toggle = new Switch(this);
        toggle.setText("Off-Label-Katalogfilter aktivieren");
        toggle.setEnabled(false);
        offLabel.addView(toggle);
        TextView hint = text("In der ersten Standalone-Alpha wird noch kein zentraler Zulassungskatalog ausgeliefert. Deshalb gibt es hier noch keinen Off-Label-Filter; eigene Medikamente bleiben frei erfassbar.", 13, false);
        hint.setTextColor(MUTED);
        offLabel.addView(hint);
        content.addView(offLabel);

        LinearLayout data = card();
        data.addView(sectionTitle("Daten"));
        data.addView(text("Die Datenbank liegt ausschließlich im App-Speicher. Für Tests kannst du jederzeit einen vollständigen JSON-Export erzeugen.", 13, false));
        Button export = primaryButton("JSON exportieren");
        export.setOnClickListener(v -> exportJson());
        data.addView(export);
        content.addView(data);

        LinearLayout info = card();
        info.addView(sectionTitle("Alpha-Hinweis"));
        info.addView(text("Version 0.9.0-alpha.1 ist für frühe Feldtests gedacht. Noch nicht alle Funktionen der Home-Assistant-Integration sind in der Standalone-App enthalten.", 13, false));
        info.addView(text("Paket: ch.animalhealth.app.alpha", 11, false));
        content.addView(info);
    }

    private View taskRow(AnimalHealthDatabase.Task task) {
        LinearLayout row = horizontal();
        row.setPadding(0, dp(6), 0, dp(6));
        LinearLayout texts = new LinearLayout(this);
        texts.setOrientation(LinearLayout.VERTICAL);
        texts.addView(text(task.title, 14, true));
        String animal = task.animalName == null ? "Allgemein" : task.animalName;
        TextView meta = text(animal + " · " + formatDateTime(task.dueAt), 12, false);
        meta.setTextColor(task.dueAt < System.currentTimeMillis() ? Color.rgb(185, 28, 28) : MUTED);
        texts.addView(meta);
        row.addView(texts, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        if (!task.done) {
            Button done = compactButton("Erledigt");
            done.setOnClickListener(v -> {
                db.completeTask(task.id);
                render();
            });
            row.addView(done);
        }
        return row;
    }

    private View eventRow(AnimalHealthDatabase.Event event) {
        LinearLayout row = horizontal();
        row.setPadding(0, dp(7), 0, dp(7));
        TextView icon = text(eventIcon(event.type), 18, false);
        icon.setGravity(Gravity.CENTER);
        row.addView(icon, new LinearLayout.LayoutParams(dp(32), dp(36)));
        LinearLayout main = new LinearLayout(this);
        main.setOrientation(LinearLayout.VERTICAL);
        main.addView(text(eventPrimary(event), 14, true));
        TextView meta = text(event.animalName + " · " + formatTime(event.occurredAt), 12, false);
        meta.setTextColor(MUTED);
        main.addView(meta);
        if (event.notes != null) {
            TextView note = text(event.notes, 12, false);
            note.setTextColor(MUTED);
            main.addView(note);
        }
        row.addView(main, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.setClickable(true);
        row.setOnClickListener(v -> showEventDetail(event));
        return row;
    }

    private String eventPrimary(AnimalHealthDatabase.Event event) {
        if ("medication".equals(event.type) && event.value != null) return number(event.value) + " " + unitLabel(event.unit) + " " + (event.medicationName == null ? event.title : event.medicationName);
        if ("weight".equals(event.type) && event.value != null) return number(event.value) + " " + unitLabel(event.unit) + " · Gewicht";
        return event.title;
    }

    private void showAnimalDialog() {
        LinearLayout form = dialogForm();
        EditText name = field("Name", false);
        EditText species = field("Tierart", false);
        EditText breed = field("Rasse (optional)", false);
        EditText color = field("Farbe (optional)", false);
        Spinner sex = spinner(new String[]{"–", "Weiblich", "Männlich", "Andere"});
        form.addView(labeled("Name", name));
        form.addView(labeled("Tierart", species));
        form.addView(labeled("Rasse", breed));
        form.addView(labeled("Farbe", color));
        form.addView(labeled("Geschlecht", sex));
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Tier anlegen").setView(wrapDialog(form)).setNegativeButton("Abbrechen", null).setPositiveButton("Speichern", null).create();
        dialog.setOnShowListener(x -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            if (name.getText().toString().trim().isEmpty() || species.getText().toString().trim().isEmpty()) {
                toast("Name und Tierart sind erforderlich.");
                return;
            }
            String sexValue = switch (sex.getSelectedItemPosition()) { case 1 -> "female"; case 2 -> "male"; case 3 -> "other"; default -> null; };
            long id = db.addAnimal(name.getText().toString(), species.getText().toString(), breed.getText().toString(), color.getText().toString(), sexValue);
            dialog.dismiss();
            detailAnimalId = id;
            view = "animals";
            render();
        }));
        dialog.show();
    }

    private void showWeightDialog(Long preselectedAnimalId) {
        List<AnimalHealthDatabase.Animal> animals = db.animals();
        if (animals.isEmpty()) {
            toast("Bitte zuerst ein Tier anlegen.");
            return;
        }
        LinearLayout form = dialogForm();
        Spinner animal = animalSpinner(animals, preselectedAnimalId);
        EditText weight = field("z. B. 1,25", true);
        Spinner unit = spinner(new String[]{"kg", "g", "mg"});
        EditText occurred = field("yyyy-MM-dd HH:mm", false);
        occurred.setText(nowText());
        EditText notes = field("Notiz (optional)", false);
        form.addView(labeled("Tier", animal));
        LinearLayout doseRow = horizontal();
        doseRow.addView(weight, weighted());
        doseRow.addView(unit, new LinearLayout.LayoutParams(dp(100), ViewGroup.LayoutParams.WRAP_CONTENT));
        form.addView(labeled("Gewicht", doseRow));
        form.addView(labeled("Zeitpunkt", occurred));
        form.addView(labeled("Notiz", notes));
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Gewicht erfassen").setView(wrapDialog(form)).setNegativeButton("Abbrechen", null).setPositiveButton("Speichern", null).create();
        dialog.setOnShowListener(x -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            Double value = positiveNumber(weight.getText().toString());
            Long time = parseTime(occurred.getText().toString());
            if (value == null || time == null) {
                toast("Gewicht und Zeitpunkt prüfen.");
                return;
            }
            AnimalHealthDatabase.Animal selected = animals.get(animal.getSelectedItemPosition());
            db.addWeight(selected.id, value, unit.getSelectedItem().toString(), time, notes.getText().toString());
            dialog.dismiss();
            render();
        }));
        dialog.show();
    }

    private void showMedicationDialog(Long preselectedAnimalId, List<AnimalHealthDatabase.MedicationInput> prefills, AnimalHealthDatabase.Event correction) {
        List<AnimalHealthDatabase.Animal> animals = db.animals();
        if (animals.isEmpty()) {
            toast("Bitte zuerst ein Tier anlegen.");
            return;
        }
        LinearLayout outer = dialogForm();
        Spinner animal = animalSpinner(animals, preselectedAnimalId);
        EditText occurred = field("yyyy-MM-dd HH:mm", false);
        occurred.setText(nowText());
        EditText commonNotes = field("Gemeinsame Notiz (optional)", false);
        outer.addView(labeled("Tier", animal));
        outer.addView(labeled("Datum / Zeit", occurred));
        outer.addView(labeled("Notiz", commonNotes));
        TextView medsTitle = text(correction == null ? "Medikamente" : "Korrigierte Medikamentengabe", 14, true);
        medsTitle.setPadding(0, dp(8), 0, dp(4));
        outer.addView(medsTitle);
        LinearLayout rowsContainer = new LinearLayout(this);
        rowsContainer.setOrientation(LinearLayout.VERTICAL);
        outer.addView(rowsContainer);
        List<MedicationRow> rows = new ArrayList<>();
        if (prefills == null || prefills.isEmpty()) addMedicationRow(rowsContainer, rows, null, correction != null);
        else for (AnimalHealthDatabase.MedicationInput input : prefills) addMedicationRow(rowsContainer, rows, input, correction != null);
        if (correction == null) {
            Button add = compactButton("+ Weiteres Medikament");
            add.setOnClickListener(v -> addMedicationRow(rowsContainer, rows, null, false));
            outer.addView(add);
        }
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle(correction == null ? "Medikament(e) dokumentieren" : "Medikamentengabe bearbeiten").setView(wrapDialog(outer)).setNegativeButton("Abbrechen", null).setPositiveButton("Speichern", null).create();
        dialog.setOnShowListener(x -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            Long time = parseTime(occurred.getText().toString());
            if (time == null) {
                toast("Zeitpunkt prüfen.");
                return;
            }
            List<AnimalHealthDatabase.MedicationInput> inputs = readMedicationRows(rows);
            if (inputs == null || inputs.isEmpty()) return;
            AnimalHealthDatabase.Animal selected = animals.get(animal.getSelectedItemPosition());
            if (correction != null) {
                if (inputs.size() != 1) {
                    toast("Eine Korrektur umfasst genau eine Gabe.");
                    return;
                }
                AnimalHealthDatabase.MedicationInput input = inputs.get(0);
                input.notes = commonNotes.getText().toString();
                db.correctMedication(correction.id, selected.id, time, input);
            } else {
                db.addMedicationBatch(selected.id, time, inputs, commonNotes.getText().toString());
            }
            dialog.dismiss();
            render();
        }));
        dialog.show();
    }

    private void addMedicationRow(LinearLayout container, List<MedicationRow> rows, AnimalHealthDatabase.MedicationInput prefill, boolean correction) {
        MedicationRow row = new MedicationRow();
        row.root = new LinearLayout(this);
        row.root.setOrientation(LinearLayout.VERTICAL);
        row.root.setPadding(0, dp(8), 0, dp(8));
        row.root.setBackgroundColor(Color.rgb(248, 250, 252));
        List<String> names = new ArrayList<>();
        for (AnimalHealthDatabase.MedicationPreset preset : db.medicationPresets()) names.add(preset.name);
        row.medication = new AutoCompleteTextView(this);
        row.medication.setHint("Medikament");
        row.medication.setSingleLine(true);
        row.medication.setThreshold(0);
        row.medication.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_dropdown_item_1line, names));
        row.medication.setOnClickListener(v -> row.medication.showDropDown());
        row.dose = field("Dosis", true);
        row.unit = spinner(UNIT_LABELS);
        row.route = field("Applikationsweg (optional)", false);
        LinearLayout doseLine = horizontal();
        doseLine.addView(row.dose, weighted());
        doseLine.addView(row.unit, new LinearLayout.LayoutParams(dp(125), ViewGroup.LayoutParams.WRAP_CONTENT));
        row.root.addView(row.medication);
        row.root.addView(doseLine);
        row.root.addView(row.route);
        if (!correction) {
            Button remove = compactButton("Entfernen");
            remove.setOnClickListener(v -> {
                if (rows.size() <= 1) {
                    toast("Mindestens eine Medikamentengabe bleibt erforderlich.");
                    return;
                }
                rows.remove(row);
                container.removeView(row.root);
            });
            row.root.addView(remove);
        }
        row.medication.setOnItemClickListener((parent, view, position, id) -> applyPreset(row));
        row.medication.setOnFocusChangeListener((v, hasFocus) -> {
            if (!hasFocus) applyPreset(row);
        });
        if (prefill != null) {
            row.medication.setText(prefill.name, false);
            row.dose.setText(number(prefill.dose));
            setUnit(row.unit, prefill.unit);
            if (prefill.route != null) row.route.setText(prefill.route);
        }
        rows.add(row);
        container.addView(row.root);
    }

    private void applyPreset(MedicationRow row) {
        String name = row.medication.getText().toString().trim();
        if (name.isEmpty()) return;
        AnimalHealthDatabase.MedicationPreset preset = db.medicationPreset(name);
        if (preset != null) {
            if (preset.defaultUnit != null) setUnit(row.unit, preset.defaultUnit);
            if (preset.defaultRoute != null && row.route.getText().toString().trim().isEmpty()) row.route.setText(preset.defaultRoute);
            return;
        }
        String lower = name.toLowerCase(Locale.ROOT);
        if (lower.contains("tablett")) setUnit(row.unit, "tablet");
        else if (lower.contains("tropf")) setUnit(row.unit, "drop");
        else if (lower.contains("suspension") || lower.contains("lösung") || lower.contains("loesung") || lower.contains("liquid")) setUnit(row.unit, "ml");
    }

    private List<AnimalHealthDatabase.MedicationInput> readMedicationRows(List<MedicationRow> rows) {
        List<AnimalHealthDatabase.MedicationInput> result = new ArrayList<>();
        for (MedicationRow row : rows) {
            String name = row.medication.getText().toString().trim();
            Double dose = positiveNumber(row.dose.getText().toString());
            if (name.isEmpty() || dose == null) {
                toast("Bei jeder Gabe Medikament und positive Dosis angeben.");
                return null;
            }
            String unit = UNIT_VALUES[row.unit.getSelectedItemPosition()];
            result.add(new AnimalHealthDatabase.MedicationInput(name, dose, unit, row.route.getText().toString(), null));
        }
        return result;
    }

    private void showEventDetail(AnimalHealthDatabase.Event event) {
        LinearLayout body = dialogForm();
        body.addView(text(eventPrimary(event), 18, true));
        body.addView(keyValue("Tier", event.animalName));
        body.addView(keyValue("Zeitpunkt", formatDateTime(event.occurredAt)));
        body.addView(keyValue("Art", eventTypeLabel(event.type)));
        if (event.route != null) body.addView(keyValue("Applikationsweg", event.route));
        if (event.notes != null) body.addView(keyValue("Notiz", event.notes));
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Eintragsdetails").setView(wrapDialog(body)).setNegativeButton("Schließen", null).create();
        if ("medication".equals(event.type) && event.value != null) {
            dialog.setButton(AlertDialog.BUTTON_NEUTRAL, "", (d, which) -> {});
            LinearLayout actions = horizontal();
            Button repeat = compactButton("Nochmals verabreichen");
            repeat.setOnClickListener(v -> {
                dialog.dismiss();
                showMedicationDialog(event.animalId, List.of(eventMedication(event)), null);
            });
            Button copy = compactButton("Kopieren");
            copy.setOnClickListener(v -> {
                dialog.dismiss();
                showMedicationDialog(null, List.of(eventMedication(event)), null);
            });
            Button edit = compactButton("Bearbeiten");
            edit.setOnClickListener(v -> {
                dialog.dismiss();
                showMedicationDialog(event.animalId, List.of(eventMedication(event)), event);
            });
            actions.addView(repeat, weighted());
            actions.addView(copy, weighted());
            actions.addView(edit, weighted());
            body.addView(actions);
        }
        dialog.show();
    }

    private void showDayDetail(List<AnimalHealthDatabase.Event> events) {
        LinearLayout body = dialogForm();
        body.addView(text(daySummary(events), 15, true));
        for (AnimalHealthDatabase.Event event : events) body.addView(keyValue(formatTime(event.occurredAt), eventPrimary(event) + " · " + event.animalName));
        List<AnimalHealthDatabase.Event> meds = new ArrayList<>();
        Long animalId = null;
        boolean sameAnimal = true;
        for (AnimalHealthDatabase.Event event : events) {
            if (!"medication".equals(event.type) || event.value == null) continue;
            meds.add(event);
            if (animalId == null) animalId = event.animalId;
            else if (!animalId.equals(event.animalId)) sameAnimal = false;
        }
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle(formatDate(events.get(0).occurredAt)).setView(wrapDialog(body)).setNegativeButton("Schließen", null).create();
        if (!meds.isEmpty() && sameAnimal) {
            Long finalAnimalId = animalId;
            Button repeat = primaryButton("Medikationen dieses Tages erneut vorbereiten");
            repeat.setOnClickListener(v -> {
                List<AnimalHealthDatabase.MedicationInput> inputs = new ArrayList<>();
                for (AnimalHealthDatabase.Event event : meds) inputs.add(eventMedication(event));
                dialog.dismiss();
                showMedicationDialog(finalAnimalId, inputs, null);
            });
            body.addView(repeat);
        }
        dialog.show();
    }

    private AnimalHealthDatabase.MedicationInput eventMedication(AnimalHealthDatabase.Event event) {
        return new AnimalHealthDatabase.MedicationInput(event.medicationName == null ? event.title : event.medicationName, event.value == null ? 1 : event.value, event.unit == null ? "dose" : event.unit, event.route, event.notes);
    }

    private void showTaskDialog() {
        List<AnimalHealthDatabase.Animal> animals = db.animals();
        LinearLayout form = dialogForm();
        List<String> animalLabels = new ArrayList<>();
        animalLabels.add("Allgemein");
        for (AnimalHealthDatabase.Animal animal : animals) animalLabels.add(animal.name);
        Spinner animal = spinner(animalLabels.toArray(new String[0]));
        EditText title = field("Aufgabe", false);
        EditText due = field("yyyy-MM-dd HH:mm", false);
        due.setText(nowText());
        Spinner kind = spinner(new String[]{"Erinnerung", "Kontrolle", "Pflege", "Medikation"});
        form.addView(labeled("Bezug", animal));
        form.addView(labeled("Aufgabe", title));
        form.addView(labeled("Fällig", due));
        form.addView(labeled("Art", kind));
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Aufgabe anlegen").setView(wrapDialog(form)).setNegativeButton("Abbrechen", null).setPositiveButton("Speichern", null).create();
        dialog.setOnShowListener(x -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            String taskTitle = title.getText().toString().trim();
            Long time = parseTime(due.getText().toString());
            if (taskTitle.isEmpty() || time == null) {
                toast("Titel und Fälligkeit prüfen.");
                return;
            }
            Long animalId = animal.getSelectedItemPosition() == 0 ? null : animals.get(animal.getSelectedItemPosition() - 1).id;
            String kindValue = switch (kind.getSelectedItemPosition()) { case 1 -> "health_check"; case 2 -> "care"; case 3 -> "medication"; default -> "reminder"; };
            db.addTask(animalId, taskTitle, time, kindValue);
            dialog.dismiss();
            render();
        }));
        dialog.show();
    }

    private void showMedicationPresetDialog() {
        LinearLayout form = dialogForm();
        EditText name = field("Medikament", false);
        EditText species = field("Tierart (optional)", false);
        Spinner unit = spinner(UNIT_LABELS);
        EditText route = field("Applikationsweg (optional)", false);
        form.addView(labeled("Medikament", name));
        form.addView(labeled("Tierart", species));
        form.addView(labeled("Standard-Einheit", unit));
        form.addView(labeled("Standard-Applikationsweg", route));
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Medikament hinzufügen").setView(wrapDialog(form)).setNegativeButton("Abbrechen", null).setPositiveButton("Speichern", null).create();
        dialog.setOnShowListener(x -> dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
            if (name.getText().toString().trim().isEmpty()) {
                toast("Medikament angeben.");
                return;
            }
            db.upsertMedicationPreset(name.getText().toString(), species.getText().toString(), UNIT_VALUES[unit.getSelectedItemPosition()], route.getText().toString());
            dialog.dismiss();
            render();
        }));
        dialog.show();
    }

    private void exportJson() {
        try {
            pendingExport = db.exportJson();
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("application/json");
            intent.putExtra(Intent.EXTRA_TITLE, "animal-health-0.9.0-alpha.1-export.json");
            startActivityForResult(intent, EXPORT_REQUEST);
        } catch (Exception error) {
            toast("Export fehlgeschlagen: " + error.getMessage());
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != EXPORT_REQUEST || resultCode != RESULT_OK || data == null || data.getData() == null || pendingExport == null) return;
        Uri uri = data.getData();
        try (OutputStream out = getContentResolver().openOutputStream(uri)) {
            if (out == null) throw new IllegalStateException("Datei konnte nicht geöffnet werden");
            out.write(pendingExport.getBytes(StandardCharsets.UTF_8));
            out.flush();
            toast("Export gespeichert.");
        } catch (Exception error) {
            toast("Export fehlgeschlagen: " + error.getMessage());
        } finally {
            pendingExport = null;
        }
    }

    private void addHeading(String title, String subtitle) {
        TextView h = text(title, 24, true);
        h.setPadding(dp(2), dp(4), dp(2), 0);
        content.addView(h);
        TextView s = text(subtitle, 13, false);
        s.setTextColor(MUTED);
        s.setPadding(dp(2), 0, dp(2), dp(10));
        content.addView(s);
    }

    private LinearLayout card() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(14), dp(12), dp(14), dp(12));
        card.setBackgroundColor(CARD);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.setMargins(0, 0, 0, dp(10));
        card.setLayoutParams(p);
        card.setElevation(dp(1));
        return card;
    }

    private LinearLayout stat(String label, String value) {
        LinearLayout box = card();
        TextView number = text(value, 22, true);
        number.setTextColor(BLUE);
        box.addView(number);
        TextView name = text(label, 11, false);
        name.setTextColor(MUTED);
        box.addView(name);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        p.setMargins(dp(3), 0, dp(3), dp(10));
        box.setLayoutParams(p);
        return box;
    }

    private TextView sectionTitle(String value) {
        TextView title = text(value, 17, true);
        title.setPadding(0, 0, 0, dp(8));
        return title;
    }

    private View keyValue(String key, String value) {
        LinearLayout row = horizontal();
        row.setPadding(0, dp(4), 0, dp(4));
        TextView k = text(key, 12, false);
        k.setTextColor(MUTED);
        TextView v = text(value == null || value.isBlank() ? "–" : displayValue(value), 13, false);
        v.setGravity(Gravity.END);
        row.addView(k, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        row.addView(v, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        return row;
    }

    private TextView empty(String value) {
        TextView t = text(value, 13, false);
        t.setTextColor(MUTED);
        t.setPadding(0, dp(10), 0, dp(10));
        return t;
    }

    private TextView text(String value, int sp, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(TEXT);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return t;
    }

    private Button primaryButton(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextColor(Color.WHITE);
        b.setBackgroundColor(BLUE);
        b.setAllCaps(false);
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        p.setMargins(0, dp(5), 0, dp(5));
        b.setLayoutParams(p);
        return b;
    }

    private Button compactButton(String label) {
        Button b = new Button(this);
        b.setText(label);
        b.setTextColor(TEXT);
        b.setAllCaps(false);
        b.setMinHeight(dp(38));
        b.setMinimumHeight(dp(38));
        b.setPadding(dp(10), 0, dp(10), 0);
        return b;
    }

    private Button actionButton(String label, View.OnClickListener listener) {
        Button b = compactButton(label);
        b.setOnClickListener(listener);
        return b;
    }

    private LinearLayout horizontal() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        return row;
    }

    private LinearLayout.LayoutParams weighted() {
        LinearLayout.LayoutParams p = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        p.setMargins(dp(3), dp(3), dp(3), dp(3));
        return p;
    }

    private LinearLayout dialogForm() {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(dp(4), dp(4), dp(4), dp(4));
        return form;
    }

    private ScrollView wrapDialog(View child) {
        ScrollView scroll = new ScrollView(this);
        scroll.setPadding(dp(14), 0, dp(14), 0);
        scroll.addView(child);
        return scroll;
    }

    private View labeled(String label, View field) {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setPadding(0, dp(4), 0, dp(4));
        TextView l = text(label, 12, false);
        l.setTextColor(MUTED);
        wrap.addView(l);
        wrap.addView(field);
        return wrap;
    }

    private EditText field(String hint, boolean numeric) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setTextSize(15);
        e.setSingleLine(true);
        if (numeric) e.setInputType(InputType.TYPE_CLASS_NUMBER | InputType.TYPE_NUMBER_FLAG_DECIMAL);
        return e;
    }

    private Spinner spinner(String[] values) {
        Spinner spinner = new Spinner(this);
        spinner.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, values));
        return spinner;
    }

    private Spinner animalSpinner(List<AnimalHealthDatabase.Animal> animals, Long selectedId) {
        String[] labels = new String[animals.size()];
        int selected = 0;
        for (int i = 0; i < animals.size(); i++) {
            labels[i] = animals.get(i).name;
            if (selectedId != null && animals.get(i).id == selectedId) selected = i;
        }
        Spinner spinner = spinner(labels);
        spinner.setSelection(selected);
        return spinner;
    }

    private void setUnit(Spinner spinner, String value) {
        if (value == null) return;
        for (int i = 0; i < UNIT_VALUES.length; i++) if (UNIT_VALUES[i].equals(value)) spinner.setSelection(i);
    }

    private String unitLabel(String value) {
        if (value == null || value.isBlank()) return "–";
        for (int i = 0; i < UNIT_VALUES.length; i++) if (UNIT_VALUES[i].equals(value)) return UNIT_LABELS[i];
        return value;
    }

    private String displayValue(String value) {
        return switch (value) {
            case "female" -> "Weiblich";
            case "male" -> "Männlich";
            case "other" -> "Andere";
            default -> value;
        };
    }

    private String eventTypeLabel(String value) {
        return switch (value) {
            case "medication" -> "Medikation";
            case "weight" -> "Gewicht";
            case "symptom" -> "Symptom";
            case "treatment" -> "Behandlung";
            case "vaccination" -> "Impfung";
            case "veterinary_visit" -> "Tierarztbesuch";
            default -> "Eintrag";
        };
    }

    private String eventIcon(String type) {
        return switch (type) {
            case "medication" -> "💊";
            case "weight" -> "⚖";
            case "vaccination" -> "✚";
            case "symptom" -> "!";
            default -> "•";
        };
    }

    private String daySummary(List<AnimalHealthDatabase.Event> events) {
        int meds = 0, weights = 0, other = 0;
        for (AnimalHealthDatabase.Event event : events) {
            if ("medication".equals(event.type)) meds++;
            else if ("weight".equals(event.type)) weights++;
            else other++;
        }
        List<String> parts = new ArrayList<>();
        if (meds > 0) parts.add(meds + (meds == 1 ? " Medikation" : " Medikationen"));
        if (weights > 0) parts.add(weights + (weights == 1 ? " Gewicht" : " Gewichte"));
        if (other > 0) parts.add(other + (other == 1 ? " weiterer Eintrag" : " weitere Einträge"));
        return String.join(" · ", parts);
    }

    private String nowText() {
        return LocalDateTime.now().format(INPUT_TIME);
    }

    private Long parseTime(String value) {
        try {
            return LocalDateTime.parse(value.trim(), INPUT_TIME).atZone(ZoneId.systemDefault()).toInstant().toEpochMilli();
        } catch (DateTimeParseException error) {
            return null;
        }
    }

    private String dateKey(long millis) {
        return Instant.ofEpochMilli(millis).atZone(ZoneId.systemDefault()).toLocalDate().toString();
    }

    private String formatDate(long millis) {
        return Instant.ofEpochMilli(millis).atZone(ZoneId.systemDefault()).format(DISPLAY_DATE);
    }

    private String formatTime(long millis) {
        return Instant.ofEpochMilli(millis).atZone(ZoneId.systemDefault()).toLocalTime().format(DateTimeFormatter.ofPattern("HH:mm"));
    }

    private String formatDateTime(long millis) {
        return Instant.ofEpochMilli(millis).atZone(ZoneId.systemDefault()).format(DISPLAY_TIME);
    }

    private Double positiveNumber(String value) {
        try {
            double number = Double.parseDouble(value.trim().replace(',', '.'));
            return number > 0 ? number : null;
        } catch (NumberFormatException error) {
            return null;
        }
    }

    private String number(double value) {
        if (Math.rint(value) == value) return String.format(Locale.GERMANY, "%.0f", value);
        return String.format(Locale.GERMANY, "%.3f", value).replaceAll("0+$", "").replaceAll(",?$", "");
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }
}
