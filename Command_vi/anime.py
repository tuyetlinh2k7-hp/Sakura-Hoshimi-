import json
import random
import urllib.parse
from pathlib import Path
from typing import Literal, Optional

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from config import OWNER_ID
from Checks_vi.i18n import t

BASE_DIR = Path(__file__).resolve().parent.parent
class AnimeLinkView(discord.ui.View):
    def __init__(self, mal_url: Optional[str] = None, trailer_url: Optional[str] = None):
        super().__init__(timeout=None)
        if mal_url and mal_url != "#":
            self.add_item(discord.ui.Button(label="Xem Chi Tiết", url=mal_url, emoji="🔗"))
        if trailer_url:
            self.add_item(discord.ui.Button(label="Trailer", url=trailer_url, emoji="▶️"))


class MediaCog(commands.Cog, name="Media"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            }
            timeout = aiohttp.ClientTimeout(total=12)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session

    async def cog_load(self) -> None:
        self._get_session()

    async def cog_unload(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    @staticmethod
    def _is_nsfw_channel(ctx: commands.Context) -> bool:
        return False

    def _build_anilist_embed(
        self,
        ctx: commands.Context,
        media: dict,
        media_type: str = "anime"
    ) -> tuple[discord.Embed, AnimeLinkView]:
        title_dict = media.get("title") or {}
        title = title_dict.get("english") or title_dict.get("romaji") or title_dict.get("native") or "N/A"
        native_title = title_dict.get("native")
        url = media.get("siteUrl") or f"https://anilist.co/{media_type}/{media.get('id', '')}"
        image_url = media.get("coverImage", {}).get("large") or media.get("coverImage", {}).get("medium") or ""

        raw_desc = media.get("description") or t(ctx.guild, "ANIME_NO_SYNOPSIS")
        clean_desc = raw_desc.replace("<br>", "\n").replace("<i>", "*").replace("</i>", "*").replace("<b>", "**").replace("</b>", "**")
        if len(clean_desc) > 1024:
            clean_desc = clean_desc[:1021] + "..."

        score = f"{media.get('averageScore')}/100" if media.get("averageScore") else "N/A"
        status = (media.get("status") or "N/A").replace("_", " ").title()

        color = discord.Color.purple() if media_type == "manga" else discord.Color.from_rgb(255, 105, 180)
        embed_title = f"{'📖' if media_type == 'manga' else '🎬'} {title}"
        if native_title and native_title != title:
            embed_title += f" ({native_title})"

        embed = discord.Embed(title=embed_title, url=url, description=clean_desc, color=color)
        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.add_field(name=t(ctx.guild, "ANIME_SCORE"), value=f"`⭐ {score}`", inline=True)
        embed.add_field(name=t(ctx.guild, "ANIME_STATUS"), value=f"`{status}`", inline=True)

        if media_type == "manga":
            chapters = media.get("chapters") or "N/A"
            volumes = media.get("volumes") or "N/A"
            embed.add_field(name=t(ctx.guild, "MANGA_CHAPTERS"), value=f"`{chapters} ch / {volumes} vol`", inline=True)
        else:
            episodes = media.get("episodes") or "N/A"
            embed.add_field(name=t(ctx.guild, "ANIME_EPISODES"), value=f"`{episodes} tập`", inline=True)

        genres = ", ".join(media.get("genres", []))
        if genres:
            embed.add_field(name=t(ctx.guild, "ANIME_GENRES"), value=genres, inline=False)

        embed.set_footer(text="Nguồn: AniList GraphQL")
        trailer = media.get("trailer") or {}
        trailer_url = None
        if trailer.get("site") == "youtube" and trailer.get("id"):
            trailer_url = f"https://www.youtube.com/watch?v={trailer['id']}"

        view = AnimeLinkView(mal_url=url, trailer_url=trailer_url)
        return embed, view

    def _build_jikan_embed(
        self,
        ctx: commands.Context,
        item: dict,
        media_type: str = "anime",
        is_random: bool = False
    ) -> tuple[discord.Embed, AnimeLinkView]:
        title = item.get("title") or "N/A"
        url = item.get("url") or "#"
        image_url = item.get("images", {}).get("jpg", {}).get("large_image_url") or ""

        synopsis = item.get("synopsis") or t(ctx.guild, "ANIME_NO_SYNOPSIS")
        if len(synopsis) > 1024:
            synopsis = synopsis[:1021] + "..."

        score = item.get("score") or "N/A"
        rank = item.get("rank") or "N/A"
        status = item.get("status") or "N/A"

        if is_random:
            embed_title = t(ctx.guild, "ANIME_RANDOM_TITLE", title=title)
            color = discord.Color.random()
        elif media_type == "manga":
            embed_title = f"📖 {title}"
            color = discord.Color.purple()
        else:
            embed_title = f"🎬 {title}"
            color = discord.Color.blue()

        embed = discord.Embed(title=embed_title, url=url, description=synopsis, color=color)
        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.add_field(name=t(ctx.guild, "ANIME_SCORE"), value=f"`{score}`", inline=True)
        embed.add_field(name=t(ctx.guild, "ANIME_RANK"), value=f"`#{rank}`", inline=True)

        if media_type == "manga":
            chapters = item.get("chapters") or "N/A"
            volumes = item.get("volumes") or "N/A"
            embed.add_field(name=t(ctx.guild, "MANGA_CHAPTERS"), value=f"`{chapters}/{volumes}`", inline=True)
        else:
            episodes = item.get("episodes") or "N/A"
            embed.add_field(name=t(ctx.guild, "ANIME_EPISODES"), value=f"`{episodes}`", inline=True)

        if not is_random:
            embed.add_field(name=t(ctx.guild, "ANIME_STATUS"), value=f"`{status}`", inline=False)

        genres = ", ".join(g["name"] for g in item.get("genres", []) if "name" in g)
        if genres:
            embed.add_field(name=t(ctx.guild, "ANIME_GENRES"), value=genres, inline=False)

        embed.set_footer(text="Nguồn: MyAnimeList (Jikan)")
        trailer_url = item.get("trailer", {}).get("url")
        view = AnimeLinkView(mal_url=url, trailer_url=trailer_url)
        return embed, view

    def _build_kitsu_embed(self, ctx: commands.Context, data: dict, media_type: str = "anime") -> tuple[discord.Embed, AnimeLinkView]:
        attrs = data.get("attributes", {})
        title = attrs.get("canonicalTitle") or "N/A"
        synopsis = attrs.get("synopsis") or t(ctx.guild, "ANIME_NO_SYNOPSIS")
        if len(synopsis) > 1024:
            synopsis = synopsis[:1021] + "..."

        score = f"{attrs.get('averageRating')}%" if attrs.get("averageRating") else "N/A"
        rank = attrs.get("ratingRank") or "N/A"
        status = (attrs.get("status") or "N/A").capitalize()
        image_url = attrs.get("posterImage", {}).get("large") or ""
        url = f"https://kitsu.app/{media_type}/{data.get('id')}"

        color = discord.Color.purple() if media_type == "manga" else discord.Color.blue()
        embed = discord.Embed(title=f"{'📖' if media_type == 'manga' else '🎬'} {title}", url=url, description=synopsis, color=color)
        if image_url:
            embed.set_thumbnail(url=image_url)

        embed.add_field(name=t(ctx.guild, "ANIME_SCORE"), value=f"`{score}`", inline=True)
        embed.add_field(name=t(ctx.guild, "ANIME_RANK"), value=f"`#{rank}`", inline=True)

        if media_type == "manga":
            chapters = attrs.get("chapterCount") or "N/A"
            volumes = attrs.get("volumeCount") or "N/A"
            embed.add_field(name=t(ctx.guild, "MANGA_CHAPTERS"), value=f"`{chapters}/{volumes}`", inline=True)
        else:
            episodes = attrs.get("episodeCount") or "N/A"
            embed.add_field(name=t(ctx.guild, "ANIME_EPISODES"), value=f"`{episodes}`", inline=True)

        embed.add_field(name=t(ctx.guild, "ANIME_STATUS"), value=f"`{status}`", inline=False)
        embed.set_footer(text="Nguồn dự phòng: Kitsu.io")
        return embed, AnimeLinkView(mal_url=url)

    async def _fetch_anime_manga(self, ctx: commands.Context, media_type: str, query: str):
        session = self._get_session()
        m_type_upper = "ANIME" if media_type == "anime" else "MANGA"

        # 1. API chính: AniList GraphQL (Nhanh, không chặn IP, thông tin chi tiết)
        try:
            gql_query = """
            query ($search: String, $type: MediaType) {
              Media (search: $search, type: $type) {
                id
                title {
                  romaji
                  english
                  native
                }
                type
                status
                description(asHtml: false)
                episodes
                chapters
                volumes
                averageScore
                genres
                coverImage {
                  large
                  medium
                }
                siteUrl
                trailer {
                  id
                  site
                }
              }
            }
            """
            async with session.post(
                "https://graphql.anilist.co",
                json={"query": gql_query, "variables": {"search": query, "type": m_type_upper}},
                headers={"Content-Type": "application/json", "Accept": "application/json"}
            ) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    media = res_json.get("data", {}).get("Media")
                    if media:
                        embed, view = self._build_anilist_embed(ctx, media, media_type=media_type)
                        return await ctx.send(embed=embed, view=view)
        except Exception:
            pass

        # 2. API dự phòng 1: Jikan (MyAnimeList)
        params_jikan = {"q": query, "limit": 1}
        if True:
            params_jikan["sfw"] = "true"
        try:
            async with session.get(f"https://api.jikan.moe/v4/{media_type}", params=params_jikan) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    if res_json and res_json.get("data"):
                        embed, view = self._build_jikan_embed(ctx, res_json["data"][0], media_type=media_type)
                        return await ctx.send(embed=embed, view=view)
        except Exception:
            pass

        # 3. API dự phòng 2: Kitsu
        try:
            headers_kitsu = {"Accept": "application/vnd.api+json"}
            async with session.get(f"https://kitsu.io/api/edge/{media_type}", params={"filter[text]": query, "page[limit]": 1}, headers=headers_kitsu) as resp:
                if resp.status == 200:
                    res_json = await resp.json()
                    if res_json and res_json.get("data"):
                        embed, view = self._build_kitsu_embed(ctx, res_json["data"][0], media_type=media_type)
                        return await ctx.send(embed=embed, view=view)
        except Exception:
            pass

        err_key = "ANIME_NOT_FOUND" if media_type == "anime" else "MANGA_NOT_FOUND"
        await ctx.send(t(ctx.guild, err_key, name=query))

    async def _fetch_waifu_neko(self, ctx: commands.Context, endpoint: str, title_key: str, color: discord.Color):
        session = self._get_session()
        image_url = None
        source_note = ""

        # 1. API chính (Nekos.best với header)
        try:
            headers = {"User-Agent": "SakuraBot/1.0 (DiscordBot)"}
            async with session.get(f"https://nekos.best/api/v2/{endpoint}", headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("results"):
                        image_url = data["results"][0].get("url")
                        source_note = "Nekos.best"
        except Exception:
            pass

        # 2. API dự phòng 1: waifu.im (Cực kỳ ổn định và nhanh)
        if not image_url:
            try:
                tag = "waifu" if endpoint == "waifu" else "maid"
                async with session.get("https://api.waifu.im/search", params={"is_nsfw": "false", "included_tags": tag}, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("images"):
                            image_url = data["images"][0].get("url")
                            source_note = "Waifu.im"
            except Exception:
                pass

        # 3. API dự phòng 2: Waifu.pics
        if not image_url:
            try:
                async with session.get(f"https://api.waifu.pics/sfw/{endpoint}", timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        image_url = data.get("url")
                        source_note = "Waifu.pics (Dự phòng)"
            except Exception:
                pass

        if not image_url:
            return await ctx.send(t(ctx.guild, "WAIFU_NO_DATA"))

        embed = discord.Embed(title=t(ctx.guild, title_key), color=color)
        embed.set_image(url=image_url)
        embed.set_footer(text=f"Nguồn: {source_note} • Yêu cầu bởi {ctx.author.display_name}")
        await ctx.send(embed=embed)

    async def _fetch_image(self, ctx: commands.Context, query: str):
        session = self._get_session()
        # 1. API chính (Wikimedia Commons)
        try:
            params = {
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrlimit": "1",
                "prop": "imageinfo",
                "iiprop": "url",
                "format": "json"
            }
            async with session.get("https://commons.wikimedia.org/w/api.php", params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})
                    for page in pages.values():
                        infos = page.get("imageinfo", [])
                        if infos and infos[0].get("url"):
                            embed = discord.Embed(title=t(ctx.guild, "IMAGE_RESULT_TITLE", keyword=query.title()), color=discord.Color.blue())
                            embed.set_image(url=infos[0]["url"])
                            embed.set_footer(text="Nguồn: Wikimedia Commons")
                            return await ctx.send(embed=embed)
        except Exception:
            pass

        # 2. API dự phòng (LoremFlickr)
        try:
            encoded = urllib.parse.quote(query)
            random_id = random.randint(1, 1000)
            url = f"https://loremflickr.com/1200/900/{encoded}?random={random_id}"
            async with session.get(url, allow_redirects=True) as resp:
                if resp.status == 200:
                    embed = discord.Embed(title=t(ctx.guild, "IMAGE_RESULT_TITLE", keyword=query.title()), color=discord.Color.blue())
                    embed.set_image(url=str(resp.url))
                    embed.set_footer(text="Nguồn: LoremFlickr")
                    return await ctx.send(embed=embed)
        except Exception:
            pass

        await ctx.send(t(ctx.guild, "IMAGE_ERROR", error="Không tìm thấy hình ảnh phù hợp từ tất cả nguồn."))

    async def _action_autocomplete(self, interaction: discord.Interaction, current: str):
        actions = [
            ("Tìm kiếm Anime (anime)", "anime"),
            ("Tìm kiếm Manga (manga)", "manga"),
            ("Gợi ý Anime ngẫu nhiên (random)", "random"),
            ("Ảnh Waifu dễ thương (waifu)", "waifu"),
            ("Ảnh Neko dễ thương (neko)", "neko"),
            ("Tìm kiếm hình ảnh (image)", "image")
        ]
        return [
            app_commands.Choice(name=name, value=val)
            for name, val in actions if current.lower() in name.lower() or current.lower() in val.lower()
        ]

    @commands.hybrid_command(
        name="anime",
        description="🎬 Hệ thống tra cứu Anime, Manga và hình ảnh nghệ thuật (Kèm API dự phòng)."
    )
    @app_commands.describe(
        action="Chọn hành động cần thực hiện",
        query="Tên anime, manga hoặc từ khóa hình ảnh cần tìm kiếm"
    )
    @app_commands.autocomplete(action=_action_autocomplete)
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def anime(
        self,
        ctx: commands.Context,
        action: Optional[str] = "anime",
        *,
        query: Optional[str] = None
    ):
        raw_action = (action or "anime").lower().strip()
        KNOWN_ACTIONS = ("anime", "manga", "random", "waifu", "neko", "image")
        
        # Xử lý khi người dùng gõ lệnh prefix như: s!anime naruto
        if raw_action not in KNOWN_ACTIONS:
            if query:
                query = f"{action} {query}".strip()
            else:
                query = action
            act = "anime"
        else:
            act = raw_action

        if ctx.interaction:
            await ctx.defer()

        if act == "anime":
            if not query:
                return await ctx.send("⚠️ Vui lòng nhập tên anime cần tìm kiếm!", ephemeral=True)
            return await self._fetch_anime_manga(ctx, "anime", query)

        if act == "manga":
            if not query:
                return await ctx.send("⚠️ Vui lòng nhập tên manga cần tìm kiếm!", ephemeral=True)
            return await self._fetch_anime_manga(ctx, "manga", query)

        if act == "random":
            session = self._get_session()
            # 1. Jikan Random
            params = {"sfw": "true"}
            try:
                async with session.get("https://api.jikan.moe/v4/random/anime", params=params, timeout=4) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        if res_json and res_json.get("data"):
                            embed, view = self._build_jikan_embed(ctx, res_json["data"], media_type="anime", is_random=True)
                            return await ctx.send(embed=embed, view=view)
            except Exception:
                pass

            # 2. AniList Random Page
            try:
                random_page = random.randint(1, 100)
                gql_query = """
                query ($page: Int) {
                  Page(page: $page, perPage: 1) {
                    media(type: ANIME, sort: POPULARITY_DESC) {
                      id
                      title { romaji english native }
                      type
                      status
                      description(asHtml: false)
                      episodes
                      averageScore
                      genres
                      coverImage { large }
                      siteUrl
                      trailer { id site }
                    }
                  }
                }
                """
                async with session.post(
                    "https://graphql.anilist.co",
                    json={"query": gql_query, "variables": {"page": random_page}},
                    headers={"Content-Type": "application/json", "Accept": "application/json"}
                ) as resp:
                    if resp.status == 200:
                        res_json = await resp.json()
                        medias = res_json.get("data", {}).get("Page", {}).get("media", [])
                        if medias:
                            embed, view = self._build_anilist_embed(ctx, medias[0], media_type="anime")
                            embed.title = f"🎲 Gợi Ý Anime Ngẫu Nhiên: {medias[0].get('title', {}).get('english') or medias[0].get('title', {}).get('romaji')}"
                            return await ctx.send(embed=embed, view=view)
            except Exception:
                pass

            return await ctx.send(t(ctx.guild, "ANIME_RANDOM_ERROR"))

        if act == "waifu":
            return await self._fetch_waifu_neko(ctx, "waifu", "WAIFU_TITLE", discord.Color.pink())

        if act == "neko":
            return await self._fetch_waifu_neko(ctx, "neko", "NEKO_TITLE", discord.Color.light_grey())

        if act == "image":
            if not query:
                return await ctx.send("⚠️ Vui lòng nhập từ khóa ảnh cần tìm!", ephemeral=True)
            return await self._fetch_image(ctx, query)

    @commands.command(name="manga")
    async def manga_shortcut(self, ctx: commands.Context, *, ten_manga: str):
        await self.anime(ctx, action="manga", query=ten_manga)

    @commands.command(name="randomanime", aliases=["ranime"])
    async def ranime_shortcut(self, ctx: commands.Context):
        await self.anime(ctx, action="random")

    @commands.command(name="waifu")
    async def waifu_shortcut(self, ctx: commands.Context):
        await self.anime(ctx, action="waifu")

    @commands.command(name="neko")
    async def neko_shortcut(self, ctx: commands.Context):
        await self.anime(ctx, action="neko")

    @commands.command(name="image", aliases=["pinterest", "pimage"])
    async def image_shortcut(self, ctx: commands.Context, *, tu_khoa: str):
        await self.anime(ctx, action="image", query=tu_khoa)


async def setup(bot: commands.Bot):
    await bot.add_cog(MediaCog(bot))
