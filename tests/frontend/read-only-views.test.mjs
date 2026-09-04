import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { createInitialState } from "../../custom_components/animal_health/frontend/src/app/state.js";
import {
  normalizeAnimalDetail,
  normalizeAnimalDirectory,
} from "../../custom_components/animal_health/frontend/src/api/normalizers/index.js";
import { createTranslator } from "../../custom_components/animal_health/frontend/src/ui/read-only/i18n.js";
import { renderAnimalDetail } from "../../custom_components/animal_health/frontend/src/ui/views/animal-detail.js";
import { renderAnimals } from "../../custom_components/animal_health/frontend/src/ui/views/animals.js";
import { renderOverview } from "../../custom_components/animal_health/frontend/src/ui/views/overview.js";

const fixture = JSON.parse(
  await readFile(
    new URL("./fixtures/phase2-snapshots-0.9.41.json", import.meta.url),
    "utf8",
  ),
);

function state({ language = "de", filters = {}, detailStatus = "ready" } = {}) {
  const directory = normalizeAnimalDirectory({
    dashboard: fixture.dashboard,
    catalog: fixture.catalog,
    features: fixture.features,
    tagState: fixture.tagState,
  });
  const detail = normalizeAnimalDetail(fixture.animalDetail, {
    today: directory.today,
  });
  detail.animal = {
    ...detail.animal,
    groupId: directory.animals[0].groupId,
    tagIds: directory.animals[0].tagIds,
    profileAttachmentId: directory.animals[0].profileAttachmentId,
  };
  const locale = language === "de" ? "de-CH" : "en-GB";
  return createInitialState({
    language: { code: language, locale },
    navigation: {
      current: { name: "overview", params: {} },
    },
    animals: {
      status: "ready",
      items: directory.animals,
      groups: directory.groups,
      tags: directory.tags,
      catalog: directory.catalog,
      directoryMeta: {
        version: directory.version,
        timeZone: directory.timeZone,
        today: directory.today,
        summary: directory.summary,
        exports: directory.exports,
      },
      filters: {
        query: "",
        groupId: "all",
        tagId: "all",
        includeArchived: true,
        openPanel: null,
        searchOpen: false,
        ...filters,
      },
      detail: {
        status: detailStatus,
        animalId: detail.animal.id,
        data: detailStatus === "ready" ? detail : null,
        error: detailStatus === "error"
          ? { code: "transport", message: "Detail nicht verfügbar" }
          : null,
      },
      error: null,
    },
    tasks: {
      status: "ready",
      definitions: directory.tasks,
      occurrences: directory.occurrences,
      error: null,
    },
    timeline: {
      status: "ready",
      items: directory.events,
      error: null,
    },
  });
}

function context(value, routeName) {
  return {
    translate: createTranslator(value.language.code),
    language: value.language.code,
    locale: value.language.locale,
    routeName,
    integrationVersion: "0.9.41",
    timeZone: value.animals.directoryMeta.timeZone,
  };
}

test("German overview renders canonical summary animals tasks and events", () => {
  const value = state();
  const html = renderOverview(value, context(value, "overview"));

  assert.match(html, /data-modern-route="overview"/);
  assert.match(html, /data-view="animals"/);
  assert.match(html, /Tartar/);
  assert.match(html, /Legehennen/);
  assert.match(html, /Meloxidyl geben/);
  assert.match(html, /Überfällig/);
  assert.match(html, /Letzte Chronikeinträge/);
  assert.match(html, /Aus Aufgabe/);
  assert.doesNotMatch(html, /animal_id|scheduled_for|is_overdue/);
});

test("overview supports English and empty states", () => {
  const english = state({ language: "en" });
  const englishHtml = renderOverview(english, context(english, "overview"));
  assert.match(englishHtml, /Active animals/);
  assert.match(englishHtml, /Due today/);
  assert.match(englishHtml, /From task/);

  const empty = createInitialState({
    language: { code: "en", locale: "en-GB" },
    animals: {
      status: "ready",
      items: [],
      groups: [],
      tags: [],
      catalog: {},
      directoryMeta: {
        version: "0.9.41",
        timeZone: "Europe/Zurich",
        today: "2026-09-04",
        summary: {},
      },
      filters: {
        query: "",
        groupId: "all",
        tagId: "all",
        includeArchived: true,
      },
      error: null,
    },
  });
  const emptyHtml = renderOverview(empty, context(empty, "overview"));
  assert.match(emptyHtml, /No animals available/);
  assert.match(emptyHtml, /No tasks available/);
  assert.match(emptyHtml, /No timeline records available/);
});

