from discord.ext import commands


# Klasická morseovka

class Morse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.MORSE_CODE_DICT = {
            'A': '.-', 'B': '-...',
            'C': '-.-.', 'D': '-..', 'E': '.',
            'F': '..-.', 'G': '--.', 'H': '....',
            'I': '..', 'J': '.---', 'K': '-.-',
            'L': '.-..', 'M': '--', 'N': '-.',
            'O': '---', 'P': '.--.', 'Q': '--.-',
            'R': '.-.', 'S': '...', 'T': '-',
            'U': '..-', 'V': '...-', 'W': '.--',
            'X': '-..-', 'Y': '-.--', 'Z': '--..',

            '1': '.----', '2': '..---', '3': '...--',
            '4': '....-', '5': '.....', '6': '-....',
            '7': '--...', '8': '---..', '9': '----.',
            '0': '-----',

            ',': '--..--', '.': '.-.-.-', '?': '..--..',
            '/': '-..-.', '-': '-....-', '(': '-.--.',
            ')': '-.--.-', '!': '––...–',
            " ": ""}

        self.REVERSED_MORSE_CODE_DICT = {value: key for key, value in self.MORSE_CODE_DICT.items()}

    @commands.command(aliases=["encrypt"])
    async def zasifruj(self, ctx, message):
        await ctx.message.delete()
        try:
            cipher = '/'.join(self.MORSE_CODE_DICT.get(x.upper()) for x in message)
            await ctx.send(cipher)
        except TypeError:
            await ctx.send("Asi jsi nezadal správný text. Text musí být bez speciálních znaků!")

    @commands.command(aliases=["decrypt"])
    async def desifruj(self, ctx, message):
        await ctx.message.delete()
        try:
            decipher = ''.join(self.REVERSED_MORSE_CODE_DICT.get(x) for x in message.split("/"))
            await ctx.send(decipher)
        except TypeError:
            decipher = ''.join(self.REVERSED_MORSE_CODE_DICT.get(x) for x in message.split("|"))
            await ctx.send(decipher)


def setup(bot):
    bot.add_cog(Morse(bot))
