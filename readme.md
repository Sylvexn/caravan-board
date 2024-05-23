# Asmodeus Discord Bot

## Setup Instructions

### Prerequisites

- Python 3.8 or later
- A Riot Games API key
- A Discord bot token
- A channel ID for the leaderboard

### Configuration

1. Clone the repository and navigate to the project directory:

    ```sh
    git clone <repository_url>
    cd <repository_name>
    ```

2. Install the required packages:

    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the project directory and add your API keys and channel ID:

    ```sh
    RIOT_API_KEY=your_riot_api_key
    DISCORD_BOT_TOKEN=your_discord_bot_token
    LEADERBOARD_CHANNEL_ID=your_channel_id
    ```

### Running the Bot

- To run the bot, use:

    ```sh
    python main.py
    ```

### Commands

- **/add**: Add a player to the leaderboard using their Riot ID.
- **/remove**: Remove a player from the leaderboard using their Riot ID.
- **/setlimit**: Set the number of players displayed on the leaderboard.

### License

This project is licensed under the MIT License.
