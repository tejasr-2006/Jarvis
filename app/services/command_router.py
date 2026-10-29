
def route_command(command: str) -> dict:
    command = command.lower().strip()

    if "email" in command or "inbox" in command:
        return {
            "service": "email_manager",
            "message": "Command routed to Email Manager",
        }

    if "workout" in command or "fitness" in command:
        return {
            "service": "fitness_manager",
            "message": "Command routed to Fitness Manager",
        }

    return {
        "service": "jarvis",
        "message": "Command not recognized yet",
    }
