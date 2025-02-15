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
                'key_insights': '',
                'product_innovation': '',
                'key_concepts': '',
                'sources': []
            }

        content = "\n\n".join([f"Title: {e['title']}\nSummary: {e['summary']}" for e in entries])

        try:
            executive_summary_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant creating a concise executive summary of AI news for a technology product executive in the B2B SaaS industry."},
                    {"role": "user", "content": f"Create a concise executive summary in a few sentences capturing the key strategic insights and takeaways from these AI news articles relevant to B2B SaaS product development and decision-making:\n\n{content}"}
                ],
                max_tokens=200
            )

            key_insights_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI analyst extracting key insights from AI news articles relevant to B2B SaaS companies."},
                    {"role": "user", "content": f"Extract key insights from these AI news articles that have strategic implications for B2B SaaS product development, market positioning, and customer success. Focus on trends, best practices, and case studies demonstrating the impact of AI on key business metrics such as revenue growth, customer retention, and operational efficiency:\n\n{content}"}
                ],
                max_tokens=200
            )

            product_innovation_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI strategist identifying product innovation opportunities based on AI news for B2B SaaS companies."},
                    {"role": "user", "content": f"Identify potential product innovation opportunities based on the insights from these AI news articles. Focus on AI applications and use cases specific to the B2B SaaS domain, such as AI-powered personalization, predictive analytics for customer success, chatbots for B2B customer support, and AI-driven marketing automation. Provide actionable recommendations for leveraging AI to enhance product features, streamline operations, and drive innovation:\n\n{content}"}
                ],
                max_tokens=200
            )

            key_concepts_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI expert explaining key AI concepts from news articles relevant to B2B SaaS product executives."},
                    {"role": "user", "content": f"Extract and explain the key AI concepts mentioned in these news articles. Provide concise explanations that distill complex AI concepts into actionable takeaways for B2B SaaS product executives:\n\n{content}"}
                ],
                max_tokens=200
            )

            return {
                'executive_summary': executive_summary_response.choices[0].message.content.strip(),
                'key_insights': key_insights_response.choices[0].message.content.strip(),
                'product_innovation': product_innovation_response.choices[0].message.content.strip(),
                'key_concepts': key_concepts_response.choices[0].message.content.strip(),
                'sources': [{'title': e['title'], 'link': e['link']} for e in entries]
            }
        except Exception as e:
            return {
                'executive_summary': f"Error analyzing content: {str(e)}",
                'key_insights': '',
                'product_innovation': '',
                'key_concepts': '',
                'sources': []
            }

    def is_marketing_content(content):
    # Keyword and phrase analysis
    marketing_keywords = ['exclusive offer', 'limited time', 'buy now', 'special promotion']
    keyword_count = sum([content.lower().count(keyword.lower()) for keyword in marketing_keywords])
    
    # Sentiment analysis
    sentiment = TextBlob(content).sentiment.polarity
    
    # Heuristic rules and patterns
    has_excessive_punctuation = content.count('!') > 3 or content.count('?') > 3
    has_capitalized_words = len([word for word in content.split() if word.isupper()]) > 3
    
    # Combine the indicators
    is_marketing = (keyword_count > 2) or (sentiment > 0.5) or has_excessive_punctuation or has_capitalized_words
    
    return is_marketing

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
            for source, content in digest_results.items():
                email_body += f"Source: {source}\n"
                email_body += f"Executive Summary: {content['executive_summary']}\n\n"
                email_body += f"Key Insights: {content['key_insights']}\n\n"
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

    messages = []
    for source, content in digest_results.items():
        message_parts = []
        message = f"🤖 <b>AI News Digest - {source}</b>\n\n"
        
        executive_summary = f"<b>Executive Summary:</b>\n{content['executive_summary']}\n\n"
        key_insights = f"<b>Key Insights:</b>\n{content['key_insights']}\n\n"
        product_innovation = f"<b>Product Innovation Opportunities:</b>\n{content['product_innovation']}\n\n"
        key_concepts = f"<b>Key Concepts:</b>\n{content['key_concepts']}\n\n"
        
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
