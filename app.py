import os
import json
import pymysql
import inspect

from datetime import datetime, timezone, timedelta
from flask import Flask, abort, request, render_template


# https://github.com/line/line-bot-sdk-python
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, LocationMessage, TextSendMessage, TemplateSendMessage, CarouselTemplate, CarouselColumn, PostbackTemplateAction, MessageTemplateAction, URITemplateAction, ButtonsTemplate, ConfirmTemplate

from pymysql import connect, cursors

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))
liffid_sharelaction = os.environ.get("LIFF_ID_SHARELACTION")
liffurl_sharelaction = os.environ.get("LIFF_URL_SHARELACTION")

# LIFF static webform


@app.route("/", methods=["GET", "POST"])
def callback():

    if request.method == "GET":
        return "Hello Heroku"
    if request.method == "POST":
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return "OK"


@handler.add(PostbackEvent)
def handle_postback(event):
    get_data = event.postback.data
    LineID = json.loads(str(event.source))['userId']
    # 註冊選單按鈕
    if get_data == "Menu_Register":
        if IsLINEIDExsit(LineID):
            reply = TextSendMessage(
                "請依照格式[ @Register:Name ]輸入您的姓名。\r\n EX: @Register:華安")
            line_bot_api.reply_message(event.reply_token, reply)
        else:
            reply = TextSendMessage(
                "請依照格式[ @SignIn:password ]輸入綁定密碼。\r\n EX: @SignIn:abc123456789\r\n綁定成功後再點擊一次選單的註冊按鈕")
            line_bot_api.reply_message(event.reply_token, reply)
    # 說明選單按鈕
    elif get_data == "Menu_Description":
        reply = TextSendMessage("這是說明按鈕，目前沒有任何的功用")
        line_bot_api.reply_message(event.reply_token, reply)

    # 接收註冊 Postback 資訊
    elif get_data[:18] == '{"type":"Register"':

        json_data = json.loads(get_data)
        staffname = json_data['Name']
        lineid = json_data['lineID']

        if RegisterLINEIDAndStaffName(lineid, staffname):
            txt = '註冊成功!'
        else:
            txt = '註冊失敗，請聯絡磊登相關人員協助處理。'

        reply = TextSendMessage(text=f"{txt}")

        line_bot_api.reply_message(event.reply_token, reply)

    # 其他 Postback 資訊
    else:
        reply = TextSendMessage(text=f"{get_data}")
        line_bot_api.reply_message(event.reply_token, reply)


@handler.add(MessageEvent)
def handle_message(event):
    messageType = event.message.type
    lineid = json.loads(str(event.source))['userId']
    # 回傳訊息類行為Text
    if messageType == "text":
        text = event.message.text
        # 登入指令
        if text[:8] == '@SignIn:':
            sfaffID = text[8:].replace(" ", "").replace("　", "")

            if IsStaffIDExsit(sfaffID) == False:
                reply = TextSendMessage(text="該密碼不存在請重新確認。")
                line_bot_api.reply_message(event.reply_token, reply)
            else:
                if IsStaffIDEnabled(sfaffID):
                    reply = TextSendMessage(text="該密碼已被註冊過，請使用尚未註冊過的密碼。")
                    line_bot_api.reply_message(event.reply_token, reply)
                else:
                    if BindingLINEID(lineid, sfaffID):
                        reply = TextSendMessage(
                            text="密碼正確，請再次點擊選單上的註冊按鈕，註冊您的姓名。")
                        line_bot_api.reply_message(event.reply_token, reply)
                    else:
                        reply = TextSendMessage(
                            text="綁定LINEID失敗，請聯絡磊登相關人員。")
                        line_bot_api.reply_message(event.reply_token, reply)

        # 註冊指令
        elif text[:10] == '@Register:':
            staffname = text[10:].replace(" ", "").replace("　", "")

            Confirm_template = TemplateSendMessage(
                alt_text='目錄 template',
                template=ConfirmTemplate(
                    title='-',
                    text='{0} 這是您的名字嗎?'.format(staffname),
                    actions=[
                          PostbackTemplateAction(
                              label='YES',
                              text='YES',
                              data='{{\"type\":\"Register\",\"Name\":\"{0}\",\"lineID\":\"{1}\"}}'.format(
                                  staffname,
                                  lineid
                              )
                          ),
                         MessageTemplateAction(
                              label='No',
                              text='NO'
                          )
                    ]
                )
            )
            line_bot_api.reply_message(event.reply_token, Confirm_template)
    else:
        reply = TextSendMessage(text=f"{event}")
        line_bot_api.reply_message(event.reply_token, reply)


