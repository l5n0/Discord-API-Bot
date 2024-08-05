# Discord User Data Fetcher

## Important
It still has some bugs. I have to fix them, but at the moment it works. 

## Setup

### Prerequisites
- Python 3.8+
- Discord bot token
- `.env` file with the following:

```bash
BOT_TOKEN=your_discord_bot_token
```

### Installation
1. Clone the repository.
2. Navigate to the project directory.
3. Install dependencies:
 ```bash
 pip install Flask discord.py python-dotenv aiohttp
```
### Usage

1. Run the application:

``` bash

python app.py
```
2. Access the web interface at:

```arduino
http://localhost:5000
```

3. Enter a Discord user ID to fetch user data.

### Project Structure

- app.py: Main application file.
- templates/index.html: HTML template.
- static/styles.css: CSS for styling.

### Notes

- The bot must be in at least one server to fetch guild member data.
- If a user is not in the guild, basic info will be fetched from the Discord API.
