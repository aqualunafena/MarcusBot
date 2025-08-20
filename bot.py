# Jaden Lee
# bot.py
# Custom, free-tiered AI bot

# Future Updates:
# 1. add functionality to create a private channel with desired members
# 2. add functionality to simultaneous add to chat history and output an image
# 3. add functionality to send birthday message
# 4. refactor code by adding more commands to commands.py
# 5. add "now that the niceties are out of the way, let's get to business"
# 6. add functionality to scrape images from Microsoft Designer for image generation

import io
import os
import discord
import random
import requests
import json
import nltk
import aiohttp
import asyncio
import datetime
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from autocorrect import Speller
from dotenv import load_dotenv
from http.client import HTTPException
load_dotenv()

# Import additional custom commands
import commands

# Download the necessary dependencies for nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')

# Get Discord token
discord_key = os.getenv('DISCORD_KEY')

# Get Gemini token
google_key = os.getenv('GEMINI_KEY')

# Get Tenor token
tenor_key = os.getenv('TENOR_KEY')

# Initiate a Discord client
intents = discord.Intents.default()  # get an instance of Intents
intents.members = True  # set member Intents to True
intents.message_content = True  # set message content Intents to True
client = discord.Client(intents=intents)

# Define the models that will be used
chat_model_name = "gemini-2.0-flash"    # Model for keeping chat history
image_model_name = "gemini-2.0-flash-exp-image-generation"  # Model for generating images

# Initiate a Google client
google_client = genai.Client(api_key=google_key)

# Initiate a chat to keep history
chat = google_client.chats.create(model=chat_model_name)

# Output information about the bot joining the server

@client.event
async def on_member_join(member):
    """Send the user a DM upon joining the server"""
    await member.create_dm()
    await do_try(member.dm_channel.send(f'Hi {member.name}, welcome to Project Lucid.'))

