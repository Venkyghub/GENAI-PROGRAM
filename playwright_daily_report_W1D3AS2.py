
import asyncio
import json
import random
import re
from datetime import datetime
from pathlib import Path
from unittest import result

import pandas as pd
from playwright.async_api import (
    async_playwright,
    TimeoutError as PlaywrightTimeoutError
)

# ==================================================
# 1. SETTINGS
# ==================================================

FOLDER = Path(__file__).resolve().parent

EXCEL_FILE = FOLDER / "contacts.xlsx"
PROFILE_FOLDER = FOLDER / "whatsapp_profile"
SCREENSHOT_FOLDER = FOLDER / "screenshots"

DEFAULT_MESSAGE = "Hello {name}, hope you are doing well!"

# Small, opt-in test batch
MAX_CONTACTS = 10

# Pacing between actions; this does not prevent restrictions
MIN_DELAY = 2
MAX_DELAY = 5

# ==================================================
# 2. SMALL HELPER FUNCTIONS
# ==================================================

def print_step(message):
    print(f"\n[INFO] {message}", flush=True)


def clean_phone(phone):
    """Keep digits only for WhatsApp's phone URL."""
    if pd.isna(phone):
        return ""

    phone = str(phone).strip()

    # Excel sometimes reads numbers as floats
    if phone.endswith(".0"):
        phone = phone[:-2]

    return re.sub(r"\D", "", phone)


async def pause(page):
    seconds = random.randint(MIN_DELAY, MAX_DELAY)
    print(f"[WAIT] Waiting {seconds} seconds...")
    await page.wait_for_timeout(seconds * 1000)


def save_reports(results):
    """Save the current results to JSON and Excel."""
    date_text = datetime.now().strftime("%Y-%m-%d")

    json_file = FOLDER / f"whatsapp_report_{date_text}.json"
    excel_file = FOLDER / f"whatsapp_report_{date_text}.xlsx"

    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(
            results,
            file,
            indent=4,
            ensure_ascii=False
        )

    # Excel summary: one row per contact
    rows = []

    for item in results:
        rows.append({
            "Name": item["name"],
            "Phone": item["phone"],
            "Status": item["status"],
            "Message": item["message"],
            "Sent At": item["sent_at"],
            "Screenshot": item["screenshot"],
            "Last 3 Incoming Messages": "\n".join(
                item["last_3_messages"]
            ),
            "Error": item["error"]
        })

    pd.DataFrame(rows).to_excel(
        excel_file,
        index=False
    )

    print(f"[REPORT] JSON saved: {json_file.name}")
    print(f"[REPORT] Excel saved: {excel_file.name}")


# ==================================================
# 3. LOGIN TO WHATSAPP
# ==================================================

async def login_whatsapp(page):
    print("\n[INFO] Opening WhatsApp Web")

    await page.goto(
        "https://web.whatsapp.com/",
        wait_until="domcontentloaded",
        timeout=60000
    )

    print("[LOGIN] Page opened.")
    print("[LOGIN] If QR code appears, scan it using your phone.")

    # Check the page repeatedly instead of waiting forever
    # for one particular selector.
    for attempt in range(60):
        print(f"[LOGIN] Checking WhatsApp... {attempt + 1}/60")

        # Check for a QR code
        qr = page.locator("canvas").first
        qr_visible = False

        try:
            qr_visible = await qr.is_visible(timeout=500)
        except Exception:
            pass

        if qr_visible:
            print("[LOGIN] QR code detected.")
            print("[LOGIN] Please scan it now.")

        # Check for the chat interface
        chat_selectors = [
            '#pane-side',
            '[aria-label="Chat list"]',
            'div[contenteditable="true"][role="textbox"]'
        ]

        for selector in chat_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible(timeout=500):
                    print("[LOGIN] WhatsApp interface detected!")
                    return True
            except Exception:
                pass

        # Print current page information occasionally
        if attempt % 10 == 0:
            print("[DEBUG] URL:", page.url)
            print("[DEBUG] Title:", await page.title())

        await page.wait_for_timeout(2000)

    print("[ERROR] WhatsApp did not become ready.")
    print("[DEBUG] Current URL:", page.url)

    await page.screenshot(
        path="whatsapp_login_debug.png"
    )
    print("[DEBUG] Screenshot saved: whatsapp_login_debug.png")

    return False


# ==================================================
# 4. FIND AND OPEN A CONTACT
# ==================================================

