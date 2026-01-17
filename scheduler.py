import schedule
import time
from runner import run_daily_planner

# ----------------------------
# Schedule the planner to run daily at 08:00 AM
# ----------------------------
schedule.every().day.at("08:00").do(run_daily_planner)

print("Planner Agent scheduler started. Waiting for daily run...")

# ----------------------------
# Keep script running
# ----------------------------
while True:
    schedule.run_pending()
    time.sleep(60)
