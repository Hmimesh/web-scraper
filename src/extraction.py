import pandas as pd
import sys
import re
import os
import time
from typing import Optional
import openai
import time
from pathlib import Path
from tqdm import tqdm


# Initialize OpenAI client only when needed
client = None

def get_openai_client():
    global client
    if client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY. Please export it using: export OPENAI_API_KEY='your-key-here'")
        client = openai.OpenAI(api_key=api_key)
    return client


def gpt_fix_names_and_department(name: str, department: str) -> tuple[str, str]:
    """Use OpenAI to fix Hebrew names and standardize departments"""
    if pd.isna(name) or not name:
        return "", department or ""

    # Use JSON format for more reliable parsing
    json_prompt = f"""תקן את פרטי איש הקשר הבא. החזר JSON בלבד:

שם: "{name}"
מחלקה: "{department}"

כללים לשם:
- רק שמות אמיתיים של אנשים (פרטי ומשפחה)
- אם זה שם באנגלית - תרגם לעברית (David → דוד)
- אם זה מילים כמו "דרישה", "מס", "טלפון", "פקס" - החזר null
- אם זה תיאור או הוראה - החזר null
- אם זה שם + תפקיד - חלץ רק את השם האמיתי

כללים למחלקה:
- תקן לפורמט "מחלקת [שם]" (חינוך/רווחה/נוער/תרבות/ספורט/הנדסה/כספים)

דוגמאות:
{{"name": "דוד כהן", "department": "מחלקת חינוך"}}
{{"name": null, "department": "מחלקת רווחה"}}

תשובה:"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = get_openai_client().chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "אתה עוזר לנקות נתוני אנשי קשר. החזר תמיד JSON תקין."},
                    {"role": "user", "content": json_prompt}
                ],
                temperature=0.1,
                max_tokens=100,
                timeout=15
            )

            content = response.choices[0].message.content.strip()

            # Try to parse JSON response
            try:
                import json
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())

                    fixed_name = result.get("name", "").strip() if result.get("name") else ""
                    fixed_dept = result.get("department", "").strip() if result.get("department") else department

                    # Validate results
                    if fixed_name and len(fixed_name) >= 2 and "לא רלוונטי" not in fixed_name:
                        time.sleep(0.2)  # Rate limiting
                        return fixed_name, fixed_dept
                    else:
                        time.sleep(0.2)
                        return "", fixed_dept

            except json.JSONDecodeError:
                # Fallback to original regex parsing
                name_match = re.search(r"שם:\s*(.+)", content)
                dept_match = re.search(r"מחלקה:\s*(.+)", content)

                fixed_name = name_match.group(1).strip() if name_match else name
                fixed_dept = dept_match.group(1).strip() if dept_match else department

                if "לא רלוונטי" in fixed_name or len(fixed_name) < 2:
                    time.sleep(0.2)
                    return "", fixed_dept

                time.sleep(0.2)
                return fixed_name, fixed_dept

        except Exception as e:
            print(f"OpenAI attempt {attempt + 1} failed for '{name[:30]}...': {e}")
            if attempt < max_retries - 1:
                time.sleep(1)  # Wait before retry
                continue

    # If all attempts fail, return original with basic cleaning
    print(f"All OpenAI attempts failed for '{name[:30]}...', using fallback")
    cleaned_name = re.sub(r'["\n\t]', '', name).strip()
    return cleaned_name if len(cleaned_name) >= 2 else "", department

def clean_phone_number(phone: str) -> Optional[str]:
    """Clean and standardize phone numbers"""
    if pd.isna(phone) or not phone:
        return None

    # Convert to string and handle float values (which lose leading zeros)
    phone_str = str(phone).strip()

    # If it's a float (like 26302700.0), convert to int first to remove .0
    if '.' in phone_str and phone_str.replace('.', '').replace('-', '').isdigit():
        try:
            phone_int = int(float(phone_str))
            phone_str = str(phone_int)
        except ValueError:
            pass

    # Add leading zero if it looks like an Israeli number without one
    if phone_str.isdigit() and len(phone_str) in [8, 9] and not phone_str.startswith('0'):
        phone_str = '0' + phone_str

    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone_str)

    # Handle international formats
    if cleaned.startswith('+972'):
        cleaned = '0' + cleaned[4:]
    elif cleaned.startswith('972'):
        cleaned = '0' + cleaned[3:]

    # Israeli phone number validation and formatting:
    # Mobile: 05X-XXX-XXXX (10 digits total)
    # Landline: 0X-XXX-XXXX (9 digits total)

    if len(cleaned) >= 8 and cleaned.startswith('0'):
        # Mobile numbers (10 digits): 050-XXX-XXXX, 052-XXX-XXXX, etc.
        if re.match(r'^05[0-9]\d{7}$', cleaned):
            # Format: 052-123-4567
            return f"{cleaned[:3]}-{cleaned[3:6]}-{cleaned[6:]}"

        # Jerusalem area (02): 02-XXX-XXXX (9 digits)
        elif re.match(r'^02\d{7}$', cleaned):
            # Format: 02-123-4567
            return f"{cleaned[:2]}-{cleaned[2:5]}-{cleaned[5:]}"

        # Tel Aviv area (03): 03-XXX-XXXX (9 digits)
        elif re.match(r'^03\d{7}$', cleaned):
            # Format: 03-123-4567
            return f"{cleaned[:2]}-{cleaned[2:5]}-{cleaned[5:]}"

        # Haifa area (04): 04-XXX-XXXX (9 digits)
        elif re.match(r'^04\d{7}$', cleaned):
            # Format: 04-123-4567
            return f"{cleaned[:2]}-{cleaned[2:5]}-{cleaned[5:]}"

        # Other valid area codes (08, 09): 0X-XXX-XXXX (9 digits)
        elif re.match(r'^0[89]\d{7}$', cleaned):
            # Format: 08-123-4567
            return f"{cleaned[:2]}-{cleaned[2:5]}-{cleaned[5:]}"

        # Special numbers (07X): 07X-XXX-XXXX (10 digits)
        elif re.match(r'^07[0-9]\d{7}$', cleaned):
            # Format: 070-123-4567
            return f"{cleaned[:3]}-{cleaned[3:6]}-{cleaned[6:]}"

    return None

def clean_email(email: str) -> Optional[str]:
    """Clean and validate email addresses"""
    if pd.isna(email) or not email:
        return None

    email = str(email).strip().lower()

    # Basic email validation
    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return email

    return None

def clean_name(name: str) -> Optional[str]:
    """Clean and standardize names"""
    if pd.isna(name) or not name:
        return None

    name = str(name).strip()

    # Remove quotes, newlines, and tabs
    name = name.replace('"', '').replace("'", '').replace('\n', ' ').replace('\t', ' ')

    # Remove common prefixes/suffixes that aren't names
    name = re.sub(r'^(תפקיד|מחלקה|אגף|לשכה|מנהל|מנהלת)[::\s]*', '', name)
    name = re.sub(r'[::\s]*(תפקיד|מחלקה|אגף|לשכה)$', '', name)

    # Remove empty or meaningless entries
    meaningless_patterns = [
        r'^[\s\-_.,]*$',  # Only whitespace/punctuation
        r'^[0-9]+$',      # Only numbers
        r'^(na|n/a|null|none|undefined)$',  # Common null values
        r'^.{1,2}$',      # Too short (1-2 characters)
        r'^(לפרטים נוספים|פרטים נוספים|צור קשר|יצירת קשר).*',  # Contact info text
        r'^(כתובת|טלפון|פקס|דוא"ל|אימייל).*',  # Field labels
    ]

    for pattern in meaningless_patterns:
        if re.match(pattern, name, re.IGNORECASE):
            return None

    # Clean up common formatting issues
    name = re.sub(r'\s+', ' ', name)  # Multiple spaces to single space
    name = re.sub(r'^[,\-\s:]+|[,\-\s:]+$', '', name)  # Remove leading/trailing punctuation

    # Remove text that looks like job titles mixed with names
    if any(word in name.lower() for word in ['מנהל', 'רכז', 'עובד', 'מזכיר', 'יועץ']):
        # Try to extract just the name part
        words = name.split()
        potential_names = []
        for word in words:
            if not any(title in word for title in ['מנהל', 'רכז', 'עובד', 'מזכיר', 'יועץ', 'תפקיד']):
                potential_names.append(word)
        if potential_names:
            name = ' '.join(potential_names)

    return name.strip() if len(name.strip()) > 2 else None

def clean_department(dept: str) -> Optional[str]:
    """Clean and standardize department names"""
    if pd.isna(dept) or not dept:
        return None

    dept = str(dept).strip()

    # Remove meaningless entries
    if len(dept) < 3 or dept.lower() in ['na', 'n/a', 'null', 'none']:
        return None

    return dept

def clean_role(role: str) -> Optional[str]:
    """Clean and standardize role/position names"""
    if pd.isna(role) or not role:
        return None

    role = str(role).strip()

    # Remove meaningless entries
    if len(role) < 3 or role.lower() in ['na', 'n/a', 'null', 'none']:
        return None

    return role

def remove_duplicate_contacts(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate contacts based on phone and email"""
    # Create a composite key for deduplication
    df['dedup_key'] = df['טלפון'].astype(str) + '|' + df['אימייל'].astype(str)

    # Keep first occurrence of each unique contact
    df_deduped = df.drop_duplicates(subset=['dedup_key'], keep='first')
    df_deduped = df_deduped.drop('dedup_key', axis=1)

    return df_deduped

