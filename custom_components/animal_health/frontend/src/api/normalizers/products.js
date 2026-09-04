import {
  asArray,
  asRecord,
  booleanValue,
  camelizeObject,
  firstDefined,
  integerValue,
  optionalText,
  requiredText,
  stringList,
} from "./common.js";

export function normalizeProductDatabase(rawValue) {
  const raw = asRecord(rawValue, "productDatabase");
  return {
    id: requiredText(
      firstDefined(raw, ["id", "database_id", "databaseId"]),
      "productDatabase.id",
    ),
    name: requiredText(raw.name, "productDatabase.name"),
    description: optionalText(raw.description),
    productTypes: stringList(
      firstDefined(raw, ["product_types", "productTypes"], []),
      "productDatabase.productTypes",
    ),
    sourceName: optionalText(firstDefined(raw, ["source_name", "sourceName"])),
    sourceType: optionalText(firstDefined(raw, ["source_type", "sourceType"])),
    version: optionalText(raw.version),
    dataAsOf: optionalText(firstDefined(raw, ["data_as_of", "dataAsOf"])),
    priority: integerValue(raw.priority, 0, "productDatabase.priority"),
    updateMode: optionalText(firstDefined(raw, ["update_mode", "updateMode"])),
    licenseNotice: optionalText(
      firstDefined(raw, ["license_notice", "licenseNotice"]),
    ),
    sourceUrl: optionalText(firstDefined(raw, ["source_url", "sourceUrl"])),
    enabled: booleanValue(raw.enabled, true),
    isSystem: booleanValue(firstDefined(raw, ["is_system", "isSystem"]), false),
    supportsLocalOverrides: booleanValue(
      firstDefined(raw, ["supports_local_overrides", "supportsLocalOverrides"]),
      false,
    ),
    viewOf: optionalText(firstDefined(raw, ["view_of", "viewOf"])),
    itemCount: integerValue(
      firstDefined(raw, ["item_count", "itemCount"]),
      0,
      "productDatabase.itemCount",
    ),
    modifiedCount: integerValue(
      firstDefined(raw, ["modified_count", "modifiedCount"]),
      0,
      "productDatabase.modifiedCount",
    ),
  };
}

function normalizeIngredientDetails(value, path) {
  return asArray(value, path).map((item, index) =>
    camelizeObject(asRecord(item, `${path}[${index}]`)),
  );
}

function normalizeProductInternal(rawValue, { includeOriginal = true } = {}) {
  const raw = asRecord(rawValue, "product");
  const product = {
    id: requiredText(firstDefined(raw, ["id", "item_id", "itemId"]), "product.id"),
    catalogItemId: optionalText(
      firstDefined(raw, ["catalog_item_id", "catalogItemId"]),
    ),
    databaseId: requiredText(
      firstDefined(raw, ["database_id", "databaseId", "source_id", "sourceId", "source"]),
      "product.databaseId",
    ),
    kind: requiredText(firstDefined(raw, ["kind", "product_type", "productType"]), "product.kind"),
    name: requiredText(raw.name, "product.name"),
    targetSpecies: stringList(
      firstDefined(raw, ["target_species", "targetSpecies"], []),
      "product.targetSpecies",
    ),
    activeIngredient: optionalText(
      firstDefined(raw, ["active_ingredient", "activeIngredient"]),
    ),
    activeIngredients: stringList(
      firstDefined(raw, ["active_ingredients", "activeIngredients"], []),
      "product.activeIngredients",
    ),
    activeIngredientDetails: normalizeIngredientDetails(
      firstDefined(raw, ["active_ingredient_details", "activeIngredientDetails"], []),
      "product.activeIngredientDetails",
    ),
    concentration: optionalText(raw.concentration),
    dosageForm: optionalText(firstDefined(raw, ["dosage_form", "dosageForm"])),
    routes: stringList(raw.routes || [], "product.routes"),
    routeDescriptions: stringList(
      firstDefined(raw, ["route_descriptions", "routeDescriptions"], []),
      "product.routeDescriptions",
    ),
    defaultRoute: optionalText(firstDefined(raw, ["default_route", "defaultRoute"])),
    authorisationNumber: optionalText(
      firstDefined(raw, ["authorisation_number", "authorisationNumber"]),
    ),
    authorisationStatus: optionalText(
      firstDefined(raw, ["authorisation_status", "authorisationStatus"]),
    ),
    applicationArea: optionalText(
      firstDefined(raw, ["application_area", "applicationArea"]),
    ),
    aliases: stringList(raw.aliases || [], "product.aliases"),
    classifications: stringList(
      raw.classifications || [],
      "product.classifications",
    ),
    isHidden: booleanValue(firstDefined(raw, ["is_hidden", "isHidden"]), false),
    isCustom: booleanValue(firstDefined(raw, ["is_custom", "isCustom"]), false),
    isModified: booleanValue(
      firstDefined(raw, ["is_modified", "isModified"]),
      false,
    ),
  };

  if (includeOriginal) {
    const originalRaw = firstDefined(raw, ["original"]);
    product.original =
      originalRaw && typeof originalRaw === "object" && !Array.isArray(originalRaw)
        ? normalizeProductInternal(originalRaw, { includeOriginal: false })
        : null;
  }
  return product;
}

export function normalizeProduct(rawValue) {
  return normalizeProductInternal(rawValue);
}

function normalizeViews(value) {
  const raw = value == null ? {} : asRecord(value, "productState.views");
  return {
    dewormingDatabaseId: optionalText(
      firstDefined(raw, ["deworming_database_id", "dewormingDatabaseId"]),
    ),
    swissmedicDatabaseId: optionalText(
      firstDefined(raw, ["swissmedic_database_id", "swissmedicDatabaseId"]),
    ),
  };
}

export function normalizeProductState(rawValue) {
  const raw = asRecord(rawValue, "productState");
  return {
    databases: asArray(raw.databases, "productState.databases").map(
      normalizeProductDatabase,
    ),
    products: asArray(raw.products, "productState.products").map(normalizeProduct),
    mergedProducts: asArray(
      firstDefined(raw, ["merged_products", "mergedProducts"], []),
      "productState.mergedProducts",
    ).map(normalizeProduct),
    views: normalizeViews(raw.views),
  };
}
