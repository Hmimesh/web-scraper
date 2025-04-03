import json

arabic_authorities = {
    "אבו גוש", "אבו סנאן", "אום אל-פחם", "באקה אל גרבייה", "בועיינה-נוג'ידאת",
    "בוקעאתא", "ביר אל-מכסור", "בית ג'ן", "בסמה", "בענה", "ג'דיידה-מכר",
    "ג'וליס", "ג'לג'וליה", "ג'סר א-זרקא", "ג'ש (גוש חלב)", "ג'ת", "דבוריה",
    "דייר חנא", "דיר אל אסד", "דליית אל כרמל", "חורה", "חורפיש", "טובא-זנגריה",
    "טורעאן", "טייבה", "טירה", "טמרה", "יאנוח-ג'ת", "יפיע", "ירכא", "כאבול",
    "כאוכב אבו אל-היג'א", "כפר ברא", "כפר כמא", "כפר כנא", "כפר מנדא", "כפר קאסם",
    "כפר קרע", "מגאר", "מג'דל אל כרום", "מג'דל שמס", "מסעדה", "מעיליא", "מעלה עירון",
    "מזרעה", "משהד", "נחף", "נצרת", "סאג'ור", "סח'נין", "ע'ג'ר", "עוספיה", "עיילבון",
    "עילוט", "עין מאהל", "עין קנייא", "עראבה", "ערערה", "ערערה-בנגב", "פסוטה", "פקיעין (בוקייעה)",
    "ראמה", "ריינה", "שבלי - אום אל - גנם", "שעב", "שפרעם", "קלנסווה", "זרזיר"
}
def extract_clean_empty_cities(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    empty_non_arabic = {
        city: contacts for city, contacts in data.items()
        if not contacts and city not in arabic_authorities
    }

    with open(output_path, "w", encoding="utf-8") as out:
        for city in empty_non_arabic:
            out.write(f"{city}\n")

    print(f"Cleaned empty cities and counties {len(empty_non_arabic)} saved to '{output_path}'")

if __name__ == "__main__":
    extract_clean_empty_cities("smart_contacts.json", "empty_contacts_cleaned.txt")
