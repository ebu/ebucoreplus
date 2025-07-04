"""
Configuration for main class groupings and domain color codes.
Modify these lists to extend or change your ontology domains and main classes.
"""

grouped_main_classes = {
    "Audit": [
        "AuditJob", "AuditReport", "Measure"
    ],
    "Commercial": [
        "Asset", "Contract", "Rights", "Rule"
    ],
    "Consumption": [
        "Account", "ConsumptionDevice", "ConsumptionEvent", "ConsumptionLicence", "Consumer", "ResonanceEvent"
    ],
    "Distribution": [
        "ConsumptionDeviceProfile", "PublicationEvent", "PublicationService"
    ],
    "Editorial": [
        "EditorialObject", "Event", "Location", "TimelineTrack"
    ],
    "Financial": [
        "AssetValue", "ContractCost"
    ],
    "Participation": [
        "Agent", "Crew", "Involvement", "Organisation", "Person"
    ],
    "Planning": [
        "Audience", "Campaign", "ProductionOrder", "PublicationPlan"
    ],
    "Production": [
        "Artefact", "Essence", "Format", "MediaResource", "OnStagePosition", "PhysicalResource",
        "ProductionDevice", "ProductionJob", "Resource", "Track"
    ]
}

group_colors = {
    "Planning": "#FFCC99",
    "Commercial": "#FFD700",
    "Editorial": "#87CEEB",
    "Participation": "#98FB98",
    "Production": "#DDA0DD",
    "Distribution": "#ADD8E6",
    "Consumption": "#FFA07A",
    "Financial": "#E6B0AA",
    "Audit": "#C0C0C0"
}


def get_class_color(label):
    for group, class_list in grouped_main_classes.items():
        if label in class_list:
            return group_colors.get(group, "gray")
    return "gray"