async def open_contact(page, name, phone):
    print_step(f"Opening contact: {name}")

    # Direct number URL is more precise than a name search.
    # If no phone is supplied, use WhatsApp's search UI.
    if phone:
        print(f"[SEARCH] Opening chat for number: {phone}")

        await page.goto(
            f"https://web.whatsapp.com/send?phone={phone}",
            wait_until="domcontentloaded"
        )

        await page.wait_for_timeout(3000)

        # Wait for either the composer or a visible page response.
        try:
            await page.wait_for_selector(
                'footer div[contenteditable="true"]',
                timeout=15000
            )
            print("[SEARCH] Chat composer found.")
            return True
        except PlaywrightTimeoutError:
            print("[SEARCH] Direct number did not open a chat.")
            return False

    # Search by name when no number is supplied.
    print(f"[SEARCH] Searching by name: {name}")

    search = page.locator(
        'div[contenteditable="true"]'
    ).first

    try:
        await search.wait_for(
            state="visible",
            timeout=10000
        )
        await search.fill(name)
        await page.wait_for_timeout(2000)

        # Click a result matching the contact name.
        result = page.get_by_text(
            name,
            exact=True
        ).last

        await result.click(timeout=7000)
        await page.wait_for_timeout(2000)

        print("[SEARCH] Contact opened.")
        return True

    except Exception as error:
        print(f"[ERROR] Could not find contact: {error}")
        return False


# ==================================================
# 5. FIND THE MESSAGE BOX
# ==================================================

async def find_message_box(page):
    print("[CHAT] Looking for the message box...")

    # WhatsApp's composer selector can change.
    selectors = [
        'footer div[contenteditable="true"][role="textbox"]',
        'footer div[contenteditable="true"]',
        'div[contenteditable="true"][aria-label="Type a message"]'
    ]

    for selector in selectors:
        try:
            box = page.locator(selector).last

            await box.wait_for(
                state="visible",
                timeout=5000
            )

            print(f"[CHAT] Message box found: {selector}")
            return box

        except PlaywrightTimeoutError:
            print(f"[CHAT] Selector not found: {selector}")

    return None


# ==================================================
# 6. SEND THE PERSONALIZED MESSAGE
# ==================================================


async def send_message(page, message):
    print_step("Preparing the message")

    box = await find_message_box(page)

    if box is None:
        raise RuntimeError("Message box not found")

    print("[MESSAGE] Clicking message box...")
    await box.click()

    print("[MESSAGE] Typing:", message)
    await box.fill(message)

    await pause(page)

    print("[MESSAGE] Pressing Enter...")
    await box.press("Enter")

    print("[MESSAGE] Waiting for chat to update...")
    await page.wait_for_timeout(3000)

    # Save a diagnostic screenshot regardless of verification.
    await page.screenshot(
        path="message_check.png"
    )
    print("[DEBUG] Saved message_check.png")

    # Check the visible page for the exact message text.
    print("[MESSAGE] Checking whether text appears in chat...")

    message_found = False

    try:
        text_locator = page.get_by_text(
            message,
            exact=True
        )

        count = await text_locator.count()

        if count > 0:
            # Exclude the composer if the text remains there.
            for i in range(count):
                item = text_locator.nth(i)
                try:
                    if await item.is_visible():
                        message_found = True
                        break
                except Exception:
                    pass

    except Exception as error:
        print("[DEBUG] Text check error:", error)

    if message_found:
        print("[MESSAGE] Exact message text found on page.")
        return True

    print("[WARNING] Could not confirm outgoing message.")
    print("[WARNING] Check message_check.png before retrying.")

    return False


# ==================================================
# 7. TAKE SCREENSHOT
# ==================================================

async def take_screenshot(page, name, index):
    print_step("Taking screenshot")

    safe_name = re.sub(
        r"[^A-Za-z0-9_-]",
        "_",
        name
    )

    time_text = datetime.now().strftime("%H%M%S")

    file_path = (
        SCREENSHOT_FOLDER /
        f"{index}_{safe_name}_{time_text}.png"
    )

    await page.screenshot(
        path=str(file_path),
        full_page=False
    )

    print(f"[SCREENSHOT] Saved: {file_path}")
    return str(file_path)


# ==================================================
# 8. EXTRACT LAST 3 INCOMING MESSAGES
# ==================================================

async def extract_last_3_messages(page):
    print_step("Extracting recent incoming messages")

    # This is a best-effort selector for incoming text.
    messages = page.locator(
        "div.message-in span.selectable-text"
    )

    try:
        await messages.first.wait_for(
            state="attached",
            timeout=5000
        )
    except PlaywrightTimeoutError:
        print("[EXTRACT] No incoming text messages found.")
        return []

    count = await messages.count()
    print(f"[EXTRACT] Found {count} incoming text elements.")

    last_messages = []

    start = max(0, count - 3)

    for i in range(start, count):
        try:
            text = (
                await messages.nth(i).inner_text()
            ).strip()

            if text:
                last_messages.append(text)
                print(f"[EXTRACT] Message {len(last_messages)}: {text}")

        except Exception as error:
            print(f"[EXTRACT] Could not read element: {error}")

    return last_messages[-3:]