def SendSqlCommand(SqlCmd):
    # 資料庫連線設定
    db = pymysql.connect(
        host='60.250.50.196',
        port=10987,
        user='OutSideUser',
        passwd='7x4r4t7?2jvcua+s+',
        db='LineBot_KY',
    )
    # 建立操作游標
    cursor = db.cursor()
    try:
        # 执行sql语句
        cursor.execute(SqlCmd)
        # 提交到数据库执行
        db.commit()
        return True
    except:
        # 如果发生错误则回滚
        db.rollback()
        return False
    finally:
        # 關閉連線
        db.close()


def SearchSqlCommand(SqlCmd):
    # 資料庫連線設定
    db = pymysql.connect(
        host='60.250.50.196',
        port=10987,
        user='OutSideUser',
        passwd='7x4r4t7?2jvcua+s+',
        db='LineBot_KY',
    )
    # 建立操作游標
    cursor = db.cursor()
    try:
        # 执行SQL语句
        cursor.execute(SqlCmd)
        # 获取所有记录列表
        results = cursor.fetchall()
        return results
    except:
        # 如果发生错误则回滚
        db.rollback()
        return None
    finally:
        # 關閉連線
        db.close()


def GetTodayData():
    return []


# 將StaffID綁定LINEID
def BindingLINEID(LineID, StaffID):
    cmd = "UPDATE `LineBot_KY`.`ManagerInfo` SET `LineID`='{0}', `Enabled`='1' WHERE `ID`='{1}' AND `Enabled` = 0;".format(
        LineID, StaffID)
    return SendSqlCommand(cmd)


# 該註冊該LINE帳號與使用者姓名
def RegisterLINEIDAndStaffName(LINEID, StaffName):
    cmd = "UPDATE `LineBot_KY`.`ManagerInfo` SET `LineID`='{0}', `Name`='{1}' WHERE  `LineID`='{0}';".format(
        LINEID, StaffName)
    return SendSqlCommand(cmd)


# 是否尚未註冊
def IsDesRegister(LINEID):
    cmd = "SELECT 1 FROM ManagerInfo WHERE ManagerInfo.LineID = '{0}' AND `StaffName`='Unknown'".format(
        LINEID
    )
    datas = SearchSqlCommand(cmd)
    if datas == None:
        return False
    if len(datas) != 0:
        return True
    else:
        return False


# 該StaffID是否啟用過
def IsStaffIDEnabled(StaffID):
    cmd = "SELECT 1 FROM ManagerInfo WHERE ManagerInfo.ID = '{0}' AND ManagerInfo.Enabled = '1'".format(
        StaffID
    )
    datas = SearchSqlCommand(cmd)
    if datas == None:
        return False
    if len(datas) != 0:
        return True
    else:
        return False

# 該StaffID是否存在


def IsStaffIDExsit(StaffID):
    cmd = "SELECT 1 FROM ManagerInfo WHERE ManagerInfo.ID = '{0}';".format(
        StaffID
    )
    datas = SearchSqlCommand(cmd)
    if datas == None:
        return False
    if len(datas) != 0:
        return True
    else:
        return False


def IsLINEIDExsit(LINEID):
    cmd = "SELECT 1 FROM ManagerInfo WHERE ManagerInfo.LineID = '{0}'".format(
        LINEID
    )
    datas = SearchSqlCommand(cmd)
    if datas == None:
        return False
    if len(datas) != 0:
        return True
    else:
        return False
