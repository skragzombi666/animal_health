export const DTO_SCHEMA_VERSION = 1;

/**
 * @typedef {"animal"|"animals"|"group"|"general"} TargetScope
 */

/**
 * @typedef {Object} TargetDto
 * @property {TargetScope} scope
 * @property {string|null} animalId
 * @property {string[]} animalIds
 * @property {string|null} groupId
 * @property {string[]} memberSnapshot
 */

/**
 * @typedef {Object} LatestWeightDto
 * @property {string} eventId
 * @property {number|null} valueKg
 * @property {number|null} originalValue
 * @property {string|null} originalUnit
 * @property {string|null} occurredAt
 */

/**
 * @typedef {Object} AnimalDto
 * @property {string} id
 * @property {string} name
 * @property {string} species
 * @property {string|null} breed
 * @property {string|null} color
 * @property {string|null} sex
 * @property {string|null} birthDate
 * @property {string|null} arrivalDate
 * @property {string} status
 * @property {string|null} statusChangedAt
 * @property {boolean} isArchived
 * @property {string|null} archivedAt
 * @property {string|null} createdAt
 * @property {string|null} updatedAt
 * @property {string|null} deviceId
 * @property {LatestWeightDto|null} latestWeight
 * @property {string|null} groupId
 * @property {string[]} tagIds
 * @property {string|null} profileAttachmentId
 */

/**
 * @typedef {Object} AttachmentDto
 * @property {string} id
 * @property {string} animalId
 * @property {string|null} eventId
 * @property {string} filename
 * @property {string} mediaType
 * @property {number|null} sizeBytes
 * @property {string|null} title
 * @property {string|null} createdAt
 * @property {string|null} thumbnailUrl
 * @property {string|null} previewUrl
 * @property {string|null} downloadUrl
 */

/**
 * @typedef {Object} TaskDefinitionDto
 * @property {string} id
 * @property {string|null} seriesId
 * @property {TargetDto} target
 * @property {string|null} animalName
 * @property {string} title
 * @property {string|null} description
 * @property {string} kind
 * @property {string} recurrenceType
 * @property {number|null} recurrenceInterval
 * @property {string|null} startDate
 * @property {string|null} endDate
 * @property {string|null} dueTime
 * @property {boolean} isActive
 * @property {string|null} nextPendingAt
 * @property {string|null} nextPendingLocal
 * @property {number|null} pendingCount
 * @property {number|null} overdueCount
 * @property {Object<string, unknown>} planned
 * @property {string|null} entityId
 * @property {string|null} createdAt
 * @property {string|null} updatedAt
 */

/**
 * @typedef {"pending"|"completed"|"skipped"|"cancelled"} TaskOccurrenceStatus
 */

/**
 * @typedef {"overdue"|"today"|"upcoming"|"closed"} TaskTiming
 */

/**
 * @typedef {Object} TaskOccurrenceDto
 * @property {string} id
 * @property {string|null} seriesId
 * @property {string} definitionId
 * @property {TargetDto} target
 * @property {string|null} animalName
 * @property {string} title
 * @property {string|null} scheduledAt
 * @property {string|null} scheduledLocal
 * @property {string|null} dueDate
 * @property {TaskOccurrenceStatus|string} status
 * @property {TaskTiming} timing
 * @property {string|null} completedAt
 * @property {string|null} notes
 * @property {boolean} taskIsActive
 * @property {Object<string, unknown>} planned
 * @property {Object<string, unknown>|null} completion
 * @property {string|null} createdAt
 * @property {string|null} updatedAt
 */

/**
 * @typedef {Object} EventSourceDto
 * @property {string|null} kind
 * @property {string|null} taskId
 * @property {string|null} occurrenceId
 * @property {string|null} groupId
 * @property {string|null} treatmentPlanId
 */

/**
 * @typedef {Object} HealthEventDto
 * @property {string} id
 * @property {string} animalId
 * @property {string|null} animalName
 * @property {string} type
 * @property {string|null} occurredAt
 * @property {string} title
 * @property {string|null} notes
 * @property {number|null} value
 * @property {string|null} unit
 * @property {string|null} correctionOfEventId
 * @property {string|null} createdAt
 * @property {TargetDto} target
 * @property {EventSourceDto|null} source
 * @property {Object<string, unknown>} payload
 * @property {AttachmentDto[]} attachments
 */

/**
 * @typedef {Object} ProductDatabaseDto
 * @property {string} id
 * @property {string} name
 * @property {string|null} description
 * @property {string[]} productTypes
 * @property {string|null} sourceName
 * @property {string|null} sourceType
 * @property {string|null} version
 * @property {string|null} dataAsOf
 * @property {number|null} priority
 * @property {string|null} updateMode
 * @property {string|null} licenseNotice
 * @property {string|null} sourceUrl
 * @property {boolean} enabled
 * @property {boolean} isSystem
 * @property {boolean} supportsLocalOverrides
 * @property {string|null} viewOf
 * @property {number|null} itemCount
 * @property {number|null} modifiedCount
 */

/**
 * @typedef {Object} ProductDto
 * @property {string} id
 * @property {string|null} catalogItemId
 * @property {string} databaseId
 * @property {string} kind
 * @property {string} name
 * @property {string[]} targetSpecies
 * @property {string|null} activeIngredient
 * @property {string[]} activeIngredients
 * @property {Object<string, unknown>[]} activeIngredientDetails
 * @property {string|null} concentration
 * @property {string|null} dosageForm
 * @property {string[]} routes
 * @property {string[]} routeDescriptions
 * @property {string|null} defaultRoute
 * @property {string|null} authorisationNumber
 * @property {string|null} authorisationStatus
 * @property {string|null} applicationArea
 * @property {string[]} aliases
 * @property {string[]} classifications
 * @property {boolean} isHidden
 * @property {boolean} isCustom
 * @property {boolean} isModified
 * @property {ProductDto|null} [original]
 */

/**
 * @typedef {Object} TreatmentComponentDto
 * @property {string} type
 * @property {string} name
 * @property {number|null} dose
 * @property {string|null} unit
 * @property {string|null} route
 * @property {string|null} instructions
 */

/**
 * @typedef {Object} TreatmentPlanDto
 * @property {string} id
 * @property {string} name
 * @property {string|null} speciesId
 * @property {string|null} listAs
 * @property {string|null} description
 * @property {string|null} defaultUnit
 * @property {string|null} defaultRoute
 * @property {TreatmentComponentDto[]} components
 */

/**
 * @typedef {Object} SettingsStateDto
 * @property {string|null} offLabelMode
 * @property {TreatmentPlanDto[]} treatmentPlans
 * @property {Object<string, unknown>[]} statusChanges
 * @property {Object<string, unknown>[]} entryTypes
 * @property {Object<string, unknown>[]} symptoms
 */

/**
 * @typedef {Object} AnimalDirectoryDto
 * @property {string} version
 * @property {string|null} generatedAt
 * @property {string|null} timeZone
 * @property {string|null} today
 * @property {Object<string, number|null>} summary
 * @property {AnimalDto[]} animals
 * @property {TaskDefinitionDto[]} tasks
 * @property {TaskOccurrenceDto[]} occurrences
 * @property {HealthEventDto[]} events
 * @property {Object<string, unknown>[]} groups
 * @property {Object<string, unknown>[]} tags
 * @property {Object<string, unknown>} catalog
 */

export {};
