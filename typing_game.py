import curses
import time
import random
import json
import uuid
import paho.mqtt.client as mqtt
from threading import Thread, Event

# --- Game Configuration ---
TEXT_TO_TYPE = [
    "The quick brown fox jumps over the lazy dog.",
    "Never underestimate the power of a well-placed semicolon.",
    "To be, or not to be, that is the question.",
    "The journey of a thousand miles begins with a single step.",
    "In the beginning, the universe was created. This has made a lot of people very angry and been widely regarded as a bad move."
]
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

# --- Global State (managed by the network thread) ---
opponent_state = {
    "wpm": 0,
    "progress": 0,
    "accuracy": 100,
    "finished": False,
    "winner": False,
}
game_started_event = Event()
game_over_event = Event()
game_text = ""

# --- MQTT Network Handling ---
def network_thread_logic(client, topic):
    """ The main loop for the MQTT client to process messages. """
    client.loop_forever()

def on_connect(client, userdata, flags, rc, properties=None):
    """ Callback for when the client connects to the broker. """
    if rc == 0:
        # Subscribe to the topic once connected
        topic = userdata['topic']
        client.subscribe(topic)
    else:
        # Handle connection failure if needed
        pass

def on_message(client, userdata, msg):
    """ Callback for when a message is received from the broker. """
    global opponent_state, game_text
    try:
        payload = msg.payload.decode()
        data = json.loads(payload)

        # Host receives join message from client
        if data.get("action") == "join" and userdata["is_host"]:
            # Send the game text to the client to start the game
            text_to_send = json.dumps({"action": "start_game", "text": userdata["game_text"]})
            client.publish(userdata["topic"], text_to_send)
            game_started_event.set()

        # Client receives the game text from the host
        elif data.get("action") == "start_game" and not userdata["is_host"]:
            game_text = data["text"]
            game_started_event.set()

        # Both players receive progress updates
        elif data.get("action") == "progress_update":
            opponent_state.update(data["state"])

        # Both players can receive a game over message
        elif data.get("action") == "game_over":
            opponent_state["winner"] = True
            game_over_event.set()

    except (json.JSONDecodeError, UnicodeDecodeError):
        # Ignore malformed messages
        pass


# --- Curses UI and Game Logic ---
def draw_ui(stdscr, state):
    """ Renders the game UI in the terminal, now with text wrapping. """
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    # Define drawing area and handle very small terminals
    start_y, start_x = 4, 4
    max_line_width = w - start_x - 2  # Leave a right margin
    if max_line_width <= 0:
        stdscr.addstr(0, 0, "Terminal is too small!")
        stdscr.refresh()
        return

    # Draw title
    stdscr.addstr(2, 2, "Type the following text:")

    # 1. Draw the full prompt text with wrapping
    for i in range(0, len(game_text), max_line_width):
        line_num = i // max_line_width
        draw_y = start_y + line_num
        if draw_y >= h - 6:  # Stop if we run out of vertical space for stats
            break
        stdscr.addstr(draw_y, start_x, game_text[i:i + max_line_width])

    # 2. Draw the user's typed text over the prompt text with colors
    for i, char in enumerate(state['current_text']):
        line_num = i // max_line_width
        char_pos = i % max_line_width
        draw_y = start_y + line_num
        draw_x = start_x + char_pos

        if draw_y >= h - 6:  # Stop if we run out of vertical space
            break
        
        correct_char = game_text[i]
        color = curses.color_pair(1) if char == correct_char else curses.color_pair(2)
        stdscr.addstr(draw_y, draw_x, char, color)

    # Draw Stats
    stdscr.addstr(h - 5, 2, "-" * (w - 4))
    my_stats = f"Your Stats -> WPM: {state['wpm']:.0f} | Progress: {state['progress']:.0f}% | Accuracy: {state['accuracy']:.1f}%"
    opp_stats = f"Opponent -> WPM: {opponent_state['wpm']:.0f} | Progress: {opponent_state['progress']:.0f}% | Accuracy: {opponent_state['accuracy']:.1f}%"
    stdscr.addstr(h - 4, 4, my_stats)
    stdscr.addstr(h - 3, 4, opp_stats)

    # Draw Game Over Message
    if state["finished"]:
        if opponent_state["winner"]:
            msg = "You lose! Better luck next time."
        else:
             msg = "You are the winner!"
        stdscr.addstr(h // 2, (w - len(msg)) // 2, msg, curses.A_BOLD)
        stdscr.addstr(h // 2 + 2, (w - 28) // 2, "Press any key to exit...")

    stdscr.refresh()

def calculate_stats(state):
    """ Calculates WPM, progress, and accuracy. """
    if not state['start_time']:
        return
    
    elapsed_time = time.time() - state['start_time']
    if elapsed_time > 0:
        # WPM is (number of characters / 5) / (time in minutes)
        state['wpm'] = (len(state['current_text']) / 5) / (elapsed_time / 60)
    
    state['progress'] = (len(state['current_text']) / len(game_text)) * 100
    
    errors = sum(1 for i, char in enumerate(state['current_text']) if char != game_text[i])
    state['accuracy'] = ((len(state['current_text']) - errors) / len(state['current_text'])) * 100 if state['current_text'] else 100

def main_game_loop(stdscr, client, topic):
    """ The main game loop that handles user input and state updates. """
    global opponent_state
    
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK) # Correct text
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)   # Incorrect text
    stdscr.nodelay(True) # Non-blocking input

    state = {
        "current_text": "",
        "wpm": 0,
        "progress": 0,
        "accuracy": 100,
        "start_time": None,
        "finished": False
    }

    last_update_time = 0

    while not game_over_event.is_set():
        if not state["finished"]:
            try:
                key = stdscr.getkey()
                # Start timer on first keypress
                if state["start_time"] is None:
                    state["start_time"] = time.time()

                if key in ("KEY_BACKSPACE", '\b', '\x7f'):
                    if state["current_text"]:
                        state["current_text"] = state["current_text"][:-1]
                elif len(key) == 1: # Regular character
                    state["current_text"] += key
                
                calculate_stats(state)

                # Check for win condition
                if state["current_text"] == game_text:
                    state["finished"] = True
                    # Notify opponent that we won
                    win_message = json.dumps({"action": "game_over"})
                    client.publish(topic, win_message)
                    game_over_event.set()


            except curses.error:
                # No input, just pass
                pass
        else:
             # If finished, wait for any key to exit
            try:
                stdscr.getkey()
                break
            except curses.error:
                pass


        # Send progress update to opponent periodically
        if time.time() - last_update_time > 0.2:
            calculate_stats(state)
            progress_data = {
                "action": "progress_update",
                "state": {
                    "wpm": state["wpm"],
                    "progress": state["progress"],
                    "accuracy": state["accuracy"]
                }
            }
            client.publish(topic, json.dumps(progress_data))
            last_update_time = time.time()
        
        draw_ui(stdscr, state)
        time.sleep(0.01)

    # Final draw to show winner/loser message before exiting
    draw_ui(stdscr, state)
    time.sleep(1)
    stdscr.nodelay(False) # Blocking input for final keypress
    if state["finished"]:
       stdscr.getch()

    client.disconnect()


