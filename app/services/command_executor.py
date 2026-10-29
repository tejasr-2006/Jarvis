
from app.integrations.email_manager import EmailManagerClient


class CommandExecutor:
    async def execute(self, classification: dict) -> dict:
        service = classification["service"]
        intent = classification["intent"]
        requires_confirmation = classification["requires_confirmation"]

        if requires_confirmation:
            return {
                "status": "confirmation_required",
                "message": f"Please confirm before proceeding: {intent}",
                "service": service,
            }

        if service == "email_manager":
            try:
                email_client = EmailManagerClient()
                emails = await email_client.get_high_priority_emails()

                return {
                    "status": "success",
                    "service": service,
                    "intent": intent,
                    "data": emails,
                }
            except Exception as exc:
                print(
                    f"Email execution error: {type(exc).__name__}: {exc}"
                )
                return {
                    "status": "failed",
                    "service": service,
                    "message": "Could not retrieve high-priority emails. Check Email Manager authentication and logs.",
                }

        if service == "fitness_manager":
            return {
                "status": "not_executed",
                "message": "Fitness access requires user authentication.",
                "service": service,
                "intent": intent,
            }

        return {
            "status": "understood",
            "message": f"JARVIS understood your request: {intent}",
            "service": "jarvis",
            "intent": intent,
        }
