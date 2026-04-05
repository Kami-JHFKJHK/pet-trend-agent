import requests
import smtplib
import json
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ============================================================
#  CONFIGURATION
#  On your laptop: fill these in directly
#  On Railway: set these as Environment Variables instead
# ============================================================
GMAIL_ADDRESS  = os.environ.get("GMAIL_ADDRESS",  "your_email@gmail.com")
GMAIL_APP_PASS = os.environ.get("GMAIL_APP_PASS", "xxxx xxxx xxxx xxxx")
ALERT_EMAIL    = os.environ.get("ALERT_EMAIL",    "your_email@gmail.com")
GROQ_KEY       = os.environ.get("GROQ_KEY",       "gsk_xxxxxxxxxxxxxxxx")
RAPIDAPI_KEY   = os.environ.get("RAPIDAPI_KEY",   "your_rapidapi_key")
# ============================================================

PET_KEYWORDS = [
    "petsupplies", "dogaccessories", "cataccessories",
    "petfood", "dogbed", "cattoy", "petgrooming",
    "slowfeederbowl", "catwaterfountain", "dogharness"
]

def fetch_instagram_trends():
    results = []
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "instagram-scraper-api2.p.rapidapi.com"
    }
    for keyword in PET_KEYWORDS[:5]:
        try:
            url = "https://instagram-scraper-api2.p.rapidapi.com/v1/hashtag"
            response = requests.get(url, headers=headers, params={"hashtag": keyword}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("items", [])
                for post in posts[:3]:
                    results.append({
                        "keyword": keyword,
                        "likes": post.get("like_count", 0),
                        "comments": post.get("comment_count", 0),
                        "caption": post.get("caption", {}).get("text", "")[:200] if post.get("caption") else "",
                        "platform": "Instagram"
                    })
        except Exception as e:
            print(f"  Warning: Could not fetch {keyword}: {e}")
        time.sleep(1)
    return results

def analyze_with_groq(trend_data):
    prompt = f"""You are a product trend analyst for a pet supplies seller in the USA.
Focus on trends from US-based social media, US consumer behavior,
and products popular on Amazon USA, TikTok USA, and Instagram USA.

Here is social media trend data collected right now:

{json.dumps(trend_data, indent=2)}

Please analyze this and provide a clear report with:
1. Top 5 trending pet supply products right now (ranked by buzz)
2. Why each product is trending (1 sentence each)
3. Demand level for each: High / Medium / Low
4. Should the seller stock it: Yes / Maybe / No
5. One action to take today

Be practical and concise. This will be sent as an email report.
"""
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            return f"Groq analysis failed: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Groq connection error: {e}"

def send_email(analysis_text, product_count):
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    subject = f"Pet Supplies Trend Report - {now}"
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 620px; margin: auto; padding: 20px;">
      <h2 style="color: #1d9e75; border-bottom: 2px solid #1d9e75; padding-bottom: 10px;">
        Pet Supplies Trend Report
      </h2>
      <p style="color: #888; font-size: 13px;">
        Generated: {now} &nbsp;|&nbsp; Products scanned: {product_count}
      </p>
      <div style="background: #f9f9f9; padding: 16px; border-radius: 8px;
                  font-size: 14px; line-height: 1.8; color: #333;
                  white-space: pre-wrap; margin: 16px 0;">
{analysis_text}
      </div>
      <p style="color: #bbb; font-size: 12px; margin-top: 24px;
                border-top: 1px solid #eee; padding-top: 12px;">
        Sent automatically by your Pet Supplies Trend Agent (powered by Groq AI - Free)
      </p>
    </body>
    </html>
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = ALERT_EMAIL
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
            server.sendmail(GMAIL_ADDRESS, ALERT_EMAIL, msg.as_string())
        print(f"  Email sent to {ALERT_EMAIL}")
    except Exception as e:
        print(f"  Email failed: {e}")

def run_once():
    print(f"\n{'='*50}")
    print(f" Pet Supplies Trend Agent")
    print(f" Started: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")
    print(f"{'='*50}\n")

    print("Step 1: Fetching Instagram trends...")
    trend_data = fetch_instagram_trends()
    if not trend_data:
        print("  No Instagram data, using keyword list...")
        trend_data = [{"keyword": k, "platform": "web", "signal": "trending"} for k in PET_KEYWORDS]
    print(f"  Collected {len(trend_data)} data points\n")

    print("Step 2: Analyzing with Groq AI...")
    analysis = analyze_with_groq(trend_data)
    print("  Analysis complete\n")

    print("Step 3: Sending email report...")
    send_email(analysis, len(trend_data))

    print(f"\nCycle complete! Next run in 1 hour.")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    print("Pet Supplies Trend Agent starting up...")
    print("Sending email reports every hour automatically.")
    print("Press Ctrl+C to stop.\n")

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"Error in cycle: {e}")
            print("Trying again in 1 hour...")
        time.sleep(3600)
