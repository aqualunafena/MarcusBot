# MarcusBot

A powerful Discord AI bot built with Python that integrates Google Gemini AI for intelligent conversations and image generation.

## Features

- 🤖 **AI-Powered Chat**: Responds to messages using Google Gemini AI
- 🎨 **Image Generation**: Creates images based on text descriptions
- 🎯 **Smart Triggers**: Responds to various prefixes (M!, m!, !M, !m, m?, M?)
- 🎭 **Fun Responses**: Brooklyn 99 quotes and random interactions
- 🎬 **GIF Integration**: Sends relevant GIFs using Tenor API
- 🔄 **Network Resilience**: Automatic reconnection and retry logic for all network operations
- 📊 **Health Monitoring**: Continuous network connectivity monitoring

## Prerequisites

- Python 3.9 or higher
- Discord Bot Token
- Google Gemini API Key
- Tenor API Key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/MarcusBot.git
cd MarcusBot
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```env
DISCORD_KEY=your_discord_bot_token_here
GEMINI_KEY=your_gemini_api_key_here
TENOR_KEY=your_tenor_api_key_here
DISCORD_GUILD=your_discord_server_name_here
```

## Getting API Keys

### Discord Bot Token
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the Bot section and copy the token

### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an API key

### Tenor API Key
1. Go to [Tenor Developer Dashboard](https://tenor.com/developer/dashboard)
2. Create an application and get your API key

## Usage

Run the bot:
```bash
python3 bot.py
```

### Bot Commands

- **Chat with AI**: Use prefixes `M!`, `m!`, `!M`, `!m`, `m?`, `M?` followed by your message
- **Generate Images**: Include words like "image", "picture", "photo" in your message
- **Brooklyn 99 Quotes**: Type `99!`
- **Console Messaging**: Type `!!@@` (admin feature)

### Example Interactions

```
M! Hello, how are you?
m! Generate an image of a sunset over mountains
M? What's the weather like?
99!
```

## Network Resilience Features

- **Automatic Reconnection**: Bot automatically reconnects if WiFi disconnects
- **Retry Logic**: All API calls have exponential backoff retry mechanisms
- **Health Monitoring**: Periodic network connectivity checks
- **Graceful Error Handling**: Informative error messages and fallback responses

## Architecture

- **Main Bot Logic**: `bot.py` - Core Discord bot functionality
- **Helper Commands**: `commands.py` - Utility functions
- **Dependencies**: `requirements.txt` - Python package requirements
- **Environment Config**: `.env` - API keys and configuration (not in repo)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

Built with ❤️ by Jaden Lee

## Acknowledgments

- Google Gemini AI for intelligent responses
- Discord.py for Discord integration
- Tenor for GIF functionality
- NLTK for natural language processing
