from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os
import time

# تحميل المتغيرات من ملف .env (للتطوير المحلي)
load_dotenv()

# المسار الجديد لمجلد التحميل
download_dir = "./downloads"

# إنشاء مجلد التحميل إذا لم يكن موجودًا
os.makedirs(download_dir, exist_ok=True)

# إعداد ChromeDriver باستخدام webdriver-manager
chrome_driver_path = ChromeDriverManager().install()

# إعداد خيارات Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--remote-debugging-port=9222")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-background-networking")
chrome_options.add_argument("--disable-background-timer-throttling")
chrome_options.add_argument("--disable-backgrounding-occluded-windows")
chrome_options.add_argument("--disable-breakpad")
chrome_options.add_argument("--disable-client-side-phishing-detection")
chrome_options.add_argument("--disable-component-update")
chrome_options.add_argument("--disable-default-apps")
chrome_options.add_argument("--disable-domain-reliability")
chrome_options.add_argument("--disable-features=AudioServiceOutOfProcess")
chrome_options.add_argument("--disable-hang-monitor")
chrome_options.add_argument("--disable-ipc-flooding-protection")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument("--disable-prompt-on-repost")
chrome_options.add_argument("--disable-renderer-backgrounding")
chrome_options.add_argument("--disable-sync")
chrome_options.add_argument("--force-color-profile=srgb")
chrome_options.add_argument("--metrics-recording-only")
chrome_options.add_argument("--no-first-run")
chrome_options.add_argument("--safebrowsing-disable-auto-update")
chrome_options.add_argument("--enable-automation")
chrome_options.add_argument("--password-store=basic")
chrome_options.add_argument("--use-mock-keychain")
chrome_options.add_argument(f"--user-data-dir={download_dir}")

# إعداد تفضيلات التحميل
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# دالة لمعالجة الصور باستخدام Selenium
def process_image(image_path):
    driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
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
    file_path = f"{download_dir}/input.jpg"  # استخدام المسار الجديد
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
    file_path = f"{download_dir}/{document.file_name}"  # استخدام المسار الجديد
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

    # استخدام Polling
    app.run_polling()

if __name__ == "__main__":
    main()
