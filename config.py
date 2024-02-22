import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LINE Bot 設定
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
OPENDATA_CWA_GOV = os.environ.get("OPENDATA_CWA_GOV")
