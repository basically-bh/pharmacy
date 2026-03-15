// Copyright (c) 2026, Basically and contributors
// For license information, please see license.txt

// ─────────────────────────────────────
// SECTION 1: CONSTANTS
// ─────────────────────────────────────
const ROUTE_PHRASES = {
    "Oral": "orally",
    "Intravenous (IV)": "to be administered intravenously",
    "Intramuscular (IM)": "to be administered intramuscularly",
    "Subcutaneous (SC)": "to be administered subcutaneously",
    "Topical": "apply topically",
    "Transdermal": "apply transdermally",
    "Inhalation": "inhale",
    "Sublingual": "place under the tongue",
    "Buccal": "place in the cheek",
    "Rectal": "insert rectally",
    "Vaginal": "insert vaginally",
    "Nasal": "spray into the nose",
    "Ophthalmic": "instill into the eyes",
    "Otic": "instill into the ears"
};

// ─────────────────────────────────────
// SECTION 2: HELPER FUNCTIONS
// ─────────────────────────────────────

/**
 * Generate full instruction text from the given document values
 * @param {object} doc - Frappe Doc object
 * @returns {string} - Instruction string
 */
function generateInstructionText(doc) {
    const { dosage, frequency, timing, route, duration } = doc;
    let instruction = "";
    const routePhrase = ROUTE_PHRASES[route];

    const isActionBasedRoute = routePhrase && /^(apply|insert|spray|instill|inhale|place)/.test(routePhrase);

    if (isActionBasedRoute) {
        instruction += `${routePhrase}`;
        if (dosage) instruction += ` ${dosage}`;
    } else if (dosage) {
        instruction += `Take ${dosage}`;
    }

    // Add frequency and timing
    if (frequency) {
        instruction += ` ${frequency.toLowerCase()}`;

        if (timing && !["As Directed", "After Meals", "Before Meals", "With Meals", "At Bedtime"].includes(timing)) {
            instruction += ` in the ${timing.toLowerCase()}`;
        } else if (timing && timing !== "As Directed") {
            instruction += ` ${timing.toLowerCase()}`;
        }
    } else if (timing && timing !== "As Directed") {
        instruction += ` in the ${timing.toLowerCase()}`;
    } else if (timing === "As Directed") {
        instruction += ` as directed`;
    }

    if (routePhrase && !isActionBasedRoute) {
        instruction += ` ${routePhrase}`;
    }

    // Append duration if applicable
    if (duration && duration !== "Until Finished") {
        if (duration === "As Directed" && timing !== "As Directed") {
            instruction += ` ${duration.toLowerCase()}`;
        } else if (duration !== "As Directed") {
            instruction += ` for ${duration}`;
        }
    }

    return instruction.trim().charAt(0).toUpperCase() + instruction.trim().slice(1);
}

/**
 * Set the instruction field on the form
 * @param {object} frm - Frappe form instance
 */
function updateInstructionField(frm) {
    const instruction = generateInstructionText(frm.doc);
    frm.set_value("instructions", instruction);
}

/**
 * Convert dosage schedule to frequency
 * @param {string} schedule 
 * @returns {string}
 */
function mapScheduleToFrequency(schedule) {
    const scheduleMap = {
        "1-0-0": "Once Daily",
        "0-1-0": "Once Daily",
        "0-0-1": "Once Daily",
        "1-0-1": "Twice Daily",
        "1-1-0": "Twice Daily",
        "1-1-1": "Three Times Daily",
        "2-0-2": "Four Times Daily",
        "2-2-2": "Four Times Daily",
        "As Needed (PRN)": "As Needed (PRN)"
    };
    return scheduleMap[schedule] || (schedule === "Custom" ? "Custom" : "");
}

// ─────────────────────────────────────
// SECTION 3: MAIN DOCTYPE EVENTS
// ─────────────────────────────────────
frappe.ui.form.on('Prescription Instruction', {
    onload(frm) {
        // Filter medicine field to show only registered products
        frm.set_query('medicine', () => ({
            filters: {
                is_registered_product: 1
            }
        }));

        updateInstructionField(frm);
    },

    dosage_schedule(frm) {
        const freq = mapScheduleToFrequency(frm.doc.dosage_schedule);
        frm.set_value('frequency', freq);
        updateInstructionField(frm);
    },

    dosage: updateInstructionField,
    frequency: updateInstructionField,
    timing: updateInstructionField,
    route: updateInstructionField,
    duration: updateInstructionField
});
