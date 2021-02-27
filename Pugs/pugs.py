import aiohttp
import discord
import gspread_asyncio
from redbot.core import commands
from redbot.core.data_manager import cog_data_path
from google.oauth2.service_account import Credentials

class Pugs(commands.Cog):
    """My custom cog test"""

    def __init__(self, bot):
        self.bot = bot
        self.path = str(cog_data_path(self)).replace("\\", "/")
        self.credentials = self.path + '/My First Project-162dbc0aa595.json'

        # Create an AsyncioGspreadClientManager object which
        # will give us access to the Spreadsheet API.
        self.agcm = gspread_asyncio.AsyncioGspreadClientManager(self.get_creds)

    # First, set up a callback function that fetches our credentials off the disk.
    # gspread_asyncio needs this to re-authenticate when credentials expire.
    def get_creds(self):
        # To obtain a service account JSON file, follow these steps:
        # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
        creds = Credentials.from_service_account_file(self.credentials)
        scoped = creds.with_scopes([
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ])
        return scoped

    def parseRole(self, role):
        return {
            # -1: Invalid role name
            #  0: No input is given

            'tank': 1,
            'dps': 2,
            'damage': 2,
            'healer': 3,
            'support': 3,
        }.get(role.lower() if role is not None else 0, -1)

    def getRoleName(self, type):
        return {
            0: 'Tidak ada',
            1: 'Tank',
            2: 'DPS',
            3: 'Support'
        }.get(type, None)

    @commands.command()
    async def daftar(self, ctx, battletag, primaryRole, secondaryRole = None):
        """
            Command untuk registrasi PUG Overwatch Indonesia

            `battletag` **Case-sensitive**, perkatikan kapitalizasi huruf
            `primaryRole` Role utama yang mau dimainkan **(wajib di-isi)**
            `secondaryRole` Role lain (kosongkan jika tidak ada)

             [role options: **Tank**, **DPS**, **Support**]
        """

        primaryRoleType = self.parseRole(primaryRole)
        secondaryRoleType = self.parseRole(secondaryRole)
        message = await ctx.send("%s mohon tunggu.." % ctx.message.author.mention)

        if primaryRoleType == -1 or secondaryRoleType == -1:
            embed = discord.Embed(color=0xEE2222, title="Invalid role for %s" % battletag)
            embed.description = "Role yang tersedia: **Tank**, **DPS**, **Support**"
            embed.add_field(name='Primary role', value=str(primaryRole), inline=True)
            embed.add_field(name='Secondary role', value=str(secondaryRole), inline=True)
            embed.set_author(name='Pick-Up Games Registration', icon_url='https://i.imgur.com/kgrkybF.png')
            await message.delete()
            await ctx.send(content=ctx.message.author.mention, embed=embed)
            return

        url = 'https://ow-api.com/v1/stats/pc/us/%s/profile' % (battletag.replace("#", "-"))
        hdr = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)' }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=hdr) as resp:
                data = await resp.json()
                status = resp.status

        try:
            if status == 404:
                embed = discord.Embed(color=0xEE2222, title="Can't find user %s" % battletag)
                embed.description = "Pastikan profile visibility anda **Public** dan coba lagi sekitar 10 menit."
                embed.set_author(name='Pick-Up Games Registration', icon_url='https://i.imgur.com/kgrkybF.png')
                await message.delete()
                await ctx.send(content=ctx.message.author.mention, embed=embed)
            elif status == 200:
                report_line = [ctx.message.created_at.strftime("%d/%m/%Y %H:%M:%S"),  str(ctx.author), battletag, self.getRoleName(primaryRoleType), self.getRoleName(secondaryRoleType), ''.join("{}: {}, ".format(i['role'].capitalize(), i['level']) for i in data['ratings'])[:-2]]
                # Always authorize first.
                # If you have a long-running program call authorize() repeatedly.
                agc = await self.agcm.authorize()
                sheet = await agc.open_by_url("https://docs.google.com/spreadsheets/d/1PaegW6jKcLcyEMOtsNQR1SXoabgf46U37Jh_CkfxeMU/edit")
                worksheet = await sheet.get_worksheet(0)
                await worksheet.append_row(report_line, value_input_option='USER_ENTERED')

                embed = discord.Embed(color=0xEE2222, title=battletag, timestamp=ctx.message.created_at, url='https://playoverwatch.com/en-us/career/pc/%s/'% (battletag.replace("#", "-")))
                embed.description="Telah berhasil terdaftar."
                embed.add_field(name='Skill Ratings', value=''.join("{}: **{}**\n".format(i['role'].capitalize(), i['level']) for i in data['ratings']))
                embed.add_field(name='Roles', value='Primary: **%s**\nSecondary: **%s**' % (self.getRoleName(primaryRoleType), self.getRoleName(secondaryRoleType)))
                embed.set_thumbnail(url=data['icon'])
                embed.set_author(name='Pick-Up Games Registration', icon_url='https://i.imgur.com/kgrkybF.png')
                await message.delete()
                await ctx.send(content=ctx.message.author.mention, embed=embed)
        except Exception:
            await message.edit("Terjadi kesalahan. Mohon contact admin.")
            raise