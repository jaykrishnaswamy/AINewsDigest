# AI News Digest

This project is a workflow designed to fetch, process, and send AI-related news to email and Telegram subscribers. It uses GitHub Actions to automate the entire process, including retrieving data, formatting it, and delivering it via notifications.

## Features
- Automatically fetches the latest AI-related news daily.
- Sends notifications via:
  - **Email** (using secure credentials).
  - **Telegram** (via bot integration).
- Secure handling of sensitive data using GitHub Secrets.

## Workflow Overview
- **Trigger:** The workflow runs daily at 10:00 AM PST or can be triggered manually.
- **Actions:**
  - Sets up a Python environment.
  - Installs dependencies.
  - Executes the `AINews.py` script to send the news digest.

## How to Use
1. **Clone the repository:**
   ```bash
   git clone https://github.com/jaykrishnaswamy/AINewsDigest.git
   ```
2. **Customize the workflow:**
   - Add your own `requirements.txt` and `AINews.py` to fit your needs.

### Secrets
Ensure you set the following secrets in your repository settings:
- `OPENAI_API_KEY`: API key for accessing OpenAI services.
- `SENDER_EMAIL`: Sender's email address for notifications.
- `APP_PASSWORD`: App password for the email account.
- `RECIPIENT_EMAIL`: Email address to receive notifications.
- `TELEGRAM_BOT_TOKEN`: Telegram bot token for sending messages.
- `TELEGRAM_CHAT_ID`: Chat ID for the Telegram recipient.

## Contributing
Contributions are welcome! Feel free to fork the repository, submit pull requests, or report issues.

## License
This project is dual-licensed:

- **[MIT License](LICENSE-MIT.txt)** for open-source use.
- **[Commercial License](LICENSE-COMMERCIAL.txt)** for proprietary/commercial use.

To obtain a commercial license, please contact [jaykrishnaswamy@gmail.com].
