from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time

# تحميل المتغيرات من ملف .env (للتطوير المحلي)
load_dotenv()

# إعداد ChromeDriver
chrome_driver_path = "/app/.chromedriver/bin/chromedriver"  # المسار في Heroku
download_dir = "/app/downloads"  # مجلد التحميل في Heroku

# إعداد الخيارات لـ Chrome
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-extensions")
options.add_argument("--disable-background-networking")
options.add_argument("--disable-background-timer-throttling")
options.add_argument("--disable-backgrounding-occluded-windows")
options.add_argument("--disable-breakpad")
options.add_argument("--disable-client-side-phishing-detection")
options.add_argument("--disable-component-update")
options.add_argument("--disable-default-apps")
options.add_argument("--disable-domain-reliability")
options.add_argument("--disable-features=AudioServiceOutOfProcess")
options.add_argument("--disable-hang-monitor")
options.add_argument("--disable-ipc-flooding-protection")
options.add_argument("--disable-popup-blocking")
options.add_argument("--disable-prompt-on-repost")
options.add_argument("--disable-renderer-backgrounding")
options.add_argument("--disable-sync")
options.add_argument("--force-color-profile=srgb")
options.add_argument("--metrics-recording-only")
options.add_argument("--no-first-run")
options.add_argument("--safebrowsing-disable-auto-update")
options.add_argument("--enable-automation")
options.add_argument("--password-store=basic")
options.add_argument("--use-mock-keychain")
options.add_argument(f"--user-data-dir={download_dir}")

# إعداد تفضيلات التحميل
options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# دالة لمعالجة الصور باستخدام Selenium
def process_image(image_path):
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=options)
    driver.get("https://www.pixelcut.ai/t/background-remover")
    try:
        wait = WebDriverWait(driver, 20)
        file_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@type="file"]')))
        driver.execute_script("arguments[0].style.display = 'block';", file_input)
        file_input.send_keys(image_path)
        time.sleep(10)
        download_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="root"]/div[2]/div/div/div/div/header/div[2]/button[2]')))
        download_button.click()
        time.sleep(5)
        downloaded_file = max([os.path.join(download_dir, f) for f in os.listdir(download_dir)], key=os.path.getctime)
        return downloaded_file
    except Exception as e:
        print(f"Error processing image: {e}")
    finally:
        driver.quit()

# دالة بدء البوت
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحبًا! أرسل صورة (كملف أو كصورة عادية) لإزالة الخلفية.")

# دالة استقبال الصور (كصورة عادية)
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_path = f"{download_dir}/input.jpg"
    await file.download_to_drive(file_path)
    
    await update.message.reply_text("جاري معالجة الصورة...")
    
    # معالجة الصورة
    processed_image_path = process_image(file_path)
    
    if processed_image_path:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(processed_image_path, "rb"))
    else:
        await update.message.reply_text("حدث خطأ أثناء معالجة الصورة.")

# دالة استقبال الصور (كملف)
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    file_path = f"{download_dir}/{document.file_name}"
    await file.download_to_drive(file_path)

    await update.message.reply_text("جاري معالجة الصورة...")
    
    # معالجة الصورة
    processed_image_path = process_image(file_path)
    
    if processed_image_path:
        await context.bot.send_document(chat_id=update.effective_chat.id, document=open(processed_image_path, "rb"))
    else:
        await update.message.reply_text("حدث خطأ أثناء معالجة الصورة.")

# إعداد البوت
def main():
    # قراءة التوكن من متغيرات البيئة
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("لم يتم تعيين التوكن في متغيرات البيئة!")
    
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    app.run_polling()

if __name__ == "__main__":
    main()