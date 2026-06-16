import time, os, threading
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager 
from database import add_log, update_status

def get_driver():
    opt = Options()
    opt.add_argument("--headless")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    svc = Service(GeckoDriverManager().install())
    return webdriver.Firefox(service=svc, options=opt)

def join_google_meet(link, mid, name):
    driver = get_driver()
    try:
        driver.get(link)
        wait = WebDriverWait(driver, 20)
        # Name field (guest join)
        try:
            inp = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Your name']")))
            inp.clear(); inp.send_keys(name)
        except TimeoutException: pass
        # Mic off
        try: driver.find_element(By.XPATH, "//button[@aria-label='Turn off microphone']").click()
        except: pass
        # Join
        for sel in ["//button[contains(.,'Join now')]", "//button[contains(.,'Ask to join')]"]:
            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, sel))).click()
                add_log("✅ Joined Google Meet", "success"); update_status(mid, "joined")
                time.sleep(int(os.getenv("MEETING_DURATION_MINUTES", 60)) * 60)
                return
            except TimeoutException: pass
        add_log("❌ Join button nahi mila", "error"); update_status(mid, "failed")
    except Exception as e:
        add_log(f"❌ Meet error: {e}", "error"); update_status(mid, "failed")
    finally:
        driver.quit()

def join_zoom(link, mid, name):
    driver = get_driver()
    try:
        # Web client URL
        if "/j/" in link:
            num = link.split("/j/")[1].split("?")[0]
            link = f"https://zoom.us/wc/{num}/join?prefer=1"
        driver.get(link)
        wait = WebDriverWait(driver, 20)
        try:
            inp = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Your Name']")))
            inp.clear(); inp.send_keys(name)
        except TimeoutException: pass
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Join')]"))).click()
            add_log("✅ Joined Zoom", "success"); update_status(mid, "joined")
            time.sleep(int(os.getenv("MEETING_DURATION_MINUTES", 60)) * 60)
        except TimeoutException:
            add_log("❌ Zoom join button nahi mila", "error"); update_status(mid, "failed")
    except Exception as e:
        add_log(f"❌ Zoom error: {e}", "error"); update_status(mid, "failed")
    finally:
        driver.quit()

def join_teams(link, mid, name):
    driver = get_driver()
    try:
        driver.get(link)
        wait = WebDriverWait(driver, 20)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Join on the web')]"))).click()
            time.sleep(2)
        except TimeoutException: pass
        try:
            inp = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Type your name']")))
            inp.clear(); inp.send_keys(name)
        except TimeoutException: pass
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Join now')]"))).click()
            add_log("✅ Joined Teams", "success"); update_status(mid, "joined")
            time.sleep(int(os.getenv("MEETING_DURATION_MINUTES", 60)) * 60)
        except TimeoutException:
            add_log("❌ Teams join button nahi mila", "error"); update_status(mid, "failed")
    except Exception as e:
        add_log(f"❌ Teams error: {e}", "error"); update_status(mid, "failed")
    finally:
        driver.quit()

def join_meeting(meeting, name="Student"):
    update_status(meeting["id"], "joining")
    p = meeting["platform"]
    if   p == "Google Meet":      join_google_meet(meeting["link"], meeting["id"], name)
    elif p == "Zoom":             join_zoom(meeting["link"], meeting["id"], name)
    elif p == "Microsoft Teams":  join_teams(meeting["link"], meeting["id"], name)