@client.event
async def on_message(message):
    """Waits for a message to be sent.
    Send a response depending on the message content."""

    if message.author == client.user:   # if the message is by the bot, escape the function
        return

    baseball_chance = 0.05      # specify a probability for sending "Baseball, huh?"
    gif_chance = 0.05           # specify a probability for sending a random GIF
    niceties_chance = 0.03      # specify a probability for sending "now that the niceties are out of the way, let's get to business"

    # Randomly output "Baseball, huh?"
    if commands.random_chance(baseball_chance):
        await do_try(message.channel.send("Baseball, huh?"))

    # Randomly send a GIF
    if commands.random_chance(gif_chance):
        await get_gif(message)

    # Send a message from terminal
    if message.content == '!!@@':
        await send_from_console()

    ## Brooklyn 99 response
    if message.content == '99!':
        brooklyn_99_quotes = [
            'Sergeant, are you familiar with the Hungarian fencing move, Hossz Gorcs?',
            'Bingpot!',
            'Cool. Cool cool cool cool cool cool, no doubt no doubt no doubt no doubt.'
            'Well, here are the orchids that I can name: Baclardia, Belagladis, Bentamia, Bephyllax, Depotium, Evotella.',
            'VIN-DI-CATION!'
        ]
        response = random.choice(brooklyn_99_quotes)
        await do_try(message.channel.send(response))

    ## Google Gemini Response
    prefixes = ["M!", "m!", "!M", "!m", "m?", "M?"]   # MarcusBot prefixes
    if any([prefix in message.content for prefix in prefixes]) or \
            client.user.mentioned_in(message) or \
            (not message.mention_everyone and hasattr(message, "referenced_message")):

        # Strip the message text of user id
        if client.user.mentioned_in(message):
            message.content = message.content.replace(f'<@{client.user.id}>',"")

        # Correct any spelling errors before getting a response, which is necessary to trigger the correct model
        token_list = await correct_token(message)
        image_token_words = ["image",
                             "picture",
                             "photo",
                             "cartoon",
                             "sketch",
                             "drawing",
                             "painting",
                             "photograph",
                             "illustration"]

        niceties_token_words = ["hi",
                                "hello",
                                "hey",
                                "sup",
                                "what's up",
                                "how are you?"]

        if len(message.attachments) != 0:
            image_url = message.attachments[0].url # Get image url
            
            # Download image with retry logic
            async def download_image():
                response = requests.get(image_url, timeout=30)
                if response.status_code == 200:
                    return Image.open(BytesIO(response.content))
                else:
                    raise requests.exceptions.HTTPError(f"HTTP {response.status_code}")
            
            try:
                input_img = await retry_with_backoff(download_image, max_retries=3, initial_delay=5, max_delay=30, operation_name="Image download")
            except Exception:
                input_img = ""
        else:
            input_img = ""

        if any([token_word in token_list for token_word in image_token_words]):
            image_instruction = "Speak like you are texting the user. "
            model_name = image_model_name
            randomness = 0.9        # between 0.1 and 2.0; select the temperature of the model output
            
            # Generate content with retry logic
            async def generate_image_content():
                return google_client.models.generate_content(
                    model=model_name,
                    contents=[image_instruction + message.content, input_img],
                    config=types.GenerateContentConfig(
                        response_modalities=['Text', 'Image'],
                        temperature=randomness,
                    )
                )
            
            try:
                response = await retry_with_backoff(generate_image_content, operation_name="Gemini image generation")
            except Exception:
                await message.channel.send("Sorry, I'm having trouble generating content right now. Please try again later.")
                return
        else:
            chat_instruction = (
                "Use at most 2000 characters. "
                "You're very cool-headed. "
                "Speak like you are texting the user. "
            )
            
            # Send chat message with retry logic
            async def send_chat_message():
                return chat.send_message(chat_instruction + message.content)
            
            try:
                response = await retry_with_backoff(send_chat_message, operation_name="Gemini chat")
            except Exception:
                await message.channel.send("Sorry, I'm having trouble responding right now. Please try again later.")
                return

        # Parse the output response and send it
        output_text = await parse_output(prefixes, message, response)

        try:
            await do_try(message.channel.send(output_text))
        except HTTPException:
            print('Too many requests sent. Please try sending a message to the bot in 20-40 minutes.')

        # Get the path to the image
        cur_directory = os.getcwd()
        image_name = 'generated-image.png'
        path_to_image = os.path.join(cur_directory,image_name)

        # Slice into the response to get the image data
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(part.text)
            elif part.inline_data is not None:
                try:
                    ## Saves the image generated by Gemini
                    image = Image.open(BytesIO(part.inline_data.data))
                    image.save(path_to_image)
                    image.show()

                    ## Open the image as read and have the bot send it
                    with open(path_to_image, 'rb') as f:
                        picture = discord.File(f)
                        await message.channel.send(file=picture)
                    os.remove(path_to_image)
                except FileNotFoundError:
                    print(f"Error: Image file '{path_to_image}' not found.")
                except Exception as e:
                    print(f"An error occurred: {e}")
            # if part.text is not None and part.inline_data is None:
            #     gen_error_message = "There may have been an error in generating your image (err: 2). "
            #     print(gen_error_message)
            #     await message.channel.send(gen_error_message)

@client.event
async def get_gif(message):
    # Set the apikey and limit
    lmt = 8   # limit how many GIFs are loaded at once
    ckey = "marcus_bot_app"

    # Select a search term
    tokens = word_tokenize(message.content)
    parts_of_speech_list = pos_tag(tokens)
    nouns = [word for word, parts_of_speech in parts_of_speech_list if parts_of_speech.startswith('NN')]
    search_term = random.choice(nouns)

    # Get the top 8 GIFs for the search term with retry logic
    async def fetch_gifs():
        r = requests.get(
            "https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s" \
            % (search_term, tenor_key, ckey, lmt),
            timeout=30
        )
        if r.status_code == 200:
            return json.loads(r.content)
        else:
            raise requests.exceptions.HTTPError(f"Tenor API returned status {r.status_code}")
    
    try:
        top_8gifs = await retry_with_backoff(fetch_gifs, operation_name="Tenor API")
    except Exception:
        print("Failed to fetch GIFs from Tenor API")
        return

    if not top_8gifs or "results" not in top_8gifs or not top_8gifs["results"]:
        print("No GIFs found from Tenor API")
        return
        
    result = top_8gifs["results"]
    random_result = random.choice(result)
    gif_url = random_result["media_formats"]["gif"]["url"]

    # Send the GIF from the url
    image_name = 'tenor.gif'
    async with aiohttp.ClientSession() as session:
        async with session.get(gif_url) as resp:
            if resp.status != 200:
                return await message.channel.send('Could not download file.')
            image = io.BytesIO(await resp.read())
            image_file = discord.File(image, image_name)
            await message.channel.send(file=image_file)

