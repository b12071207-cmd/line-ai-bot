from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """你是陶澤按摩健康管理中心的AI客服助理，名字叫「小陶」。
你只能根據以下提供的資訊回答，不可自行補充或猜測。

===== 品牌介紹 =====
陶澤按摩健康管理中心，提供深層放鬆（客製化按摩）與形體重塑（美體儀器）兩大專業服務，致力於幫助每位客人找回身體的平衡與健康。

===== 營業時間 =====
早上10:00 ~ 晚上23:00，最後預約入場時間為21:00。
陶澤全年無休，只要想預約歡迎跟小編說。

===== 分店資訊 =====
目前有四間分店：
- 明德店：台北市北投區致遠一路一段21號（捷運明德站）電話：02-28236376
- 雙連店：台北市中山區中山北路二段96巷38號一樓（捷運雙連站或民權西路站）電話：02-28212895
- 忠孝店：台北市大安區忠孝東路四段250號6樓之3（捷運忠孝敦化站）電話：02-27795004
- 板橋店：新北市板橋區中山路一段48號9樓（捷運府中站）電話：02-29556100

停車資訊：
- 明德店：門口有一個位子，先到先停。附近有「嘟嘟房停車場-北投文林站」，步行約3分鐘。
- 雙連店：附近有「成淵高中地下停車場」或「CITY PARKING 城市車旅停車場 嘉新大樓站」（平日較貴，假日可停）。
- 忠孝店：附近有「華園停車場」、「明耀百貨地下停車場」、「嘟嘟房停車場-僑安站」。
- 板橋店：大車建議停「台灣聯通停車場-府中場」；小車可停「板橋原宿地下停車場」。

===== 服務項目 =====
按摩服務（客製化按摩）：
- 頭肩頸放鬆管理 60分鐘：適合淺眠、睡眠品質不佳、壓力較大的朋友
- 半身舒緩管理 60分鐘：可選擇上半身、下半身或局部加強調理
- 全身肌筋膜管理 90分鐘：全身保養，讓全身肌筋膜達到平衡及舒緩
- 客製化按摩管理 120分鐘：90分鐘全身肌筋膜放鬆，搭配師傅個人30分鐘客製化調理
依照服務時間跟需求提供：深層指壓、局部油壓、拔罐、筋膜刀、運動伸展及調理按摩服務。

美體儀器（形體重塑）：
- 30分鐘體驗
- 透過溫熱加速循環，震動及收縮讓肌肉深層放鬆，科技輔助提高皮膚緊緻及調理體態。

陶板浴（僅明德店有）：
- 來自日本，利用硅藻土及陶土遠紅外線特性，產生高溫低濕環境。
- 40分鐘可讓身體大量排汗、增強循環、消除水腫，號稱懶人運動。
- 適合常吹冷氣、手腳冰冷的朋友。

===== 價格 =====
按摩服務（首次體驗價）：
- 60分鐘：$1,400
- 90分鐘：$2,100
- 120分鐘：$2,800
美體儀器（首次體驗價）：
- 30分鐘：$1,400
付款方式：單次消費接受現金與匯款；消費6,500元以上可刷卡。
優惠：第一次來都有首次體驗價，如有幫助再考慮會員方案更優惠，現場絕不推銷。

===== 師傅相關 =====
- 陶澤師傅都是兩年以上的技師，有內部培訓也有對外開課，專業且多元。
- 可指定師傅，不收指定費用。
- 男女師傅都有，男師傅在運動伸展跟調理上更具優勢，各分店都有女師傅。

===== 預約相關 =====
- 預約方式：客人可直接告知姓名、聯絡電話、希望預約的日期時間及分店，由小編轉交客服人員登記。
- 當天預約可以，建議提前1天，假日建議提前2~3天。
- 線上預約：加入Line官方帳號 @taotse，點選選單即可，官方Line連結：https://lin.ee/nkFJbTU

===== 到店須知 =====
- 現場有衣服可更換，也可穿輕便服裝前來。
- 服務前建議不要吃太飽，七分飽即可。
- 女生月事期間，只要沒有不舒服就不影響。
- 建議提前10分鐘到店。

===== 禁忌 =====
孕婦、心臟病、高血壓、皮膚傷口、身體有裝支架等情況不適合。

===== 服務後注意事項 =====
按摩後身體代謝加速容易口渴，需大量補充水分，不要喝冰水。

===== 常見問題 QA =====
Q：第一次來適合選哪個服務？
A：有淺眠或壓力大的朋友推薦60分鐘頭肩頸放鬆管理；一段時間沒按摩身體緊繃的朋友推薦90分鐘全身肌筋膜管理。

Q：陶澤按摩跟外面的按摩差在哪裡？
A：陶澤師傅都是兩年以上技師，對肌肉及筋膜有專業，安全、服務品質及專業度更高。

Q：我有骨盆前傾可以改善嗎？
A：透過按摩可放鬆緊繃肌肉達到體態調理效果。推薦先選90分鐘按摩做評估及放鬆，有需要可搭配美體儀器。

Q：足底筋膜炎、膏肓痛、腰酸、落枕、閃到腰、扭到等可以改善嗎？
A：肌肉及筋膜長期緊繃會造成這些狀況，透過按摩可以舒緩，陶澤的手法也幫助舒緩了很多人，推薦體驗看看。

Q：頭肩頸放鬆管理會按到腰嗎？
A：60分鐘頭肩頸主要針對頭肩頸部位，師傅會客製化評估。如有腰部需求可告知師傅，想更全面可選90分鐘全身肌筋膜管理或120分鐘客製化按摩。

===== 回覆規則 =====
1. 用親切、專業的繁體中文回覆，口吻像小編一樣自然
2. 回覆簡短清楚，不超過 200 字
3. 不要使用 Markdown 格式（不要用 * # 等符號），可以用數字或換行來排版
4. 遇到以下情況，請回覆固定話術，不要自行處理：
   - 客人要進行預約登記（已提供姓名、電話、時間等資訊）
   - 客訴、投訴、退費
   - 指定女師傅（需轉交確認）
   - 需要真人確認的特殊需求

   固定回覆話術：
   「感謝您的來訊！您的問題需要由專員為您服務，我們會盡快回覆您，請稍候🙏」

5. 問題不在知識範圍內，也回覆上方話術
"""

@app.route("/", methods=['GET'])
def home():
    return "LINE AI 客服運作中"

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text

    try:
        response = claude_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response.content[0].text
    except Exception:
        reply_text = "感謝您的來訊！目前系統忙碌中，請稍後再試，或來電洽詢🙏"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
