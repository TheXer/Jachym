import json

import discord
from discord.ext import commands
from discord.ext.commands import has_permissions


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Jáchym je ready!")

    @commands.command()
    async def test(self, ctx):
        with open("text_json/package.json") as f:
            test = json.load(f)
            embed = discord.Embed.from_dict(test["test"])
            await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=['help'])
    async def pomoc(self, ctx):
        embed = discord.Embed(title="Pomocník", description="Pomůžu ti najít příkazy!",
                              timestamp=ctx.message.created_at, color=0xff0000)
        file = discord.File("fotky/LogoPotkani.png", filename="LogoPotkani.png")
        embed.set_thumbnail(url="attachment://LogoPotkani.png")
        embed.add_field(name="!pomoc nebo !help", value="Když potřebuješ pomoct s příkazy... :-)", inline=False)
        embed.add_field(name='!anketa "Otázka" "Odpověď"',
                        value='Jednoduchá anketa, ukáže počet osob hlasujících i kdo hlasoval. Maximálně 10 odpovědí. '
                              '\n> `!anketa "Kdo je hlavní vedoucí Potkanů?" "Křeček" "Žiry" "Bára"`',
                        inline=False)
        embed.add_field(name="!rozcestnik",
                        value="Všechny důležité věci, co skaut potřebuje, včetně věcí jako organizace a hospodářství.",
                        inline=False)
        embed.add_field(name="!ping", value="Ukáže latenci bota (v případě kdyby něco nefungovalo)", inline=False)
        embed.add_field(name="!vypis", value="Výpis všech aktuálních členů na discordu podle skupin")
        embed.add_field(name="!vlakna", value="Výpis všech vláken podle kategorie, včetně těch, kam nemáte přístup")
        embed.add_field(name="!serverinfo", value="Výpis všech informací na serveru", inline=False)
        embed.add_field(name="!userinfo", value="Výpis uživatelských informací")
        embed.add_field(name="!clear nebo !smazat",
                        value="Administrátorský příkaz pro smazání zpráv. Maximálně 99 zpráv", inline=False)

        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(file=file, embed=embed)

    @commands.command(pass_context=True)
    async def rozcestnik(self, ctx):
        embed = discord.Embed(title="Rozcestník", description="‎Všechny věci, co skaut potřebuje",
                              timestamp=ctx.message.created_at, color=0xf5ec00)
        embed.add_field(name="https://krizovatka.skaut.cz/",
                        value="-skautská křižovatka \n-rozcestník informací od Junáka \n-stezky \n-materiály "
                              "\n-komunikace \n-a spousta dalšího \n")
        embed.add_field(name="https://is.skaut.cz/",
                        value="-SkautIS \n-přihlašování na kurzy \n-správa informací a členů \n-správa akcí, výprav, "
                              "táborů")
        embed.add_field(name="https://discord.gg/ztxcybF",
                        value="-Skautský discord server \n-setkávání a pokec skautů z ČR \n-nápady, inspirace")
        embed.add_field(name="https://www.skaut.cz/", value="-hlavní webová stránka Junáka \n-vyhledávání oddílů")
        embed.add_field(name="https://kurzy.skaut.cz/",
                        value="-databáze rádcovských, čekatelských, vůdcovských a dalších kurzů")
        embed.add_field(name="https://krizovatka.skaut.cz/oddil/zakladny-taboriste",
                        value="-Databáze skautských základen a tábořišť")
        embed.add_field(name="https://www.facebook.com/groups/skautforum",
                        value="-celostátní FB skupina skautských vedoucích")
        embed.add_field(name="https://h.skauting.cz/", value="-hSkauting \n-hospodaření \n-vyúčtování výprav, táborů")
        embed.add_field(name="https://www.facebook.com/SkautInfo", value="-oficiální skautský informační kanál")
        embed.add_field(name="https://www.junshop.cz/", value="-obchod se skautským a turistickým vybavením")
        embed.add_field(name="https://www.facebook.com/potkani53", value="-facebook oddílu \n-fotky, alba")

        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def ping(self, ctx):
        await ctx.send('Odezva je takováhle: {} ms'.format(round(self.bot.latency * 1000)))

    @commands.command(pass_context=True)
    async def vypis(self, ctx):
        embed = discord.Embed(title="Výpis všech členů na discordu", timestamp=ctx.message.created_at, color=0xff0000)
        server = ctx.message.guild

        sedma = ctx.guild.get_role(765546277857263616)
        mrtvoly = ctx.guild.get_role(765548660380663839)
        vedouci = ctx.guild.get_role(765549177857376256)
        lamy = ctx.guild.get_role(765549514630496306)

        def vypis_lidi(role_id, jmeno_skupiny: str):
            x = []
            for member in server.members:
                if role_id in member.roles:
                    x.append(member)

            return embed.add_field(name=f"{jmeno_skupiny}", value=f"{', '.join(member.display_name for member in x)}",
                                   inline=False)

        vypis_lidi(sedma, "Sedmička")
        vypis_lidi(mrtvoly, "Mrtvoly")
        vypis_lidi(vedouci, "Vedoucí")
        vypis_lidi(lamy, "Lamy")

        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def vlakna(self, ctx):
        embed = discord.Embed(title="Všechny vlákna", timestamp=ctx.message.created_at, color=0xff0000)

        guild = ctx.message.guild
        obecne = discord.utils.get(guild.categories, id=765544635861827596)
        organizace = discord.utils.get(guild.categories, id=765552626267324426)
        projekty = discord.utils.get(guild.categories, id=765597261760561162)
        vypravy_akce = discord.utils.get(guild.categories, id=765561951064948737)
        druzinovky = discord.utils.get(guild.categories, id=765595377750638652)
        archiv = discord.utils.get(guild.categories, id=795225930611687464)

        def vsechny_vlakna(category, nazev: str):
            x = []
            for channel in category.channels:
                x.append(channel)
            return embed.add_field(name=f"{nazev}", value='\n'.join(channel.name for channel in x), inline=False)

        vsechny_vlakna(obecne, "Obecné")
        vsechny_vlakna(organizace, "Organizace")
        vsechny_vlakna(projekty, "Projekty")
        vsechny_vlakna(vypravy_akce, "Výpravy a jiné akce")
        vsechny_vlakna(druzinovky, "Družinovky")
        vsechny_vlakna(archiv, "Archiv")

        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def userinfo(self, ctx, user: discord.Member):
        list_members = ctx.guild.members
        if user in list_members:

            roles = [role for role in user.roles]

            embed = discord.Embed(title="Uživatelské informace", timestamp=ctx.message.created_at,
                                  colour=discord.Color.gold())
            embed.set_author(name=user.display_name, icon_url=user.avatar_url)
            embed.set_thumbnail(url=user.avatar_url)
            embed.set_footer(text="Jáchym", icon_url=self.bot.user.avatar_url)

            fields = [
                ("Jméno", str(user), False),
                ("ID", user.id, False),
                (f"Role ({len(roles) - 1})",
                 ", ".join([str(role) for role in user.roles if role != ctx.guild.default_role]), False),
                ("Vytvořen účet:", user.created_at.strftime("%d.%m.%Y"), False),
                ("Připojil se:", user.joined_at.strftime("%d.%m.%Y %H:%M:%S"), False)]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            await ctx.send(embed=embed)

        else:
            await ctx.send('Musíš někoho pingnout z tohoto serveru!')

    @commands.command(pass_context=True)
    async def serverinfo(self, ctx):
        role_count = len(ctx.guild.roles)
        list_of_bots = [bot.mention for bot in ctx.guild.members if bot.bot]
        staff_roles = ["Majitel", "Moderátor", "Sedmička", "Vedoucí", "Mrtvoly", "Lamy"]

        embed = discord.Embed(timestamp=ctx.message.created_at, color=ctx.author.color)
        embed.add_field(name='Jméno', value=f"{ctx.guild.name}", inline=False)
        embed.add_field(name='Hlavní vedoucí', value=f"{ctx.message.guild.owner.display_name} 👑", inline=False)
        embed.add_field(name='Vertifikační level', value=str(ctx.guild.verification_level), inline=False)
        embed.add_field(name='Nejvyšší role', value=ctx.guild.roles[-1], inline=False)

        for r in staff_roles:
            role = discord.utils.get(ctx.guild.roles, name=r)
            if role:
                members = '\n'.join([member.display_name for member in role.members]) or "None"
                count = len(role.members)
                embed.add_field(name=f"{role.name} ({count})", value=members)

        embed.add_field(name='Celkem rolí', value=str(role_count), inline=False)
        embed.add_field(name='Celkem členů beze botů', value=f"{len([m for m in ctx.guild.members if not m.bot])}",
                        inline=False)
        embed.add_field(name='Botové:', value=(', '.join(list_of_bots)))
        embed.add_field(name='Vytvořeno', value=ctx.guild.created_at.strftime('%d.%m.%Y'), inline=False)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(pass_context=True, aliases=["smazat"])
    @has_permissions(administrator=True)
    async def clear(self, ctx, limit: int):
        if 1 < limit < 100:
            deleted = await ctx.channel.purge(limit=limit)
            await ctx.send("Smazáno {deleted} zpráv.".format(deleted=len(deleted)))
        else:
            await ctx.send("Limit musí být někde mezi 1 nebo 99!")


def setup(bot):
    bot.add_cog(Utility(bot))