# ==================================================
# 9. PROCESS ONE CONTACT
# ==================================================

async def process_contact(page, contact, index):
    name = str(contact["Name"]).strip()
    phone = clean_phone(contact["Phone"])

    template = contact["Message"]

    if pd.isna(template) or not str(template).strip():
        template = DEFAULT_MESSAGE

    # Replace {name} with the actual contact name.
    message = str(template).replace("{name}", name)

    print("\n" + "=" * 55)
    print(f"[CONTACT {index}] {name}")
    print(f"[CONTACT] Phone: {phone}")
    print(f"[CONTACT] Message: {message}")
    print("=" * 55)

    result = {
        "name": name,
        "phone": phone,
        "message": message,
        "status": "pending",
        "sent_at": None,
        "screenshot": None,
        "last_3_messages": [],
        "error": None
    }

    try:
        if not phone:
            raise ValueError("Phone number is missing.")

        opened = await open_contact(
            page,
            name,
            phone
        )

        if not opened:
            result["status"] = "contact_not_found"
            result["error"] = "Could not open the contact chat."
            print("[ERROR] Contact not found.")
            return result

        await pause(page)

        # Send the message.
        
        
        #await send_message(page, message)

        #result["status"] = "sent"
        confirmed = await send_message(page, message)

        if confirmed:
            result["status"] = "sent_visible"
            result["sent_at"] = datetime.now().isoformat(timespec="seconds")
            result["screenshot"] = await take_screenshot(page, name, index)
            result["last_3_messages"] = (await extract_last_3_messages(page))

        else:
            result["status"] = "unconfirmed"
            result["error"] = ("Message was attempted, but outgoing text ""could not be verified. Check message_check.png.")
                               








        result["sent_at"] = datetime.now().isoformat(
            timespec="seconds"
        )

        print("[STATUS] Message appears in outgoing chat.")

        # Screenshot after the outgoing message appears.
        result["screenshot"] = await take_screenshot(
            page,
            name,
            index
        )

        await pause(page)

        # Extract recent incoming messages from this chat.
        result["last_3_messages"] = (
            await extract_last_3_messages(page)
        )

    except PlaywrightTimeoutError as error:
        result["status"] = "timeout"
        result["error"] = str(error)
        print(f"[TIMEOUT] {error}")

    except Exception as error:
        if result["status"] == "pending":
            result["status"] = "failed"

        result["error"] = str(error)
        print(f"[ERROR] {error}")

    print(f"[RESULT] {name}: {result['status']}")
    return result


# ==================================================
# 10. MAIN PROGRAM
# ==================================================

async def main():
    print_step("Starting WhatsApp automation")

    # Check the Excel file.
    if not EXCEL_FILE.exists():
        print(f"[ERROR] Excel file not found: {EXCEL_FILE}")
        return

    print("[EXCEL] Reading contacts.xlsx")

    df = pd.read_excel(
        EXCEL_FILE,
        dtype={"Phone": str}
    )

    required_columns = ["Name", "Phone", "Message"]

    for column in required_columns:
        if column not in df.columns:
            print(f"[ERROR] Missing Excel column: {column}")
            return

    df = df.head(MAX_CONTACTS)

    print(f"[EXCEL] Loaded {len(df)} contacts.")

    SCREENSHOT_FOLDER.mkdir(
        parents=True,
        exist_ok=True
    )

    results = []

    async with async_playwright() as p:

        print_step("Launching browser")

        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_FOLDER),
            headless=False
        )

        page = (
            context.pages[0]
            if context.pages
            else await context.new_page()
        )

        try:
            logged_in = await login_whatsapp(page)

            if not logged_in:
                print("[STOP] Login failed. Check whatsapp_login_debug.png")
                return

            print_step("Beginning contact processing")

            for index, (_, contact) in enumerate(
                df.iterrows(),
                start=1
            ):
                result = await process_contact(
                    page,
                    contact,
                    index
                )

                results.append(result)

                # Save after every contact so partial work is kept.
                print_step("Saving current reports")
                save_reports(results)

                # Pause before processing the next contact.
                if index < len(df):
                    print("[NEXT] Preparing next contact...")
                    await pause(page)

            print_step("All contacts processed")

        except Exception as error:
            print(f"[FATAL] Automation stopped: {error}")

        finally:
            print_step("Saving final reports")
            save_reports(results)

            print_step("Closing browser")
            await context.close()

    print_step("Automation finished")


# ==================================================
# 11. RUN THE PROGRAM
# ==================================================

if __name__ == "__main__":
    asyncio.run(main())