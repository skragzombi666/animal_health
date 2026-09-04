import assert from "node:assert/strict";
import test from "node:test";

import {
  escapeAttribute,
  escapeHtml,
  formatDateOnly,
  formatDateTime,
  formatEnum,
  formatNumber,
  speciesLabel,
} from "../../custom_components/animal_health/frontend/src/ui/read-only/format.js";
import {
  MESSAGES,
  createTranslator,
} from "../../custom_components/animal_health/frontend/src/ui/read-only/i18n.js";
import {
  renderError,
  renderEventRow,
  renderHeader,
  renderOccurrenceRow,
  renderQuickActions,
  renderShell,
} from "../../custom_components/animal_health/frontend/src/ui/read-only/components.js";
import { READ_ONLY_STYLES } from "../../custom_components/animal_health/frontend/src/ui/read-only/styles.js";

test("date-only formatting never shifts the calendar date", () => {
  assert.equal(formatDateOnly("2026-03-29", "de-CH"), "29.03.2026");
  assert.equal(formatDateOnly("2026-03-29", "en-GB"), "29/03/2026");
  assert.equal(formatDateOnly(null, "de-CH"), "–");
  assert.equal(formatDateOnly("29.03.2026", "de-CH"), "29.03.2026");
});

test("date-time and number formatting are locale aware", () => {
  assert.match(formatDateTime("2026-09-04T08:05:00+02:00", "de-CH"), /04\.09\.2026|4\.9\.2026/);
  assert.match(formatDateTime("2026-09-04T08:05:00+02:00", "de-CH"), /08:05/);
  assert.equal(formatNumber(1250, "de-CH", 0).replace(/[’'\s]/g, ""), "1250");
  assert.equal(formatNumber(null, "de-CH"), "–");
});

test("all read-only translation keys exist in German and English", () => {
  assert.deepEqual(Object.keys(MESSAGES.de).sort(), Object.keys(MESSAGES.en).sort());
  assert.equal(createTranslator("de")("animals"), "Tiere");
  assert.equal(createTranslator("de-CH")("overdue"), "Überfällig");
  assert.equal(createTranslator("en")("animals"), "Animals");
  assert.equal(createTranslator("fr")("animals"), "Animals");
  assert.equal(createTranslator("de")("unknown-key"), "unknown-key");
});

test("dynamic HTML and attribute content is escaped", () => {
  const raw = `<b title="x">&'</b>`;
  assert.equal(
    escapeHtml(raw),
    "&lt;b title=&quot;x&quot;&gt;&amp;&#039;&lt;/b&gt;",
  );
  assert.equal(escapeAttribute(raw), escapeHtml(raw));
});

test("canonical enum and species labels use translations and catalogue names", () => {
  const translate = createTranslator("de");
  const state = {
    animals: {
      catalog: {
        species: [
          { id: "chicken", nameDe: "Huhn", nameEn: "Chicken" },
        ],
      },
    },
  };
  assert.equal(formatEnum("active", translate), "Aktiv");
  assert.equal(formatEnum("veterinary_visit", translate), "Tierarztbesuch");
  assert.equal(formatEnum("custom_value", translate), "custom value");
  assert.equal(speciesLabel({ species: "chicken" }, state, translate, "de"), "Huhn");
  assert.equal(speciesLabel({ species: "chicken" }, state, createTranslator("en"), "en"), "Chicken");
  assert.equal(speciesLabel({ species: "alpaca" }, state, translate, "de"), "alpaca");
});

test("shared components preserve legacy action names without issuing writes", () => {
  const translate = createTranslator("de");
  const context = {
    translate,
    language: "de",
    locale: "de-CH",
    routeName: "overview",
    integrationVersion: "0.9.41",
  };
  const header = renderHeader(context);
  const quick = renderQuickActions("A-1", translate);
  assert.match(header, /data-view="overview"/);
  assert.match(header, /data-view="tasks"/);
  assert.match(header, /data-action="refresh"/);
  assert.match(quick, /data-action="create-animal"/);
  assert.match(quick, /data-action="record-weight" data-id="A-1"/);

  const shell = renderShell("<p>content</p>", context);
  assert.match(shell, new RegExp(READ_ONLY_STYLES.includes("\.card") ? "<style>" : "never"));
  assert.match(shell, /data-modern-route="overview"/);
});

test("task and event rows use canonical fields and escape content", () => {
  const translate = createTranslator("de");
  const context = { translate, locale: "de-CH", language: "de" };
  const occurrence = renderOccurrenceRow(
    {
      id: "O-1",
      title: "Medikament <geben>",
      animalName: "Tartar",
      status: "pending",
      timing: "overdue",
      dueDate: "2026-09-03",
      scheduledLocal: "2026-09-03T08:00:00+02:00",
      planned: { medicationName: "Meloxidyl" },
    },
    context,
  );
  assert.match(occurrence, /Medikament &lt;geben&gt;/);
  assert.match(occurrence, /Überfällig/);
  assert.match(occurrence, /03\.09\.2026/);

  const event = renderEventRow(
    {
      id: "E-1",
      title: "Meloxidyl",
      animalName: "Tartar",
      type: "medication",
      occurredAt: "2026-09-03T08:05:00+02:00",
      source: { kind: "task" },
      target: {
        scope: "group",
        groupId: "G-1",
        memberSnapshot: ["A-1", "A-2"],
      },
      notes: "vollständig & gut",
    },
    context,
  );
  assert.match(event, /Aus Aufgabe/);
  assert.match(event, /Gruppenaktion/);
  assert.match(event, /vollständig &amp; gut/);
});

test("error component exposes one explicit retry action", () => {
  const context = { translate: createTranslator("en") };
  const markup = renderError(
    { code: "transport", message: "offline <now>" },
    "read.refresh",
    context,
  );
  assert.match(markup, /offline &lt;now&gt;/);
  assert.match(markup, /data-action="read.refresh"/);
  assert.equal((markup.match(/data-action=/g) || []).length, 1);
});
