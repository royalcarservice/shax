import argparse

from skills.agent import run_agent


def get_user_message():
    first_line = input("You: ")

    if first_line.strip().lower() != "/multi":
        return first_line.strip()

    print("Shax: Multiline mode. Type your message.")
    print("Shax: Type END on its own line when finished.\n")

    lines = []

    while True:
        line = input()

        if line.strip() == "END":
            break

        lines.append(line)

    return "\n".join(lines).strip()


def ask(user_message, conversation):
    try:
        return run_agent(user_message, conversation)
    except Exception as e:
        return f"Sorry, something went wrong: {e}", conversation


def text_loop():
    conversation = []

    print("Shax is ready.")
    print("Type 'exit' to quit.")
    print("Type '/multi' for multiline input.")
    print("Run 'python main.py --voice' to talk to Shax instead.\n")

    while True:
        user_message = get_user_message()

        if not user_message:
            continue

        if user_message.lower() in {"exit", "quit"}:
            print("Shax: Goodbye.")
            break

        response, conversation = ask(user_message, conversation)
        print(f"Shax: {response}\n")


def voice_loop(require_wake_word: bool):
    from skills.voice import Voice, VoiceUnavailable, is_stop_command, strip_wake_word

    try:
        print("Shax: Calibrating microphone, stay quiet for a second...")
        voice = Voice()
    except VoiceUnavailable as exc:
        print(f"Shax: {exc}")
        print("Shax: Falling back to text mode.\n")
        return text_loop()

    conversation = []
    print(f"Shax is listening ({voice.engine_name}).")
    if require_wake_word:
        print('Say "Shax" before each request, e.g. "Shax, what time is it?"')
    print('Say "goodbye" to quit. Press Ctrl+C to stop.\n')
    voice.speak("Shax is online.")

    try:
        while True:
            heard = voice.listen()
            if not heard:
                continue

            woke, command = strip_wake_word(heard)
            if require_wake_word and not woke:
                continue

            if woke and not command:
                voice.speak("Yes?")
                command = voice.listen(timeout=8)
                if not command:
                    continue

            print(f"You (voice): {command}")

            if is_stop_command(command):
                print("Shax: Goodbye.")
                voice.speak("Goodbye.")
                break

            response, conversation = ask(command, conversation)
            print(f"Shax: {response}\n")
            voice.speak(response)
    except KeyboardInterrupt:
        print("\nShax: Goodbye.")


def main():
    parser = argparse.ArgumentParser(description="Shax, your personal AI agent.")
    parser.add_argument("--voice", action="store_true", help="talk to Shax with your microphone")
    parser.add_argument(
        "--always-listen",
        action="store_true",
        help='in voice mode, respond to everything you say (no need to say "Shax" first)',
    )
    args = parser.parse_args()

    if args.voice:
        voice_loop(require_wake_word=not args.always_listen)
    else:
        text_loop()


if __name__ == "__main__":
    main()
