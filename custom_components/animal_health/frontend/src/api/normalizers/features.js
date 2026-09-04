import { normalizeGroup, normalizeTag } from "./animals.js";
import {
  asArray,
  asRecord,
  booleanValue,
  firstDefined,
  integerValue,
  optionalText,
  recordOfStringLists,
  recordOfText,
} from "./common.js";

function normalizeExports(value) {
  const raw = value == null ? {} : asRecord(value, "features.exports");
  return {
    json: optionalText(raw.json),
    backup: optionalText(raw.backup),
    animalPdf: optionalText(firstDefined(raw, ["animal_pdf", "animalPdf"])),
  };
}

export function normalizeFeatureState(featuresValue, tagStateValue = {}) {
  const features = asRecord(featuresValue, "features");
  const tagState = asRecord(tagStateValue, "tagState");
  return {
    storage: optionalText(features.storage),
    maxAttachmentSizeBytes: integerValue(
      firstDefined(features, ["max_attachment_size_bytes", "maxAttachmentSizeBytes"]),
      0,
      "features.maxAttachmentSizeBytes",
    ),
    primaryGroupRequired: booleanValue(
      firstDefined(tagState, ["primary_group_required", "primaryGroupRequired"]),
      false,
    ),
    groups: asArray(features.groups, "features.groups").map(normalizeGroup),
    memberships: recordOfText(features.memberships, "features.memberships"),
    tags: asArray(tagState.tags, "tagState.tags").map(normalizeTag),
    tagMemberships: recordOfStringLists(
      firstDefined(tagState, ["tag_memberships", "tagMemberships"], {}),
      "tagState.tagMemberships",
    ),
    profiles: Object.fromEntries(
      Object.entries(asRecord(firstDefined(tagState, ["profiles"], {}), "tagState.profiles")).map(
        ([animalId, attachmentId]) => [String(animalId), optionalText(attachmentId)],
      ),
    ),
    exports: normalizeExports(features.exports),
  };
}
