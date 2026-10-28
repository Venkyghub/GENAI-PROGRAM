
import os
import traceback
from pathlib import Path
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import gspread

# Load the existing external .env file
env_path = Path(
    r"C:\Users\VENKATESH\GENAI PROGRAM\WEEK2\DAY3LANGCHAIN\traced-app\.env"
)

print("Environment file exists:", env_path.is_file())
load_dotenv(dotenv_path=env_path, override=True)

try:
    json_value = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not json_value:
        raise ValueError(
            "GOOGLE_SERVICE_ACCOUNT_JSON is missing from the .env file."
        )

    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID is missing from the .env file.")

    json_path = Path(json_value.strip().strip('"').strip("'"))
    print("Credentials file exists:", json_path.is_file())

    credentials = Credentials.from_service_account_file(
        str(json_path),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    print("Credentials loaded successfully.")

    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(sheet_id.strip())

    print("Spreadsheet opened successfully:", spreadsheet.title)

except Exception as exc:
    print("ERROR TYPE:", type(exc).__name__)
    print("ERROR DETAILS:", repr(exc))
    traceback.print_exc()
