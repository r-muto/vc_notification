# インストールした discord.py を読み込む
import discord
import re
import os
import csv
import pandas as pd
import datetime

TOKEN = os.environ['VC_NOTIFICATION_BOT_TOKEN']

SETTING_CSV_PATH = './notification_setting_{server_id}.csv'

# 接続に必要なオブジェクトを生成
client = discord.Client()


# 起動時に動作する処理
@client.event
async def on_ready():
    # 起動したらターミナルにログイン通知が表示される
    print('ログインしました')


# メッセージ受信時に動作する処理
@client.event
async def on_message(message):
    server_id = message.guild.id
    # csvがなかったらカラム情報のみのファイルを作成
    if not os.path.exists(SETTING_CSV_PATH.format(server_id=server_id)):
        with open(SETTING_CSV_PATH.format(server_id=server_id), mode='w') as f:
            f.write("voice_channel,text_channel,role\n")
        print("ファイルを作成")

    # デバッグ用
    # if message.content == "rh roles":
    #     await message.channel.send(message.guild.roles)
    # if message.content == "rh text-channels":
    #     await message.channel.send(message.guild.text_channels)
    # if message.content == "rh voice-channels":
    #     await message.channel.send(message.guild.voice_channels)

    # 通知の設定
    if re.match(r'^rh set ', message.content):
        setting_list = message.content.lstrip('rh set ').split()
        print(setting_list)
        if len(setting_list) != 3:
            await message.channel.send("**こんな感じで設定してねｯ↑↑**\n `rh set ボイスチャンネル名 通知先チャンネル名 通知するロール名(@mention付けないで！)`")
            return
        f = open(SETTING_CSV_PATH.format(server_id=server_id), 'a')
        csv_writer = csv.writer(f, lineterminator='\n')

        voice_channel_name = setting_list[0]
        text_channel_name = setting_list[1]
        role_name = setting_list[2]
        append_row = (voice_channel_name, text_channel_name, role_name)
        csv_writer.writerow(append_row)
        f.close()
        print("データ追加")

        await message.channel.send(f"```設定を追加ｯ↑↑\n"
                                   f" ボイスチャンネル名:{voice_channel_name}\n"
                                   f" 通知先チャンネル名:{text_channel_name}\n"
                                   f" 通知するロール名:{role_name}```"
                                   )
    # 通知の設定
    if message.content == "rh settings":
        setting_df = pd.read_csv(SETTING_CSV_PATH.format(server_id=server_id))
        if setting_df.size != 0:
            await message.channel.send(f"```{setting_df}```")
        else:
            await message.channel.send("通知設定がﾅｲｯ↑↑")

    if re.match(r'^rh rm ', message.content):
        setting_list = message.content.lstrip('rh rm ').split()
        if len(setting_list) != 1:
            await message.channel.send("こんな感じで設定してねｯ↑↑\n`rh rm 削除したいindex番号`")
            return
        try:
            index = int(setting_list[0])
        except ValueError as e:
            print(e)
            await message.channel.send("削除したいindex番号は半角数字でお願いｯ↑↑")
            return

        setting_df = pd.read_csv(SETTING_CSV_PATH.format(server_id=server_id))
        if setting_df[index:index+1].size == 0:
            await message.channel.send("削除する設定がないｯ↑↑")
            return
        await message.channel.send(f"```{setting_df[index:index+1]}```\nの設定を削除ｯ↑↑")
        setting_df = setting_df.drop(index)
        setting_df.to_csv(SETTING_CSV_PATH.format(server_id=server_id), header=True, index=False)
        print('データ削除')

    if message.content == "rh clear":
        with open(SETTING_CSV_PATH.format(server_id=server_id), mode='w') as f:
            f.write("voice_channel,text_channel,role\n")
        await message.channel.send("設定を全部削除ｯ↑↑")
        print("ファイルを再作成")

    if message.content == "rh help":
        rh_help_text = (
            "```rh set ボイスチャンネル名 通知先テキストチャンネル名 通知するロール名\n"
            "  設定を追加```"
            "```rh settings\n"
            "  既存の設定の表示```"
            "```rh rm 削除したいindex番号\n"
            "  settingに振られているindexを指定して設定の削除```" 
            "```rh clear\n"
            "  設定の全削除```"
        )
        await message.channel.send(rh_help_text)


@client.event
async def on_vc_start(member, voice_channel, text_channel, role):
    if role.name == '@everyone':
        mention = role
        print(mention)
    else:
        mention = role.mention
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")

    title = "通話開始ｯ↑↑"
    description = (f"```ch :{voice_channel.name}\n"
                   f"始めた人 :{member.name}さん\n"
                   f"開始時間 :{now}```"
                )
    embed = discord.Embed(title=title, description=description)
    embed.set_thumbnail(url=member.avatar_url)
    await text_channel.send(f"{mention}\n", embed=embed)


@client.event
async def on_vc_end(member, voice_channel, text_channel, role):
    if role.name == '@everyone':
        mention = role
        print(mention)
    else:
        mention = role.mention
    await text_channel.send(f"{mention}\n {voice_channel.name}の通話終了ｫ↓↓")


def notification_process(server_id, voice_channel, member, event_handler):
    """
    設定csvを読み込んで通知処理を行う
    :param server_id: 読み込むcsvの判定に使う
    :param voice_channel: 検知したvc読み込むcsvの判定に使う
    :param member: サーバーやチャンネルなどの情報がここから取得できる
    :param event_handler: vc_startかvc_end
    :return:
    """
    # 設定csvを読み込み
    setting_df = pd.read_csv(SETTING_CSV_PATH.format(server_id=server_id))
    # 設定をvcチャンネルで絞り込み
    setting_df = setting_df[setting_df.voice_channel == voice_channel.name]
    # 設定がない場合はスキップ
    if not setting_df.size:
        print("通知先がありません")
        return
    # vcチャンネルに対する設定の数だけ通知を出す
    for setting_data in setting_df.values:
        text_channel_name = setting_data[1]
        role_name = setting_data[2]
        # チャンネルオブジェクト取得
        text_channel = discord.utils.get(member.guild.text_channels, name=text_channel_name)
        # ロールオブジェクト取得
        role = discord.utils.get(member.guild.roles, name=role_name)

        if (text_channel is None) or (role is None):
            print("通知するチャンネルかロールがありません")
            pass
        else:
            # 通知
            client.dispatch(event_handler, member, voice_channel, text_channel, role)

@client.event
async def on_voice_state_update(member, before, after):
    """
    ボイスチャットの入退出を検知し、入室したか退出したchannelを実際の処理部分に渡す
    :param member: ボイスチャットの状態を動かしたメンバー情報
    :param before: ボイスチャットの前情報
    :param after: ボイスチャットの後情報
    """
    # 入退出を検知
    if before.channel != after.channel:
        server_id = member.guild.id
        # 入室時
        # ※channel.membersはbot起動後ミュートなどをしてステータスを変えたメンバーしか検知しないので注意（2021/04/24現在）
        if after.channel and len(after.channel.members) == 1:
            voice_channel = after.channel
            notification_process(server_id=server_id, voice_channel=voice_channel, member=member, event_handler="vc_start")

        if before.channel and len(before.channel.members) == 0:
            voice_channel = before.channel
            notification_process(server_id=server_id, voice_channel=voice_channel, member=member, event_handler="vc_end")


# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)
