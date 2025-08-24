import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import asyncio
from datetime import datetime

class LikeCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_host = "http://raw.thug4ff.com"
        self.headers = {"Content-Type": "application/json"}
        self.cooldowns = {}
        self.session = aiohttp.ClientSession()

    async def cog_unload(self):
        await self.session.close()

    async def check_channel(self, ctx):
        # Allow command in any channel (optional: add your own check here)
        return True

    @commands.hybrid_command(name="like", description="Sends likes to a Free Fire player")
    @app_commands.describe(region="Player region (e.g. in, bd, br, sg)", uid="Player UID (numbers only, minimum 6 characters)")
    async def like_command(self, ctx: commands.Context, region: str, uid: str):
        is_slash = ctx.interaction is not None

        if not await self.check_channel(ctx):
            msg = "This command is not available in this channel."
            if is_slash:
                await ctx.response.send_message(msg, ephemeral=True)
            else:
                await ctx.reply(msg, mention_author=False)
            return

        user_id = ctx.author.id
        cooldown = 30
        if user_id in self.cooldowns:
            last_used = self.cooldowns[user_id]
            remaining = cooldown - (datetime.now() - last_used).seconds
            if remaining > 0:
                await ctx.send(f"Please wait {remaining} seconds before using this command again.", ephemeral=is_slash)
                return
        self.cooldowns[user_id] = datetime.now()

        if not uid.isdigit() or len(uid) < 6:
            await ctx.reply("❌ Invalid UID. Must be numbers & at least 6 characters.", mention_author=False, ephemeral=is_slash)
            return

        try:
            async with ctx.typing():
                async with self.session.get(
                    f"{self.api_host}/like?uid={uid}&region={region}",
                    headers=self.headers
                ) as response:

                    if response.status == 404:
                        await ctx.send("❌ Player not found.", ephemeral=is_slash)
                        return
                    if response.status == 429:
                        await ctx.send("⚠️ API request limit reached. Try again later.", ephemeral=is_slash)
                        return
                    if response.status != 200:
                        text = await response.text()
                        print(f"API Error: {response.status} - {text}")
                        await ctx.send("⚠️ API error occurred. Try again later.", ephemeral=is_slash)
                        return

                    data = await response.json()

                    embed = discord.Embed(
                        title="FREE FIRE LIKE SEND",
                        timestamp=datetime.now()
                    )

                    # ✅ Success
                    if data.get("status") == 1:
                        embed.color = 0x2ECC71
                        embed.description = (
                            f"┌ ACCOUNT\n"
                            f"├─ NICKNAME: {data.get('player', 'Unknown')}\n"
                            f"├─ UID: {uid}\n"
                            f"├─ REGION: {region}\n"
                            f"└─ RESULT:\n"
                            f"   ├─ ADDED: +{data.get('likes_added', 0)}\n"
                            f"   ├─ BEFORE: {data.get('likes_before', 'N/A')}\n"
                            f"   └─ AFTER: {data.get('likes_after', 'N/A')}\n\n"
                            f"YOUR REMAIN: {data.get('remain', 'N/A')} / {data.get('daily_limit', '2500')} USED\n"
                        )

                    # ⚠️ Already used today
                    elif data.get("status") == 3:
                        embed.color = 0xF1C40F
                        embed.description = (
                            f"┌ DAILY LIMIT REACHED\n"
                            f"├─ UID: {uid}\n"
                            f"├─ REGION: {region}\n"
                            f"└─ MESSAGE: {data.get('message', 'Already used today.')}\n"
                            f"⌛ Try again after: {data.get('expires_at', 'unknown')}\n"
                        )

                    # ❌ Max likes or other
                    else:
                        embed.color = 0xE74C3C
                        embed.description = (
                            f"┌ MAX LIKES / ERROR\n"
                            f"└─ This UID cannot receive more likes today.\n"
                        )

                    embed.set_footer(text="DEVELOPED BY M8N")
                    embed.description += "\n🔗 JOIN : https://discord.gg/ThJyZQjkMr"

                    await ctx.send(embed=embed, mention_author=True, ephemeral=is_slash)

        except asyncio.TimeoutError:
            await ctx.send("⚠️ Timeout: Server took too long to respond.", ephemeral=is_slash)
        except Exception as e:
            print(f"Unexpected error in like_command: {e}")
            await ctx.send("⚡ Unexpected error occurred. Please try again later.", ephemeral=is_slash)


async def setup(bot):
    await bot.add_cog(LikeCommands(bot))