test("overview renders filter controls from canonical group and tag data", () => {
  const value = state({
    filters: {
      openPanel: "group",
      groupId: "GR-FLOCK",
      tagId: "TG-RESCUE",
      searchOpen: true,
      query: "tartar",
    },
  });
  const html = renderOverview(value, context(value, "overview"));

  assert.match(html, /data-action="home-group-select" data-id="GR-FLOCK"/);
  assert.match(html, /data-action="home-tag-toggle"/);
  assert.match(html, /data-action="home-search"/);
  assert.match(html, /value="tartar"/);
  assert.match(html, /data-action="home-filter-reset"/);
});

test("animal directory renders searchable canonical animal cards", () => {
  const value = state();
  value.navigation.current = { name: "animals", params: {} };
  const html = renderAnimals(value, context(value, "animals"));

  assert.match(html, /data-modern-route="animals"/);
  assert.match(html, /data-action="animal-detail" data-id="AH-CHICKEN-1"/);
  assert.match(html, /data-action="animals-filter"/);
  assert.match(html, /data-action="animals-toggle-archived"/);
  assert.match(html, /Legehennen/);
  assert.match(html.replace(/[’'\s]/g, ""), /1250g/);
  assert.doesNotMatch(html, /latest_weight|group_id|tag_ids/);
});

test("animal directory exposes filtered-empty and archived states", () => {
  const filtered = state({ filters: { query: "does-not-exist" } });
  filtered.navigation.current = { name: "animals", params: {} };
  assert.match(
    renderAnimals(filtered, context(filtered, "animals")),
    /Keine Tiere vorhanden/,
  );

  const archived = state();
  archived.animals.items = [
    {
      ...archived.animals.items[0],
      id: "A-ARCHIVE",
      name: "Archivtier",
      isArchived: true,
      status: "rehomed",
    },
  ];
  archived.navigation.current = { name: "animals", params: {} };
  const html = renderAnimals(archived, context(archived, "animals"));
  assert.match(html, /Archivtier/);
  assert.match(html, /Archiviert/);
});

test("animal detail renders identity group tags weight tasks and event origin", () => {
  const value = state();
  value.navigation.current = {
    name: "animal-detail",
    params: { animalId: "AH-CHICKEN-1" },
  };
  const html = renderAnimalDetail(value, context(value, "animal-detail"));

  assert.match(html, /data-modern-route="animal-detail"/);
  assert.match(html, /Tartar/);
  assert.match(html, /Legehennen/);
  assert.match(html, /#Ehemalige Legehenne/);
  assert.match(html.replace(/[’'\s]/g, ""), /1250g/);
  assert.match(html, /Meloxidyl geben/);
  assert.match(html, /Aus Aufgabe/);
  assert.match(html, /data-action="edit-animal" data-id="AH-CHICKEN-1"/);
  assert.match(html, /data-action="animal-status" data-id="AH-CHICKEN-1"/);
  assert.match(html, /data-view="animals"/);
  assert.doesNotMatch(html, /animal_id|task_occurrence_id|occurred_at/);
});

test("animal detail keeps directory identity during loading and errors", () => {
  const loading = state({ detailStatus: "loading" });
  loading.navigation.current = {
    name: "animal-detail",
    params: { animalId: "AH-CHICKEN-1" },
  };
  const loadingHtml = renderAnimalDetail(
    loading,
    context(loading, "animal-detail"),
  );
  assert.match(loadingHtml, /Tartar/);
  assert.match(loadingHtml, /Animal Health wird geladen/);

  const failed = state({ detailStatus: "error" });
  failed.navigation.current = loading.navigation.current;
  const errorHtml = renderAnimalDetail(
    failed,
    context(failed, "animal-detail"),
  );
  assert.match(errorHtml, /Tartar/);
  assert.match(errorHtml, /Detail nicht verfügbar/);
  assert.match(errorHtml, /data-action="detail-refresh"/);
});

test("all view renderers escape canonical user content", () => {
  const value = state();
  value.animals.items[0] = {
    ...value.animals.items[0],
    name: '<script data-test="animal">bad</script>',
  };
  value.animals.detail.data.animal = value.animals.items[0];
  value.timeline.items[0] = {
    ...value.timeline.items[0],
    title: "<b>event</b>",
  };

  const overview = renderOverview(value, context(value, "overview"));
  assert.doesNotMatch(overview, /<script data-test=/);
  assert.match(overview, /&lt;script data-test=&quot;animal&quot;&gt;/);
  assert.doesNotMatch(overview, /<b>event<\/b>/);
  assert.match(overview, /&lt;b&gt;event&lt;\/b&gt;/);
});
