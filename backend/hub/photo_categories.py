PHOTO_CATEGORY_GROUPS = {
    "Biography": ["Headshots", "Childhood", "Highschool", "Tertiary", "Professional last days"],
    "Wife tributes": ["Pre marriage", "Weddings", "Pictures together"],
    "Children": ["Pictures with children"],
    "Family": ["Pictures with family at occasions", "Pictures with Ga", "Pictures with Nungua", "Pictures Shama", "Pictures with Akrapong"],
    "Pictures with siblings": ["Pictures with siblings"],
    "Cousins": ["Pictures with cousins"],
    "Nephews and nieces": ["Pictures with nieces and nephews"],
    "Professional": ["Clogsag", "Labour union", "Ministry of agriculture"],
    "School": ["Katanga", "Accra Academy"],
    "Social": ["Social", "Social with friends", "Church"],
}
PHOTO_CATEGORIES = {"Uncategorised"} | {
    f"{group} / {name}" for group, names in PHOTO_CATEGORY_GROUPS.items() for name in names
}