def clean_csv_data(input_file: str, output_file: str, use_openai: bool = True):
    """Main function to clean CSV contact data"""
    try:
        # Read the CSV file
        print(f"Reading {input_file}...")
        df = pd.read_csv(input_file)

        print(f"Original data: {len(df)} rows")

        # Clean each column
        print("Cleaning phone numbers...")
        df['טלפון'] = df['טלפון'].apply(clean_phone_number)

        print("Cleaning email addresses...")
        df['אימייל'] = df['אימייל'].apply(clean_email)

        print("Cleaning names...")
        df['שם'] = df['שם'].apply(clean_name)

        print("Cleaning departments...")
        df['מחלקה'] = df['מחלקה'].apply(clean_department)
        
        # Optional OpenAI processing
        if use_openai and os.getenv("OPENAI_API_KEY"):
            print("Fixing names and departments with OpenAI...")
            print(f"Processing {len(df)} contacts with OpenAI (this may take a while)...")

            # Process in batches to show progress and avoid rate limits
            batch_size = 10
            total_batches = (len(df) + batch_size - 1) // batch_size
            temp_output = output_file.replace(".csv", "_temp.csv")

            for i in range(0, len(df), batch_size):
                batch_end = min(i + batch_size, len(df))
                batch_num = (i // batch_size) + 1
                print(f"\nProcessing batch {batch_num}/{total_batches} (contacts {i+1}-{batch_end})...")

                # Apply OpenAI fixes to the batch
                for idx in tqdm(range(i, batch_end), desc=f"Batch {batch_num}/{total_batches}", leave=False):
                    if idx < len(df):
                        original_name = df.iloc[idx]["שם"]
                        original_dept = df.iloc[idx]["מחלקה"]

                        fixed_name, fixed_dept = gpt_fix_names_and_department(original_name, original_dept)

                        df.iloc[idx, df.columns.get_loc("שם")] = fixed_name
                        df.iloc[idx, df.columns.get_loc("מחלקה")] = fixed_dept

                # Save progress after each batch
                df.to_csv(temp_output, index=False, encoding="utf-8-sig")
                print(f"Progress saved to {temp_output}")
        else:
            if not use_openai:
                print("Skipping OpenAI processing (disabled)")
            else:
                print("Skipping OpenAI processing (no API key found)")
        # Drop bad rows (fix column name typo)
        print("Removing rows without contact information...")
        df = df.dropna(subset=['אימייל', 'טלפון'], how='all')
        df = df.dropna(subset=['שם'])


        print("Cleaning roles...")
        df['תפקיד'] = df['תפקיד'].apply(clean_role)

        # Remove rows where both phone and email are empty
        print("Removing rows without contact information...")
        df = df.dropna(subset=['טלפון', 'אימייל'], how='all')

        # Remove rows where name is empty
        print("Removing rows without names...")
        df = df.dropna(subset=['שם'])

        # Remove duplicates
        print("Removing duplicate contacts...")
        df = remove_duplicate_contacts(df)

        # Sort by city and name
        df = df.sort_values(['עיר', 'שם'])

        # Reset index
        df = df.reset_index(drop=True)

        print(f"Cleaned data: {len(df)} rows")

        # Ensure phone numbers are saved as strings, not floats
        if 'טלפון' in df.columns:
            df['טלפון'] = df['טלפון'].astype(str).replace('nan', '')
            df['טלפון'] = df['טלפון'].replace('None', '')
            df.loc[df['טלפון'] == '', 'טלפון'] = None

        # Save cleaned data
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"Saved cleaned data to {output_file}")

        # Print summary statistics
        print("\n=== Cleaning Summary ===")
        print(f"Total contacts: {len(df)}")
        print(f"Contacts with phone: {df['טלפון'].notna().sum()}")
        print(f"Contacts with email: {df['אימייל'].notna().sum()}")
        print(f"Contacts with both: {(df['טלפון'].notna() & df['אימייל'].notna()).sum()}")
        print(f"Unique cities: {df['עיר'].nunique()}")

    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) < 3:
        print("Usage: python extraction.py <input_csv> <output_csv> [--no-openai]")
        print("  --no-openai: Skip OpenAI processing for faster basic cleaning")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    use_openai = "--no-openai" not in sys.argv

    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        sys.exit(1)

    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"OpenAI processing: {'Enabled' if use_openai else 'Disabled'}")
    print("-" * 50)

    clean_csv_data(input_file, output_file, use_openai)

if __name__ == "__main__":
    main()
