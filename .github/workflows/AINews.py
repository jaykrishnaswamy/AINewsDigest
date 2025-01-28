import feedparser
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import requests

class Config:
    def __init__(self):
        self.credentials = {
            'OPENAI_API_KEY': os.environ['OPENAI_API_KEY'],
            'SENDER_EMAIL': os.environ['SENDER_EMAIL'],
            'APP_PASSWORD': os.environ['APP_PASSWORD'],
            'RECIPIENT_EMAIL': os.environ['RECIPIENT_EMAIL'],
            'TELEGRAM_BOT_TOKEN': os.environ['TELEGRAM_BOT_TOKEN'],
            'TELEGRAM_CHAT_ID': os.environ['TELEGRAM_CHAT_ID']
        }
        self.rss_feeds = {
            'MIT Technology Review - AI': 'https://www.technologyreview.com/feed/',
            'DeepMind Blog': 'https://deepmind.com/blog/feed/basic/',
            'OpenAI Blog': 'https://openai.com/blog/rss/',
            'Google AI Blog': 'http://googleaiblog.blogspot.com/atom.xml',
            'IBM Research Blog - AI': 'https://research.ibm.com/blog/category/artificial-intelligence/feed',
            'FAIR Blog': 'https://research.facebook.com/blog/ai-category/rss/'
        }

    def get_rss_feeds(self):
        return self.rss_feeds

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text):
        try:
            url = f"{self.base_url}/sendMessage"
            max_length = 4096
            messages = [text[i:i+max_length] for i in range(0, len(text), max_length)]

            for message in messages:
                payload = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, json=payload)
                response.raise_for_status()
            return True
        except Exception as e:
            print(f"Telegram notification error: {str(e)}")
            return False

class NewsDigest:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def fetch_rss_feed(self, feed_url, days=1):
        feed = feedparser.parse(feed_url)
        recent_entries = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for entry in feed.entries:
            pub_date = datetime(*entry.published_parsed[:6])
            if pub_date > cutoff_date:
                recent_entries.append({
                    'title': entry.title,
                    'summary': entry.summary,
                    'link': entry.link,
                    'published': pub_date
                })

        return recent_entries[:5]

    def analyze_content(self, entries):
        if not entries:
            return {'summary': 'No recent updates', 'explanation': '', 'sources': []}

        content = "\n\n".join([f"Title: {e['title']}\nSummary: {e['summary']}" for e in entries])

        try:
            summary_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Create a concise summary focusing on key AI developments and their implications."},
                    {"role": "user", "content": f"Summarize these AI news items:\n\n{content}"}
                ],
                max_tokens=500
            )

            explanation_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI expert explaining complex concepts in simple terms."},
                    {"role": "user", "content": f"Extract and explain key AI concepts and terms from these articles, with practical examples:\n\n{content}"}
                ],
                max_tokens=500
            )

            return {
                'summary': summary_response.choices[0].message.content,
                'explanation': explanation_response.choices[0].message.content,
                'sources': [{'title': e['title'], 'link': e['link']} for e in entries]
            }
        except Exception as e:
            return {'summary': f"Error analyzing content: {str(e)}", 'explanation': '', 'sources': []}

def send_email(sender_email, app_password, recipient_email, digest_results):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email

        if all(content['summary'] == 'No recent updates' for content in digest_results.values()):
            msg['Subject'] = f"AI News Digest - No New Updates - {datetime.now().strftime('%Y-%m-%d')}"
            email_body = "There are no recent updates for your AI news digest."
        else:
            msg['Subject'] = f"AI News Digest - {datetime.now().strftime('%Y-%m-%d')}"
            email_body = "Daily AI News Digest:\n\n"
            for source, content in digest_results.items():
                email_body += f"\n{source}:\n"
                email_body += f"SUMMARY:\n{content['summary']}\n\n"
                email_body += f"KEY CONCEPTS EXPLAINED:\n{content['explanation']}\n\n"
                if content.get('sources'):
                    email_body += "Sources:\n"
                    for source in content['sources']:
                        email_body += f"- {source['title']}: {source['link']}\n"
                email_body += "-" * 50 + "\n"

        msg.attach(MIMEText(email_body.encode('utf-8'), 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()

        return "Email sent successfully!"
    except Exception as e:
        return f"Error sending email: {str(e)}"

def format_telegram_message(digest_results):
    if all(content['summary'] == 'No recent updates' for content in digest_results.values()):
        return "🤖 <b>Daily AI News Digest - No New Updates</b>\n\nThere are no recent updates for your AI news digest."
    
    message = "🤖 <b>Daily AI News Digest</b>\n\n"
    for source, content in digest_results.items():
        message += f"📰 <b>{source}</b>\n"
        message += f"<b>Summary:</b>\n{content['summary']}\n\n"
        message += f"<b>Key Concepts:</b>\n{content['explanation']}\n\n"
        if content.get('sources'):
            message += "<b>Sources:</b>\n"
            for source in content['sources']:
                message += f"• <a href='{source['link']}'>{source['title']}</a>\n"
        message += "➖➖➖➖➖➖➖➖\n\n"
    return message

def main():
    try:
        config = Config()
        credentials = config.credentials
        rss_feeds = config.get_rss_feeds()

        digest = NewsDigest(credentials['OPENAI_API_KEY'])
        all_digests = {}

        telegram_notifier = TelegramNotifier(
            credentials['TELEGRAM_BOT_TOKEN'],
            credentials['TELEGRAM_CHAT_ID']
        )

        telegram_notifier.send_message("Starting AI News Digest...")

        for feed_name, feed_url in rss_feeds.items():
            print(f"Fetching {feed_name}...")
            entries = digest.fetch_rss_feed(feed_url)
            if entries:
                analysis = digest.analyze_content(entries)
                all_digests[feed_name] = analysis

        email_result = send_email(
            credentials['SENDER_EMAIL'],
            credentials['APP_PASSWORD'],
            credentials['RECIPIENT_EMAIL'],
            all_digests
        )
        print(email_result)

        telegram_message = format_telegram_message(all_digests)
        telegram_notifier.send_message(telegram_message)
        print("Telegram notification sent successfully!")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")

if __name__ == "__main__":
    main()
