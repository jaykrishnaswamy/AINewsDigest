import feedparser
from openai import OpenAI
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os
import requests
import time
from textblob import TextBlob

class Config:
    #... (Config class remains unchanged)

class TelegramNotifier:
    #... (TelegramNotifier class remains unchanged)

class NewsDigest:
    #... (NewsDigest class with the changes as discussed previously)

def send_email(sender_email, app_password, recipient_email, digest_results):
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email

        if all(not content for content in digest_results.values()):
            msg['Subject'] = f"AI News Digest - No New Updates - {datetime.now().strftime('%Y-%m-%d')}"
            email_body = "There are no recent updates for your AI news digest."
        else:
            msg['Subject'] = f"AI News Digest - {datetime.now().strftime('%Y-%m-%d')}"
            email_body = "AI News Digest for Technology Product Executives\n\n"
            for source, content in digest_results.items():
                email_body += f"Source: {source}\n"
                email_body += f"Key Takeaways: {', '.join(content['executive_summary']['key_takeaways'])}\n\n"  # Corrected line
                email_body += f"Key Insights: {', '.join(content['key_insights'])}\n\n"  # Corrected line
                email_body += f"Product Innovation Opportunities: {content['product_innovation']}\n\n"
                email_body += f"Key Concepts: {content['key_concepts']}\n\n"
                email_body += "-" * 50 + "\n\n"

        body = MIMEText(email_body, 'plain', 'utf-8')
        msg.attach(body)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.send_message(msg)
        server.quit()

        return "Email sent successfully!"
    except Exception as e:
        return f"Error sending email: {str(e)}"

def format_telegram_message(digest_results):
    if all(not content for content in digest_results.values()):
        return ["🤖 <b>AI News Digest - No New Updates</b>\n\nThere are no recent updates for your AI news digest."]

    messages =
    for source, content in digest_results.items():
        message_parts =
        message = f"🤖 <b>AI News Digest - {source}</b>\n\n"
        
        executive_summary = f"<b>Executive Summary:</b>\n{', '.join(content['executive_summary']['key_takeaways'])}\n\n" # Corrected line
        key_insights = f"<b>Key Insights:</b>\n{', '.join(content['key_insights'])}\n\n"  # Corrected line
        product_innovation = f"<b>Product Innovation Opportunities:</b>\n{content['product_innovation']}\n\n"
        key_concepts = f"<b>Key Concepts:</b>\n{content['key_concepts']}\n\n"
        
        #... (Rest of the message formatting logic remains the same)
        if len(message + executive_summary) <= 4096:
            message += executive_summary
        else:
            message_parts.append(message)
            message = executive_summary
        
        if len(message + key_insights) <= 4096:
            message += key_insights
        else:
            message_parts.append(message)
            message = key_insights
        
        if len(message + product_innovation) <= 4096:
            message += product_innovation
        else:
            message_parts.append(message)
            message = product_innovation
        
        if len(message + key_concepts) <= 4096:
            message += key_concepts
        else:
            message_parts.append(message)
            message = key_concepts
        
        message_parts.append(message)
        messages.extend(message_parts)

    return messages


def get_sentiment_label(sentiment):
    #... (remains unchanged)

def get_sentiment_emoji(sentiment):
    #... (remains unchanged)

def is_marketing_content(content):
    #... (remains unchanged)

def summarize_analysis(analysis):
    summary = {}
    for source, data in analysis.items():
        if 'executive_summary' in data and 'key_insights' in data: #Check if the required keys are present
            summary[source] = {
                "Key Takeaways": data.get('executive_summary', {}).get('key_takeaways',),  # Handle missing keys safely
                "Key Insights": data.get('key_insights',)
            }
        else: # Handle the case when summary and insights are not present
            summary[source] = "Analysis Missing or Incomplete"
    return summary


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

        telegram_notifier.send_message(["Starting AI News Digest..."])

        print("Fetching RSS feeds...")
        for feed_name, feed_url in rss_feeds.items():
            retries = 3
            while retries > 0:
                print(f"Fetching {feed_name}...")
                try:
                    entries = digest.fetch_rss_feed(feed_url)
                    filtered_entries = [entry for entry in entries if not is_marketing_content(entry['summary'])]
                    if filtered_entries:
                        print(f"Analyzing content for {feed_name}...")
                        analysis = digest.analyze_content(filtered_entries)
                        all_digests[feed_name] = analysis
                    break
                except Exception as e:
                    print(f"Error fetching {feed_name}: {str(e)}. Retries left: {retries}")
                    retries -= 1
                    time.sleep(5)  # Wait for 5 seconds before retrying

        summarized_digests = summarize_analysis(all_digests)

        print("Sending email notification...")
        email_result = send_email(
            credentials['SENDER_EMAIL'],
            credentials['APP_PASSWORD'],
            credentials['RECIPIENT_EMAIL'],
            summarized_digests  # Use summarized digests
        )
        print(email_result)

        print("Sending Telegram notification...")
        telegram_message = format_telegram_message(summarized_digests)  # Use summarized digests
        telegram_notifier.send_message(telegram_message)
        print("Telegram notification sent successfully!")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        raise e

if __name__ == "__main__":
    main()
