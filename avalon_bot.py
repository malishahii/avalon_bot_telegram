import logging
import random
from typing import Dict, List
from telegram import Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters


# Enable logging
logging.basicConfig(level=logging.INFO)

# Set your bot token here
TOKEN = "5808124189:AAFXQ0fDIsadvWl9M2jsyAdVSOmF_HVJi-I"

# Define roles
ROLES = [
    "Merlin",
    "Percival",
    "Servant 1",
    "Servant 2",
    "Servant 3",
    "Servant 4",
    "Servant 5",
    "Servant 6",
    "SuperMerlin",
    "Mordred",
    "Assassin",
    "Morgana",
    "Oberon",
    "Minion 1",
    "Minion 2",
    "Minion 3",
]

# Game state
game_state = {
    "roles": [],
    "players": {},
    "lady_of_the_lake": None,
    "locked_roles": False,
}

def private_message_handler(update: Update, context: CallbackContext) -> None:
    """Handle private messages sent to the bot."""
    # Check if the message is a command
    if update.message and update.message.entities and update.message.entities[0].type == "bot_command":
        command = update.message.text.lower().split()[0][1:]
        if command == "start":
            # Clear the game state
            game_state.clear()
            game_state.update({"roles": [], "players": {}, "lady_of_the_lake": None})
            context.bot.send_message(chat_id=update.effective_chat.id, text="Game state cleared.")
        elif command == "join":
            # Join the game
            join(update, context)
        elif command == "help":
            # Send the menu
            menu = (
                "Welcome to the Avalon Bot!\n\n"
                "/start - Start the game and select roles.\n"
                "/join - Join the game after roles have been selected.\n"
                "/help - Show this help message.\n"
                "/restart - Clear the game state and start over.\n\n"
                "/reveal - Show the list of players and their roles. Only available after the game has started and roles have been assigned."
                "To interact with the bot, please send me a private message.\n\n"
                "Note: The bot only works in group chats."
            )
            context.bot.send_message(chat_id=update.effective_chat.id, text=menu)
        elif command == "restart":
            # Clear the game state and start over
            game_state.clear()
            game_state.update({"roles": [], "players": {}, "lady_of_the_lake": None})
            context.bot.send_message(chat_id=update.effective_chat.id, text="Game state cleared. Starting over...")
            start(update, context)
        elif command == "reveal":
            # Check if game has started and roles have been assigned
            if not game_state["players"] or not game_state["roles"]:
                context.bot.send_message(chat_id=update.effective_chat.id, text="Game has not started yet.")
                return
            # Prompt user for PIN
            context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter the PIN to reveal the roles.")
        else:
            # Send a message asking users to interact with the bot using a command
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please enter a valid command.",
                reply_to_message_id=update.message.message_id,
            )
    else:
        # Send a message asking users to interact with the bot using a command
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Please enter a valid command.",
            reply_to_message_id=update.message.message_id,
        )




