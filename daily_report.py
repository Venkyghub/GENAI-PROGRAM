import pyautogui
import pyscreeze
import pyperclip
import time as t
from datetime import datetime,time
import openpyxl
import os
import sys

pyautogui.FAILSAFE=True
pyautogui.PAUSE=1.0

todays_dt=datetime.now().strftime('%Y-%m-%d')
todays_dt_u=datetime.now().strftime('%Y_%m_%d')
curr_time = datetime.now()
todays_dt_time= curr_time.strftime("%Y-%m-%d %H:%M:%S")
start_x = 1195
start_y = 486

end_x = 1370 
end_y = 915
my_comments = "DAILY REPORT IS CAPTURED."

print("Opening the browser....")
t.sleep(2)
pyautogui.hotkey("win","r")
t.sleep(2)
pyautogui.write("chrome")
t.sleep(2)
pyautogui.press("enter")
t.sleep(2)

pyautogui.write("https://mausam.imd.gov.in/chennai/")
t.sleep(2)
pyautogui.press("enter")
t.sleep(2)


pyautogui.moveTo(start_x, start_y, duration=1.0)
pyautogui.click()
t.sleep(0.5)

print("Dragging to select the area...")
pyautogui.dragTo(end_x, end_y, duration=1.5, button='left')
t.sleep(1.0)  # Pause so you can visually verify the selection

print("Copying selection...")
pyautogui.hotkey("ctrl", "c")
t.sleep(0.5)

copied_text = pyperclip.paste()
pyautogui.hotkey('alt', 'f4')
excel_file = fr"C:\Users\VENKATESH\GENAI PROGRAM\daily_report_{todays_dt}.xlsx"


# Open a blank Excel application instance visually
if sys.platform == "win32":
    os.system("start excel")
elif sys.platform == "darwin":
    os.system("open -a 'Microsoft Excel'")
t.sleep(4.0)  # Wait for Excel start window to open
'''
# Maximize the window so coordinates are consistent
if sys.platform == "win32":
    pyautogui.hotkey('win', 'up')
    t.sleep(1.0)
'''
# --- Row 1: Date & Time ---
pyautogui.typewrite("Current Date & Time:")
pyautogui.press('enter')
pyautogui.typewrite(todays_dt_time)
pyautogui.press('enter')  # Moves to next row start (Cell A2)

# --- Row 2: Copied Web Content ---
pyautogui.typewrite("Copied Web Content:")
pyautogui.press('enter')
# We paste the text from clipboard instead of typing it character by character (much faster!)
if sys.platform == "darwin":
    pyautogui.hotkey("command", "v")
else:
    pyautogui.typewrite(copied_text)
t.sleep(0.5)
pyautogui.press('enter')  # Moves to Cell A3

# --- Row 3: Your Comments ---
pyautogui.typewrite("User Comments:")
pyautogui.press('enter')
pyautogui.typewrite(my_comments)
pyautogui.press('enter')
t.sleep(1.5)  # Pause to see everything completely typed up on screen

pyautogui.press('f12') 
pyautogui.typewrite(excel_file)
pyautogui.press('enter')

print("\n=== STEP 3: SCREENSHOT & CLOSING ===")
# Take screenshot of the sheet exactly as it looks right now
screenshot_name = f"excel_live_entry_{todays_dt}.png"
screenshot = pyautogui.screenshot()
t.sleep(2)
screenshot.save(screenshot_name)
pyautogui.hotkey('alt', 'f4')
t.sleep(2)
print(f"📸 Live view snapshot saved as: {screenshot_name}")



# Close Excel without saving to keep your computer clean
print("Closing application...")
if sys.platform == "win32":
    pyautogui.hotkey('alt', 'f4')
    t.sleep(0.5)
    pyautogui.press('right') # Highlight "Don't Save" option
    pyautogui.press('enter') # Confirm don't save
elif sys.platform == "darwin":
    pyautogui.hotkey('command', 'q')
    t.sleep(0.5)
    pyautogui.press('right') 
    pyautogui.press('enter')

print("✨ Live workflow loop successfully complete!")




'''
print("--- PHASE 1: START POINT (Top-Left) ---")
print("Move your mouse to the TOP-LEFT corner of the square content...")
t.sleep(5)  # 5 seconds to position your mouse
start_x, start_y = pyautogui.position()
print(f"✅ Captured Start Point: start_x = {start_x}, start_y = {start_y}\n")

print("--- PHASE 2: END POINT (Bottom-Right) ---")
print("Now, move your mouse to the BOTTOM-RIGHT corner of the content...")
t.sleep(5)  # 5 seconds to move your mouse
end_x, end_y = pyautogui.position()
print(f"✅ Captured End Point: end_x = {end_x}, end_y = {end_y}\n")

print("--- YOUR FINAL COORDINATES ---")
print(f"start_x, start_y = {start_x}, start_y")
print(f"end_x, end_y = {end_x}, {end_y}")
'''
'''
print("Get ready! Move your mouse over the website text...")
t.sleep(5)  # Gives you 5 seconds to position your mouse

# Get the current mouse position
x, y = pyautogui.position()

print(f"Your coordinates are: text_x = {x}, text_y = {y}")
'''