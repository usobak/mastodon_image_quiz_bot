# The Bot


## Setup

### 1) Python setup

Create a Python virtual environment somewhere in your computer:

`python3 -m venv bot_env`

Activate the environment:

`source bot_env/bin/activate`

Install the dependencies required by the bot:

`pip install -r requirements.txt`

Run the unit tests to make sure everything is fine:

`python3 -m unittest`


### 2) Mastodon setup

Create a Mastodon account in an instance that accepts bots.

Go to `Preferences` and update a few things:

- In `Public profile` mark the option `This is an automated account`
- In `Development` click on `New application`
    - Add a new for your application. The rest can be left untouched.
    - Click submit
    - Copy the string that appears next to `Your access token`


### 3) Add your content

Add some images (JPG or PNG) to the dataset folder.

For each image you need to write a JSON file with the following format:

```
{
    "title": "Bayonetta Origins: Cereza and the Lost Demon",
    "filepath": "cereza.jpg",
    "valid_responses": [
        "cereza",
        "bayonetta origins"
    ]
}
```


### 3) Running the bot

Store your authentication token in an environment variable:

`export MASTODON_TOKEN=$your_token`

Run the bot passing the endpoint of your Mastodon instance, your mastodon
username (optional) and the visibility of the messages published by the bot.


`python3 main.py --mastodon_endpoint="https://your_instance" --mastodon_owner=your_account --mastodon_visibility=public`

In order to actually make calls to your Mastodon instance you have to add the
parameter `--no_dry_run`. Otherwise the requests to Mastodon will be simulated.

Log messages will be written to `bot.log` and showed on then terminal.


## Bot commands

If the bot is launched with the argument `--mastodon_owner`, the messages
received by the bot from that account will be treated as commands.

Commands:

- `\die` The bot will shutdown itself
- `\solution_found` Publishes a message that the solution has been found and
starts the next round
- `\finish` Publishes a messages with the solution of the current round and
starts the next
- \next Publishes the next clue for the current round