def main(stdscr):
    """ Main entry point to set up the connection and start the game. """
    global game_text
    stdscr.clear()
    stdscr.addstr(0, 0, "P2P Typing Game (via MQTT Relay)")
    stdscr.addstr(2, 0, "1. Create Game")
    stdscr.addstr(3, 0, "2. Join Game")
    stdscr.refresh()
    
    is_host = False
    topic = ""

    while True:
        key = stdscr.getkey()
        if key == '1':
            is_host = True
            game_text = random.choice(TEXT_TO_TYPE)
            unique_id = str(uuid.uuid4()).split('-')[0]
            topic = f"typing-game/{unique_id}"
            stdscr.clear()
            stdscr.addstr(0, 0, "Game Created!")
            stdscr.addstr(2, 0, "Share this code with your friend:")
            stdscr.addstr(4, 2, topic, curses.A_BOLD)
            stdscr.addstr(6, 0, "Waiting for them to join...")
            stdscr.refresh()
            break
        elif key == '2':
            curses.echo()
            stdscr.clear()
            stdscr.addstr(0, 0, "Enter the game code from your friend:")
            stdscr.refresh()
            topic = stdscr.getstr(2, 0, 30).decode('utf-8')
            curses.noecho()
            stdscr.clear()
            stdscr.addstr(0, 0, f"Joining game: {topic}")
            stdscr.addstr(2, 0, "Connecting...")
            stdscr.refresh()
            break

    # --- Setup MQTT Client ---
    user_data = {"topic": topic, "is_host": is_host, "game_text": game_text}
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=user_data)
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    
    # Start the network thread
    net_thread = Thread(target=network_thread_logic, args=(client, topic), daemon=True)
    net_thread.start()

    if is_host:
        # Host waits for the client to join
        game_started_event.wait(timeout=120) # 2 minute timeout
    else:
        # Client sends a join message and waits for the host to start the game
        client.publish(topic, json.dumps({"action": "join"}))
        game_started_event.wait(timeout=120)

    if not game_started_event.is_set():
        stdscr.clear()
        stdscr.addstr(0,0, "Error: Game did not start. Opponent not found. Press any key to exit.")
        stdscr.refresh()
        stdscr.nodelay(False)
        stdscr.getch()
    else:
        main_game_loop(stdscr, client, topic)


if __name__ == "__main__":
    curses.wrapper(main)

