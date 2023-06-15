
class EmbedBaseError(Exception):
    def __init__(self, message, interaction, inner):
        super().__init__(message, inner)
        self.message = message
        self.interaction = interaction

    async def send(self):
        args = {
            "content": self.message,
            "ephemeral": True
        }
        if not self.interaction.response.is_done():
            await self.interaction.response.send_message(**args)
        else:
            self.interaction.followup.send(**args)

class TooManyOptionsError(EmbedBaseError):
    pass

class TooFewOptionsError(EmbedBaseError):
    pass


