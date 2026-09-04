import {
  asArray,
  asRecord,
  booleanValue,
  firstDefined,
  optionalText,
  requiredText,
} from "./common.js";
import { normalizeTreatmentState } from "./treatments.js";

export function normalizeMasterItem(rawValue) {
  const raw = asRecord(rawValue, "masterItem");
  return {
    kind: requiredText(raw.kind, "masterItem.kind"),
    id: requiredText(firstDefined(raw, ["id", "item_id", "itemId"]), "masterItem.id"),
    baseLabelDe: optionalText(firstDefined(raw, ["base_label_de", "baseLabelDe"])),
    baseLabelEn: optionalText(firstDefined(raw, ["base_label_en", "baseLabelEn"])),
    label: requiredText(firstDefined(raw, ["label", "base_label_de", "baseLabelDe"]), "masterItem.label"),
    overrideLabel: optionalText(
      firstDefined(raw, ["override_label", "overrideLabel"]),
    ),
    storageValue: requiredText(
      firstDefined(raw, ["storage_value", "storageValue", "id"]),
      "masterItem.storageValue",
    ),
    isCustom: booleanValue(firstDefined(raw, ["is_custom", "isCustom"]), false),
    isHidden: booleanValue(firstDefined(raw, ["is_hidden", "isHidden"]), false),
    isModified: booleanValue(
      firstDefined(raw, ["is_modified", "isModified"]),
      false,
    ),
  };
}

export function normalizeMasterDataState(rawValue) {
  const raw = asRecord(rawValue, "masterDataState");
  return {
    entryTypes: asArray(
      firstDefined(raw, ["entry_types", "entryTypes"], []),
      "masterDataState.entryTypes",
    ).map(normalizeMasterItem),
    symptoms: asArray(raw.symptoms, "masterDataState.symptoms").map(
      normalizeMasterItem,
    ),
  };
}

export function normalizeSettingsState(treatmentValue, masterDataValue) {
  const treatment = normalizeTreatmentState(treatmentValue);
  const masterData = normalizeMasterDataState(masterDataValue);
  return {
    ...treatment,
    ...masterData,
  };
}