def start(update: Update, context: CallbackContext) -> None:
    """Send a multi-choose menu consisting of role options."""
    if game_state["roles"]:
        update.message.reply_text("Game already started. Please join the game by sending /join.")
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    role if role not in game_state["roles"] else f"{role} ✅",
                    callback_data=role,
                )
                for role in ROLES[i:i + 3]
            ]
            for i in range(0, len(ROLES), 3)
        ]
        keyboard.append([InlineKeyboardButton("Lock Roles", callback_data="lock_roles")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("Select roles:", reply_markup=reply_markup)


def restart(update: Update, context: CallbackContext) -> None:
    """Reset the game state and automatically start the game."""
    global game_state
    game_state = {
        "roles": [],
        "players": {},
        "lady_of_the_lake": None,
        "locked_roles": False,
    }
    context.bot.send_message(chat_id=update.effective_chat.id, text="The game state has been reset. Starting the game...")
    start(update, context)


# Modify the main function to add the restart command

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a help message to the user."""
    help_message = (
        "Here are the available commands:\n"
        "/start - Start the game and select roles.\n"
        "/join - Join the game after roles have been selected.\n"
        "/restart - Clear all game state and reset the bot.\n"
        "/reveal - Reveal all player roles with the correct PIN (1234).\n\n"
        "/help - Show this help message.\n\n"
        "Note: The bot only works in group chats."
    )
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_message)

def lock_roles(update: Update, context: CallbackContext) -> None:
    """Lock the roles and notify users."""
    query = update.callback_query
    query.answer()

    selected_roles = game_state["roles"]

    if len(selected_roles) > 10:
        query.edit_message_text("Please select up to 10 roles.")
        return

    game_state["locked_roles"] = True
    query.edit_message_text(f"Roles locked: {', '.join(selected_roles)}")

    num_roles = len(selected_roles)
    context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=f"Waiting for {num_roles} players to join the game. Join the game by sending /join."
    )


def join(update: Update, context: CallbackContext) -> None:
    """Add a player to the game."""
    user = update.message.from_user
    user_id = user.id
    name = user.first_name
    surname = user.last_name

    if not game_state["locked_roles"]:
        update.message.reply_text("Game not started yet. Please wait until roles are locked. /start the game now")
        return

    if user_id in game_state["players"]:
        update.message.reply_text("You have already joined the game.")
        return

    num_players = len(game_state["players"])
    num_roles = len(game_state["roles"])
    if num_players == num_roles:
        update.message.reply_text("Boarding has been completed. See you next game!")
        return

    game_state["players"][user_id] = {"name": f"{name} {surname}", "role": None}

    num_players = len(game_state["players"])
    if num_players == num_roles:
        start_game(update, context)

    message = f"{name} {surname} ({num_players}/{num_roles} players joined the game)"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)




def start_game(update: Update, context: CallbackContext) -> None:
    """Start the game and distribute roles."""
    roles = game_state["roles"]
    random.shuffle(roles)

    for index, user_id in enumerate(game_state["players"]):
        game_state["players"][user_id]["role"] = roles[index]

    # Set the Lady of the Lake
    game_state["lady_of_the_lake"] = random.choice(list(game_state["players"].keys()))

    # Send role information to players
    for user_id, player in game_state["players"].items():
        send_role_information(user_id, player, game_state, context)
        
        # Send the identity of Lady of the Lake
        if user_id == game_state["lady_of_the_lake"]:
            context.bot.send_message(chat_id=user_id, text="You are the Lady of the Lake.")
        else:
            context.bot.send_message(chat_id=user_id, text=f"Lady of the Lake: {game_state['players'][game_state['lady_of_the_lake']]['name']}")

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"Lady of the Lake: {game_state['players'][game_state['lady_of_the_lake']]['name']}"
    )



def send_role_information(user_id: int, player: Dict, game_state: Dict, context: CallbackContext) -> None:
    """Send role information and relevant information to each player."""
    role = player["role"]
    name = player["name"]

    # Prepare role-specific messages
    message = f"Your role is {role}.\n"

    if role == "Merlin":
        message += get_merlin_info(game_state)
    elif role == "Percival":
        message += get_percival_info(game_state)
    elif role in ["Mordred", "Assassin", "Morgana", "Minion 1", "Minion 2", "Minion 3"]:
        message += get_evil_info(game_state, role)

    # Add information about Oberon for Merlin
    if role == "Merlin":
        for p_id, p in game_state["players"].items():
            if p["role"] == "Oberon":
                message += f"{p['name']} (Oberon)\n"

    context.bot.send_message(chat_id=user_id, text=message)



def get_merlin_info(game_state: Dict) -> str:
    evil_list = [
        player["name"] + " (Oberon)" if player["role"] == "Oberon" else player["name"]
        for player in game_state["players"].values()
        if player["role"] in ["Assassin", "Morgana", "Minion 1", "Minion 2", "Minion 3"] and player["role"] != "Mordred"
    ]
    return f"Evil players (except Mordred): {', '.join(evil_list)}\n"




def get_percival_info(game_state: Dict) -> str:
    merlin_and_morgana = [
        player["name"]
        for player in game_state["players"].values()
        if player["role"] in ["Merlin", "Morgana"]
    ]
    random.shuffle(merlin_and_morgana)
    return f"Merlin or Morgana: {', '.join(merlin_and_morgana)}\n"


def get_evil_info(game_state: Dict, role: str) -> str:
    if role == "Oberon":
        return ""

    evil_list = [
        player["name"]
        for player in game_state["players"].values()
        if player["role"] in ["Mordred", "Assassin", "Morgana", "Minion 1", "Minion 2", "Minion 3"]
    ]
    return f"Evil players (except Oberon): {', '.join(evil_list)}\n"


def button(update: Update, context: CallbackContext) -> None:
    """Handle button presses."""
    query = update.callback_query
    query.answer()

    role = query.data

    if role == "lock_roles":
        lock_roles(update, context)
    elif role in ROLES:
        if role not in game_state["roles"]:
            game_state["roles"].append(role)
        else:
            game_state["roles"].remove(role)

        keyboard = [
            [
                InlineKeyboardButton(
                    role if role not in game_state["roles"] else f"{role} ✅",
                    callback_data=role,
                )
                for role in ROLES[i:i + 3]
            ]
            for i in range(0, len(ROLES), 3)
        ]
        keyboard.append([InlineKeyboardButton("Lock Roles", callback_data="lock_roles")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text("Select roles:", reply_markup=reply_markup)



# Add group message handler
def group_message_handler(update: Update, context: CallbackContext) -> None:
    """Handle messages sent to the group."""
    # Check if the message was sent by the bot
    if update.message and update.message.from_user.is_bot:
        return

    # Check if the message is a command
    if update.message and update.message.entities and update.message.entities[0].type == "bot_command":
        return

    # Check if the message is a PIN sent by the user who used the /reveal command
    if update.message and update.message.text and update.message.text.isdigit() and int(update.message.text) == 1234 and update.message.from_user.id == context.user_data.get("reveal_user_id"):
        # Get the list of players and their roles
        players = []
        for player in game_state["players"].values():
            players.append(f"{player['name']} - {player['role']}")
        players_text = "\n".join(players)

        # Send the list to the group
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=f"List of players and their roles:\n{players_text}"
        )

        # Clear the user_data for the /reveal command
        del context.user_data["reveal_user_id"]
    elif update.message and update.message.text and update.message.text.isdigit() and int(update.message.text) != 1234 and update.message.from_user.id == context.user_data.get("reveal_user_id"):
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Incorrect PIN. Please try again."
        )





def reveal(update: Update, context: CallbackContext) -> None:
    """Reveal all player roles with the correct PIN."""
    if not game_state["roles"]:
        update.message.reply_text("The game has not started yet.")
        return

    if len(game_state["players"]) != len(game_state["roles"]):
        update.message.reply_text("Not all players have joined yet.")
        return

    if game_state["locked_roles"] is False:
        update.message.reply_text("Roles have not been locked yet.")
        return

    update.message.reply_text("Please enter the PIN to reveal player roles:")

    def pin_handler(update: Update, context: CallbackContext) -> None:
        """Check the PIN entered by the user and reveal player roles if correct."""
        pin = "1234"
        entered_pin = update.message.text.strip()

        if entered_pin != pin:
            update.message.reply_text("Incorrect PIN. Please try again.")
            return

        players_info = "\n".join([f"{player['name']}: {player['role']}" for player in game_state["players"].values()])
        update.message.reply_text(f"Player roles:\n{players_info}")

        # Remove the PIN handler
        context.dispatcher.remove_handler(pin_handler)

    # Add the PIN handler to the dispatcher
    pin_handler = MessageHandler(Filters.text & ~Filters.command, pin_handler)
    context.dispatcher.add_handler(pin_handler)
    context.user_data["reveal_user_id"] = update.effective_user.id




def main() -> None:
    """Run the bot."""
    updater = Updater(TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("join", join))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("restart", restart))  # Add the restart command
    dispatcher.add_handler(CommandHandler("reveal", reveal))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(MessageHandler(~Filters.private, group_message_handler))

    updater.start_polling()
    updater.idle()
    

if __name__ == "__main__":
    main()
