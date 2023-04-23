import discord
from discord import Message, app_commands
from discord.ext import commands


# Klasická morseovka


class Morse(commands.Cog):
    """Class for Morse code"""

    MORSE_CODE_DICT = {
        "A": ".-",
        "B": "-...",
        "C": "-.-.",
        "D": "-..",
        "E": ".",
        "F": "..-.",
        "G": "--.",
        "H": "....",
        "I": "..",
        "J": ".---",
        "K": "-.-",
        "L": ".-..",
        "M": "--",
        "N": "-.",
        "O": "---",
        "P": ".--.",
        "Q": "--.-",
        "R": ".-.",
        "S": "...",
        "T": "-",
        "U": "..-",
        "V": "...-",
        "W": ".--",
        "X": "-..-",
        "Y": "-.--",
        "Z": "--..",
        "1": ".----",
        "2": "..---",
        "3": "...--",
        "4": "....-",
        "5": ".....",
        "6": "-....",
        "7": "--...",
        "8": "---..",
        "9": "----.",
        "0": "-----",
        ",": "--..--",
        ".": ".-.-.-",
        "?": "..--..",
        "/": "-..-.",
        "-": "-....-",
        "(": "-.--.",
        ")": "-.--.-",
        "!": "--...-",
        " ": "",
    }

    REVERSED_MORSE_CODE_DICT = {value: key for key, value in MORSE_CODE_DICT.items()}
    SEPARATOR = ["/", "|"]

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="zasifruj", description="Zašifruj text do morserovky!")
    @app_commands.describe(message="Věta nebo slovo pro zašifrování")
    async def zasifruj(self, interaction: discord.Interaction, message: str) -> Message:
        try:
            cipher = "/".join(
                self.MORSE_CODE_DICT.get(letter.upper()) for letter in message
            )
            return await interaction.response.send_message(cipher)
        except TypeError:
            return await interaction.response.send_message(
                "Asi jsi nezadal správný text. Text musí být bez speciálních znaků!"
            )

    @app_commands.command(name="desifruj", description="Dešifruj text z morserovky!")
    @app_commands.describe(message="Věta nebo slovo pro dešifrování")
    async def desifruj(self, interaction: discord.Interaction, message: str) -> Message:
        try:
            decipher = "".join(
                self.REVERSED_MORSE_CODE_DICT.get(letter)
                for letter in message.split("/")
            )
            return await interaction.response.send_message(decipher)
        except TypeError:
            decipher = "".join(
                self.REVERSED_MORSE_CODE_DICT.get(x) for x in message.split("|")
            )
            return await interaction.response.send_message(decipher)


async def setup(bot):
    await bot.add_cog(Morse(bot))
