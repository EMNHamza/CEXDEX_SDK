# def sendToTelegram(messageDecode: str):
#     try:
#         response = requests.post(
#             apiURL, json={"chat_id": chatID, "text": messageDecode}
#         )
#     except Exception as e:
#         print(e)