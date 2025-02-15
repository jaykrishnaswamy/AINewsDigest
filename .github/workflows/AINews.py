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
        recent_entries =
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
                'executive_summary': {'key_takeaways':},
                'key_insights':,
                'product_innovation': '',
                'key_concepts': '',
                'sources':
            }

        content = "\n\n".join([f"Title: {e['title']}\nSummary: {e['summary']}" for e in entries])

        try:
            executive_summary_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant creating a concise executive summary of AI news for a technology product executive in the B2B SaaS industry."},
                    {"role": "user", "content": f"Create a concise executive summary with a list of key takeaways capturing the key strategic insights from these AI news articles relevant to B2B SaaS product development and decision-making:\n\n{content}"}
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
                'executive_summary': {'key_takeaways': executive_summary_response.choices.message.content.strip().split('\n')},
                'key_insights': key_insights_response.choices.message.content.strip().split('\n'),
                'product_innovation': product_innovation_response.choices.message.content.strip(),
                'key_concepts': key_concepts_response.choices.message.content.strip(),
                'sources': [{'title': e['title'], 'link': e['link']} for e in entries]
            }
        except Exception as e:
            return {
                'executive_summary': {'key_takeaways':},
                'key_insights':,
                'product_innovation': f"Error analyzing content: {str(e)}",
                'key_concepts': '',
                'sources':
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
