import {
  asRecord,
  booleanValue,
  dateOnly,
  dateTime,
  firstDefined,
  integerValue,
  numberValue,
  optionalText,
  requiredText,
  stringList,
} from "./common.js";

export function normalizeLatestWeight(value, path = "animal.latestWeight") {
  if (value == null) return null;
  const raw = asRecord(value, path);
  return {
    eventId: requiredText(
      firstDefined(raw, ["event_id", "eventId"]),
      `${path}.eventId`,
    ),
    valueKg: numberValue(
      firstDefined(raw, ["value_kg", "valueKg"]),
      null,
      `${path}.valueKg`,
    ),
    originalValue: numberValue(
      firstDefined(raw, ["original_value", "originalValue"]),
      null,
      `${path}.originalValue`,
    ),
    originalUnit: optionalText(
      firstDefined(raw, ["original_unit", "originalUnit"]),
    ),
    occurredAt: dateTime(
      firstDefined(raw, ["occurred_at", "occurredAt"]),
      `${path}.occurredAt`,
    ),
  };
}

export function normalizeAnimal(rawValue, metadata = {}) {
  const raw = asRecord(rawValue, "animal");
  const meta = metadata == null ? {} : asRecord(metadata, "animalMetadata");
  return {
    id: requiredText(firstDefined(raw, ["id", "animal_id", "animalId"]), "animal.id"),
    name: requiredText(firstDefined(raw, ["name", "animal_name", "animalName"]), "animal.name"),
    species: requiredText(firstDefined(raw, ["species", "species_id", "speciesId"]), "animal.species"),
    breed: optionalText(firstDefined(raw, ["breed", "breed_name", "breedName"])),
    color: optionalText(firstDefined(raw, ["color", "colour"])),
    sex: optionalText(raw.sex),
    birthDate: dateOnly(firstDefined(raw, ["birth_date", "birthDate"]), "animal.birthDate"),
    arrivalDate: dateOnly(firstDefined(raw, ["arrival_date", "arrivalDate"]), "animal.arrivalDate"),
    status: requiredText(firstDefined(raw, ["status"], "active"), "animal.status"),
    statusChangedAt: dateTime(
      firstDefined(raw, ["status_changed_at", "statusChangedAt"]),
      "animal.statusChangedAt",
    ),
    isArchived: booleanValue(firstDefined(raw, ["is_archived", "isArchived"]), false),
    archivedAt: dateTime(
      firstDefined(raw, ["archived_at", "archivedAt"]),
      "animal.archivedAt",
    ),
    createdAt: dateTime(firstDefined(raw, ["created_at", "createdAt"]), "animal.createdAt"),
    updatedAt: dateTime(firstDefined(raw, ["updated_at", "updatedAt"]), "animal.updatedAt"),
    deviceId: optionalText(firstDefined(raw, ["device_id", "deviceId"])),
    latestWeight: normalizeLatestWeight(
      firstDefined(raw, ["latest_weight", "latestWeight"]),
    ),
    groupId: optionalText(
      firstDefined(meta, ["groupId", "group_id"], firstDefined(raw, ["group_id", "groupId"])),
    ),
    tagIds: stringList(
      firstDefined(meta, ["tagIds", "tag_ids"], firstDefined(raw, ["tag_ids", "tagIds"], [])),
      "animal.tagIds",
    ),
    profileAttachmentId: optionalText(
      firstDefined(
        meta,
        ["profileAttachmentId", "profile_attachment_id"],
        firstDefined(raw, ["profile_attachment_id", "profileAttachmentId"]),
      ),
    ),
  };
}

export function normalizeGroup(rawValue) {
  const raw = asRecord(rawValue, "group");
  return {
    id: requiredText(firstDefined(raw, ["id", "group_id", "groupId"]), "group.id"),
    name: requiredText(raw.name, "group.name"),
    species: optionalText(firstDefined(raw, ["species", "species_id", "speciesId"])),
    description: optionalText(raw.description),
    createdAt: dateTime(firstDefined(raw, ["created_at", "createdAt"]), "group.createdAt"),
    updatedAt: dateTime(firstDefined(raw, ["updated_at", "updatedAt"]), "group.updatedAt"),
    animalCount: integerValue(
      firstDefined(raw, ["animal_count", "animalCount"]),
      0,
      "group.animalCount",
    ),
  };
}

export function normalizeTag(rawValue) {
  const raw = asRecord(rawValue, "tag");
  return {
    id: requiredText(firstDefined(raw, ["id", "tag_id", "tagId"]), "tag.id"),
    name: requiredText(raw.name, "tag.name"),
    description: optionalText(raw.description),
    createdAt: dateTime(firstDefined(raw, ["created_at", "createdAt"]), "tag.createdAt"),
    updatedAt: dateTime(firstDefined(raw, ["updated_at", "updatedAt"]), "tag.updatedAt"),
    animalCount: integerValue(
      firstDefined(raw, ["animal_count", "animalCount"]),
      0,
      "tag.animalCount",
    ),
  };
}

export function normalizeAttachment(rawValue) {
  const raw = asRecord(rawValue, "attachment");
  return {
    id: requiredText(firstDefined(raw, ["id", "attachment_id", "attachmentId"]), "attachment.id"),
    animalId: requiredText(firstDefined(raw, ["animal_id", "animalId"]), "attachment.animalId"),
    eventId: optionalText(firstDefined(raw, ["event_id", "eventId"])),
    filename: requiredText(raw.filename, "attachment.filename"),
    mediaType: requiredText(firstDefined(raw, ["media_type", "mediaType"]), "attachment.mediaType"),
    sizeBytes: integerValue(
      firstDefined(raw, ["size_bytes", "sizeBytes"]),
      0,
      "attachment.sizeBytes",
    ),
    title: optionalText(raw.title),
    createdAt: dateTime(firstDefined(raw, ["created_at", "createdAt"]), "attachment.createdAt"),
    thumbnailUrl: optionalText(firstDefined(raw, ["thumbnail_url", "thumbnailUrl"])),
    previewUrl: optionalText(firstDefined(raw, ["preview_url", "previewUrl"])),
    downloadUrl: optionalText(firstDefined(raw, ["download_url", "downloadUrl", "url"])),
  };
}
