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
            'FAIR Blog': 'https://research.facebook.com/blog/ai-category/rss/',
            'AWS Machine Learning Blog': 'https://aws.amazon.com/blogs/machine-learning/feed/',
            'Microsoft Research Blog - AI': 'https://www.microsoft.com/en-us/research/blog/category/artificial-intelligence/feed/',
            'NVIDIA AI Blog': 'https://blogs.nvidia.com/blog/category/deep-learning/feed/',
            'AI Trends': 'https://aitrends.com/feed/'
        }

    def get_rss_feeds(self):
        return self.rss_feeds

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, text_list):
        for text in text_list:
            try:
                payload = {
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': 'HTML'
                }
                response = requests.post(self.base_url, json=payload)
                response.raise_for_status()
            except Exception as e:
                print(f"Telegram notification error: {str(e)}")
                print(f"Response content: {response.content}")
                return False
        return True

class NewsDigest:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def fetch_rss_feed(self, feed_url, days=7):
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

        return recent_entries[:10]

    def analyze_content(self, entries):
        if not entries:
            return {
                'executive_summary': '',
                'industry_trends': '',
                'product_innovation': '',
                'competitor_analysis': '',
                'regulatory_updates': '',
                'customer_insights': '',
                'strategic_recommendations': '',
                'sources': []
            }

        content = "\n\n".join([f"Title: {e['title']}\nSummary: {e['summary']}" for e in entries])

        try:
            executive_summary_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant creating a concise executive summary of AI news for a technology product executive."},
                    {"role": "user", "content": f"Create a concise executive summary highlighting the most important insights and takeaways from these AI news articles for a technology product executive:\n\n{content}"}
                ],
                max_tokens=200
            )

            industry_trends_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI analyst identifying industry trends and market dynamics related to AI and technology products."},
                    {"role": "user", "content": f"Identify and summarize the latest industry trends, market dynamics, and potential disruptions mentioned in these AI news articles:\n\n{content}"}
                ],
                max_tokens=200
            )

            product_innovation_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI analyst highlighting innovative AI-powered products and use cases."},
                    {"role": "user", "content": f"Identify and showcase innovative AI-powered products, features, or use cases mentioned in these news articles:\n\n{content}"}
                ],
                max_tokens=200
            )

            competitor_analysis_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI analyst providing insights on competitors' AI initiatives and their implications."},
                    {"role": "user", "content": f"Analyze the AI-related moves, initiatives, and strategic shifts of key competitors mentioned in these news articles and their potential implications:\n\n{content}"}
                ],
                max_tokens=200
            )

            regulatory_updates_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI analyst tracking regulatory changes and policy updates related to AI and technology products."},
                    {"role": "user", "content": f"Identify and summarize any regulatory changes, government policies, or legal developments related to AI and technology products mentioned in these news articles:\n\n{content}"}
                ],
                max_tokens=200
            )

            customer_insights_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI analyst extracting customer insights and feedback from news articles."},
                    {"role": "user", "content": f"Extract and summarize relevant customer insights, user feedback, or market research findings mentioned in these AI news articles:\n\n{content}"}
                ],
                max_tokens=200
            )

            strategic_recommendations_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI strategist providing strategic recommendations based on AI news insights."},
                    {"role": "user", "content": f"Based on the analysis of these AI news articles, provide strategic recommendations or actionable insights for a technology product executive:\n\n{content}"}
                ],
                max_tokens=200
            )

            return {
                'executive_summary': executive_summary_response.choices[0].message.content.strip(),
                'industry_trends': industry_trends_response.choices[0].message.content.strip(),
                'product_innovation': product_innovation_response.choices[0].message.content.strip(),
                'competitor_analysis': competitor_analysis_response.choices[0].message.content.strip(),
                'regulatory_updates': regulatory_updates_response.choices[0].message.content.strip(),
                'customer_insights': customer_insights_response.choices[0].message.content.strip(),
                'strategic_recommendations': strategic_recommendations_response.choices[0].message.content.strip(),
                'sources': [{'title': e['title'], 'link': e['link']} for e in entries]
            }
        except Exception as e:
            return {
                'executive_summary': f"Error analyzing content: {str(e)}",
                'industry_trends': '',
                'product_innovation': '',
                'competitor_analysis': '',
                'regulatory_updates': '',
                'customer_insights': '',
                'strategic_recommendations': '',
                'sources': []
            }

    def analyze_sentiment(self, text):
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        return sentiment

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
            email_body += "EXECUTIVE SUMMARY:\n"
            for source, content in digest_results.items():
                email_body += f"{content['executive_summary']}\n\n"
            email_body += "-" * 50 + "\n\n"

            email_body += "INDUSTRY TRENDS AND MARKET ANALYSIS:\n"
            for source, content in digest_results.items():
                email_body += f"{content['industry_trends']}\n\n"
            email_body += "-" * 50 + "\n\n"

            email_body += "PRODUCT INNOVATION AND USE CASES:\n"
            for source, content in digest_results.items():
                email_body += f"{content['product_innovation']}\n\n"
            email_body += "-" * 50 + "\n\n"

            email_body += "COMPETITOR ANALYSIS:\n"
            for source, content in digest_results.items():
                email_body += f"{content['competitor_analysis']}\n\n"
            email_body += "-" * 50 + "\n\n"

            email_body += "REGULATORY AND POLICY UPDATES:\n"
            for source, content in digest_results.items():
                email_body += f"{content['regulatory_updates']}\n\n"
            email_body += "-" * 50 + "\n\n"

            email_body += "CUSTOMER INSIGHTS AND FEEDBACK:\n"
            for source, content in digest_results.items():
                email_body += f"{content['customer_insights']}\n\n"
            email_body += "-" * 50 + "\n\n"

            email_body += "STRATEGIC RECOMMENDATIONS:\n"
            for source, content in digest_results.items():
                email_body += f"{content['strategic_recommendations']}\n\n"
            email_body += "-" * 50 + "\n\n"

            email_body += "SOURCES:\n"
            for source, content in digest_results.items():
                if content.get('sources'):
                    email_body += f"{source}:\n"
                    for article in content['sources']:
                        email_body += f"- {article['title']}: {article['link']}\n"
                    email_body += "\n"
            email_body += "-" * 50 + "\n"

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

    messages = []
    message = "🤖 <b>AI News Digest for Technology Product Executives</b>\n\n"

    message += "<b>Executive Summary:</b>\n"
    for source, content in digest_results.items():
        message += f"{content['executive_summary']}\n\n"
    messages.append(message)

    message = "<b>Industry Trends and Market Analysis:</b>\n"
    for source, content in digest_results.items():
        message += f"{content['industry_trends']}\n\n"
    messages.append(message)

    message = "<b>Product Innovation and Use Cases:</b>\n"
    for source, content in digest_results.items():
        message += f"{content['product_innovation']}\n\n"
    messages.append(message)

    message = "<b>Competitor Analysis:</b>\n"
    for source, content in digest_results.items():
        message += f"{content['competitor_analysis']}\n\n"
    messages.append(message)

    message = "<b>Regulatory and Policy Updates:</b>\n"
    for source, content in digest_results.items():
        message += f"{content['regulatory_updates']}\n\n"
    messages.append(message)

    message = "<b>Customer Insights and Feedback:</b>\n"
    for source, content in digest_results.items():
        message += f"{content['customer_insights']}\n\n"
    messages.append(message)

    message = "<b>Strategic Recommendations:</b>\n"
    for source, content in digest_results.items():
        message += f"{content['strategic_recommendations']}\n\n"
    messages.append(message)

    message = "<b>Sources:</b>\n"
    for source, content in digest_results.items():
        if content.get('sources'):
            message += f"<b>{source}:</b>\n"
            for article in content['sources']:
                message += f"• <a href='{article['link']}'>{article['title']}</a>\n"
            message += "\n"
    messages.append(message)

    return messages

def get_sentiment_label(sentiment):
    if sentiment > 0.3:
        return "Positive"
    elif sentiment < -0.3:
        return "Negative"
    else:
        return "Neutral"

def get_sentiment_emoji(sentiment):
    if sentiment > 0.3:
        return "😊"
    elif sentiment < -0.3:
        return "😔"
    else:
        return "😐"

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
                    if entries:
                        print(f"Analyzing content for {feed_name}...")
                        analysis = digest.analyze_content(entries)
                        all_digests[feed_name] = analysis
                    break
                except Exception as e:
                    print(f"Error fetching {feed_name}: {str(e)}. Retries left: {retries}")
                    retries -= 1
                    time.sleep(5)  # Wait for 5 seconds before retrying

        print("Sending email notification...")
        email_result = send_email(
            credentials['SENDER_EMAIL'],
            credentials['APP_PASSWORD'],
            credentials['RECIPIENT_EMAIL'],
            all_digests
        )
        print(email_result)

        print("Sending Telegram notification...")
        telegram_message = format_telegram_message(all_digests)
        telegram_notifier.send_message(telegram_message)
        print("Telegram notification sent successfully!")

    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        raise e

if __name__ == "__main__":
    main()
