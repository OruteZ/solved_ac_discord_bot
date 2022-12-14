import os

import discord
# 유저정보를 관리할 용도의 라이브러리 pandas
from discord.ext import commands
# 반복 작업을 위한 패키지
from discord.ext import tasks

# 딜레이 걸어서 부담 줄이는 용도
# solved ac 정보 가져오기
from database_api import *

intent = discord.Intents(value=3181056)

client = discord.Client(intents=intent)

# base command prefix is !
bot = commands.Bot(command_prefix='/', intents=intent)
TOKEN = os.environ['TOKEN']

Tier_color = {
    "Unrated": 0X444444,
    "Bronze": 0XD2691E,
    "Silver": 0XE6E6FA,
    "Gold": 0XFFA500,
    "Platinum": 0X33FFCC,
    "Diamond": 0X00FFFF,
    "Ruby": 0XFF0000,
    "Master": 0XCC00FF
}
Tier_list = [
    "Unrated",
    "Bronze V", "Bronze IV", "Bronze III", "Bronze II", "Bronze I",
    "Silver V", "Silver IV", "Silver III", "Silver II", "Silver I",
    "Gold V", "Gold IV", "Gold III", "Gold II", "Gold I",
    "Platinum V", "Platinum IV", "Platinum III", "Platinum II", "Platinum I",
    "Diamond V", "Diamond IV", "Diamond III", "Diamond II", "Diamond I",
    "Ruby V", "Ruby IV", "Ruby III", "Ruby II", "Ruby I",
    "Master"
]

user_dataframe = pd.DataFrame()


def load_dataframe():
    global user_dataframe

    load_BOJ_dataframe()
    try:
        user_dataframe = pd.read_csv("User_DB.csv", sep=',', index_col=0)
        print(user_dataframe)
    except pd.errors.EmptyDataError:
        cname = ['guild_id', 'text_channel_id', 'user_id', 'boj_id']
        user_dataframe = pd.DataFrame(columns=cname)
        user_dataframe.set_index('guild_id')


def backup_dataframe():
    backup_BOJ_dataframe()
    user_dataframe.to_csv("User_DB.csv")


def user_embed(boj_id):
    user_data_series = get_user_data(boj_id)

    embed = discord.Embed(
        color=Tier_color[Tier_list[user_data_series['tier']].split()[0]],
        title=f"BOJ_Player : {boj_id}",
        url=f"https://solved.ac/profile/{boj_id}"
    )
    embed.add_field(name='> 티어', value='`' + Tier_list[user_data_series['tier']] + '`')
    embed.add_field(name='> 레이팅', value='`' + str(user_data_series['rating']) + '`')
    embed.add_field(name='> 랭킹', value='`' + str(user_data_series['rank']) + '`')
    return embed


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("개발"))
    print("유저 정보 로딩 중. . .")
    load_dataframe()
    print('[알림][봇이 정상적으로 구동되었습니다.]')

    #update_user_info.start()


"""
@tasks.loop(seconds=5)
async def update_user_info():
    if adding_user_info: return
    print("update_user_info")

    alert_channel = bot.get_channel(alert_textChannel_id)
    for dsc_id in users.keys():
        player = users[dsc_id]
        player_boj = player.boj_profile
        player_dsc = player.dscUser

        changed = player_boj.Reset_user_info()

        if changed['solved_count'] > 0:
            embed = discord.Embed(
                color=Tier_color[(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc} solved problem",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            embed.add_field(name='> 해결한 문제', value='`' + str(changed['solved_count']) + '개`')
            embed.add_field(name='> 레이팅', value='`+' + str(changed['rating']) + '`')
            embed.add_field(name='> 랭킹', value='`' + str(changed['rank']) + '`')
            await alert_channel.send(embed=embed)

        if changed['tier'] > 0:
            embed = discord.Embed(
                color=Tier_color[list(player_boj.get_user_info()['tier'].split())[0]],
                title=f"{player_dsc}의 티어가 {changed['tier']}단계 상승했습니다!",
                url=f"https://solved.ac/profile/{player_boj.id}"
            )
            info = player_boj.get_user_info()
            embed.add_field(name='> 티어', value='`' + info['tier'] + '`')
            embed.add_field(name='> 레이팅', value='`' + str(info['rating']) + '`')
            embed.add_field(name='> 랭킹', value='`' + str(info['rank']) + '`')
            await alert_channel.send(embed=embed)
"""


@bot.event
async def on_message(msg):
    if msg.author.bot: return None
    await bot.process_commands(msg)


@bot.command()
async def repeat(ctx, message):
    await ctx.send(message)


@bot.command()
async def 등록(ctx, boj_id, discord_user=None):
    global user_dataframe

    if discord_user is None:
        discord_user = ctx.author
    else:
        mentioned_members = ctx.message.mentions
        if not mentioned_members:
            discord_user = ctx.author
        else:
            discord_user = mentioned_members[0]

    user_id = discord_user.id
    guild_id = ctx.guild.id
    channel_id = ctx.channel.id

    success = add_user_data(boj_id)
    if not success:
        await ctx.send(f"Error : 아이디 : {boj_id}를 solved.ac 페이지에서 찾을 수 없음.")
        return

    old_user_df = user_dataframe[user_dataframe['user_id'].isin([user_id])]
    print(user_dataframe['user_id'].isin([user_id]))

    if not old_user_df.empty:
        print(old_user_df)
        old_boj_id = old_user_df.loc[guild_id, 'boj_id']
        print(old_boj_id)

        if old_boj_id != boj_id:
            await ctx.send(f"이미 solved.ac 계정 '{old_boj_id}'에 연동 되어 있습니다.\n연동 계정을 변경합니다.")
        else:
            await ctx.send(f"이미 solved.ac 계정 '{old_boj_id}'에 연동 되어 있습니다.")
            return

    new_user_series = pd.Series({
        'guild_id': guild_id,
        'text_channel_id': channel_id,
        'user_id': user_id,
        'boj_id': boj_id
    }, name=guild_id)

    user_dataframe = user_dataframe.append(new_user_series)

    print(user_dataframe)
    backup_dataframe()

    await ctx.send("등록 완료\n", embed=user_embed(boj_id))

@bot.command()
async def profile(ctx, boj_id):
    await ctx.send(embed=user_embed(boj_id))


bot.run(token=TOKEN)