@client.event
async def send_from_console():
    marcus_bot_channel_id = 1354446865919377570
    run = True
    while run:
        message = input('Enter message: ')
        if "!!!" in message:
            return
        channel = client.get_channel(marcus_bot_channel_id)
        await channel.send(message)

async def correct_token(message):
    spell = Speller()
    corrected_tokens = []
    words = message.content.split()
    for word in words:
        corrected_token = spell(word)
        if corrected_token is not None:
            corrected_tokens.append(corrected_token)
        else:
            corrected_tokens.append(word)
    return corrected_tokens

async def parse_output(key_phrases, message, response):
    """Parse the bot output response"""
    output_text = ""
    error_message = "There may have been an error in generating your image (err: 1). "
    for index, element in enumerate(key_phrases):
        if element in message.content:
            bot_prefix = key_phrases[index]
            try:
                stringIndex = response.text.find(bot_prefix)
                if stringIndex != -1:
                    output_text = response.text[:stringIndex]
                else:
                    output_text = response.text
            except AttributeError:
                print(error_message)
                output_text = error_message
    if len(output_text) == 0: # if the message was a reply and does not include the prefix
        output_text = response.text
    return output_text  # Send the text from the response

# Centralized retry helper functions
async def retry_with_backoff(func, max_retries=3, initial_delay=10, max_delay=60, operation_name="operation"):
    """Generic retry function with exponential backoff for any async operation"""
    for attempt in range(max_retries):
        try:
            return await func()
        except (OSError, ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
            if attempt < max_retries - 1:
                retry_delay = min(initial_delay * (2 ** attempt), max_delay)
                print(f"{operation_name} network error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                print(f"{operation_name} failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                retry_delay = min(initial_delay * (2 ** attempt), max_delay)
                print(f"{operation_name} error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                print(f"{operation_name} failed after {max_retries} attempts: {e}")
                raise

def retry_sync_with_backoff(func, max_retries=3, initial_delay=10, max_delay=60, operation_name="operation"):
    """Generic retry function with exponential backoff for synchronous operations"""
    import time
    for attempt in range(max_retries):
        try:
            return func()
        except (OSError, ConnectionError, TimeoutError, requests.exceptions.RequestException) as e:
            if attempt < max_retries - 1:
                retry_delay = min(initial_delay * (2 ** attempt), max_delay)
                print(f"{operation_name} network error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"{operation_name} failed after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                retry_delay = min(initial_delay * (2 ** attempt), max_delay)
                print(f"{operation_name} error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"{operation_name} failed after {max_retries} attempts: {e}")
                raise

async def do_try(function, max_retries = 5):
    """Enhanced Discord message sending with retry logic"""
    for attempt in range(max_retries):
        try:
            return await function
        except discord.errors.HTTPException as e:
            if e.status == 429:
                retry_after = 15*60   # retry reconnecting after 20 minutes
                print(f"Rate limited. Retrying in {retry_after} seconds...")
                await asyncio.sleep(retry_after)
            else:
                raise
        except (OSError, ConnectionError, TimeoutError) as e:
            if attempt < max_retries - 1:
                retry_delay = min(30 * (2 ** attempt), 300)  # Exponential backoff
                print(f"Network error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                print(f"Network error after {max_retries} attempts: {e}")
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                retry_delay = min(30 * (2 ** attempt), 300)
                print(f"Unexpected error: {e}. Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(retry_delay)
            else:
                print(f"Error after {max_retries} attempts: {e}")
                raise
    raise Exception("Max connection attempts reached. Please wait another 20 minutes.")

# Network resilience and reconnection handling
@client.event
async def on_disconnect():
    """Handle bot disconnection gracefully"""
    print(f"[{datetime.datetime.now()}] Bot disconnected from Discord")
    print("Attempting to reconnect...")

@client.event
async def on_resumed():
    """Handle bot reconnection"""
    print(f"[{datetime.datetime.now()}] Bot reconnected to Discord")
    print(f"Resumed session with {len(client.guilds)} guilds")

@client.event
async def on_error(event, *args, **kwargs):
    """Handle any errors that occur"""
    print(f"[{datetime.datetime.now()}] Error in event {event}: {args} {kwargs}")

# Network health monitoring
async def network_health_check():
    """Periodically check network connectivity"""
    while True:
        try:
            # Test basic internet connectivity using a simple endpoint
            response = requests.get("https://httpbin.org/status/200", timeout=10)
            if response.status_code == 200:
                print(f"[{datetime.datetime.now()}] Network health check: OK")
            else:
                print(f"[{datetime.datetime.now()}] Network health check: HTTP {response.status_code}")
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Network health check failed: {e}")
        
        # Check every 5 minutes
        await asyncio.sleep(300)

# Start network monitoring when bot is ready
@client.event
async def on_ready():
    guild_name = os.getenv('DISCORD_GUILD')
    guild = discord.utils.get(client.guilds, name=guild_name)
    print(f'{client.user} has connected to Discord!')  # Indicate that the bot has connected to the guild
    print(f'{client.user} is connected to the following guilds:\n')
    
    if guild:
        print(f'{guild.name} (id: {guild.id})')
        print(f'There are {len(guild.members)} members')
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')
    else:
        print(f'Guild "{guild_name}" not found. Available guilds:')
        for g in client.guilds:
            print(f' - {g.name} (id: {g.id})')
    
    # Start network health monitoring
    asyncio.create_task(network_health_check())
    print("Network health monitoring started")

# Enhanced error handling for network issues
async def run_bot_with_retry():
    """Run the bot with automatic reconnection on network failures"""
    max_retries = 10
    retry_delay = 30  # Start with 30 seconds
    
    for attempt in range(max_retries):
        try:
            print(f"[{datetime.datetime.now()}] Attempt {attempt + 1}/{max_retries} to connect to Discord...")
            await client.start(discord_key)
            break  # If we get here, connection was successful
            
        except discord.errors.ConnectionClosed as e:
            print(f"[{datetime.datetime.now()}] Connection closed: {e}")
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)  # Exponential backoff, max 5 minutes
            else:
                print("Max retry attempts reached. Exiting.")
                raise
                
        except discord.errors.HTTPException as e:
            print(f"[{datetime.datetime.now()}] HTTP error: {e}")
            if e.status == 429:  # Rate limited
                retry_after = e.retry_after or 60
                print(f"Rate limited. Waiting {retry_after} seconds...")
                await asyncio.sleep(retry_after)
            elif attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)
            else:
                print("Max retry attempts reached. Exiting.")
                raise
                
        except (OSError, ConnectionError, TimeoutError) as e:
            print(f"[{datetime.datetime.now()}] Network error: {e}")
            if attempt < max_retries - 1:
                print(f"Network issue detected. Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)
            else:
                print("Max retry attempts reached. Exiting.")
                raise
                
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Unexpected error: {e}")
            if attempt < max_retries - 1:
                print(f"Unexpected error. Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 300)
            else:
                print("Max retry attempts reached. Exiting.")
                raise

# Start the bot
if __name__ == "__main__":
    try:
        print("Starting MarcusBot...")
        print(f"Discord Key: {'Set' if discord_key else 'Not Set'}")
        print(f"Gemini Key: {'Set' if google_key else 'Not Set'}")
        print(f"Tenor Key: {'Set' if tenor_key else 'Not Set'}")
        print(f"Guild: {'Set' if os.getenv('DISCORD_GUILD') else 'Not Set'}")
        
        if not discord_key:
            print("Error: DISCORD_KEY not found in environment variables")
            exit(1)
        
        # Import datetime for timestamps
        import datetime
        
        # Run the bot with enhanced error handling
        asyncio.run(run_bot_with_retry())
        
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        exit(1)