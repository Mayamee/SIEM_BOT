import datetime
import requests
import json
import telebot
from telebot import types
import emoji
import threading
import time
import warnings


class RuSIEMBot(object):

    def __init__(self, token, chatID, ip, api):
        """
        Constructor
        """

        self.TOKEN = token
        self.bot = telebot.TeleBot(token)
        self.CHATID = chatID
        self.API = api
        self.IP = ip
        self.keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        btn1 = types.KeyboardButton("Назначенные инциденты")
        btn2 = types.KeyboardButton("Список инцидентов")
        self.keyboard.add(btn1, btn2)
        self.assignedList = []

    def changeKeyBoard(self, keyboard):
        """
        Делает клавиатуру
        :return: Self
        """
        self.keyboard = keyboard
        return self

    def parseAssigned(self):
        """
        Зарос в базу за новыми инцидентами с обработкой ответа
        :return: string
        """
        json_parse = self.requestIncidentString()
        if json_parse['recordsFiltered'] == 0:
            return emoji.emojize('Все хорошо, отдыхаем) :thumbs_up:')
        else:
            lister = []
            for key in json_parse['data']:
                lister.append(f"id: {str(key['id'])}")
                lister.append(f"Название: {key['name']}")
                lister.append(f"Статус: {key['status']}")
                lister.append(f'Значения:{str(key["group_by_value"])}')
                lister.append(f'Ссылка на инцидент: https://{self.IP}/incidents#!/item/{str(key["id"])}' + "\n")
            return "\n".join(lister).strip()

    def requestIncidentString(self):
        """
        Запрос в базу за новыми инцидентами
        :return: dict
        """

        data = {'status': "assigned"}
        headers = {'Content-type': 'application/json',  # Определение типа данных
                   'Accept': 'text/plain',
                   'Content-Encoding': 'utf-8'}
        r = requests.get(f'https://{self.IP}/api/v1/incidents?_api_key={self.API}', verify=False,
                         data=json.dumps(data), headers=headers)
        json_parse = json.loads(r.text)
        return json_parse

    def getAssignedIncident(self):  # debug
        """
        Ручная проверка инцидента в telegram
        :return: self
        """
        json_parse = self.requestIncidentString()
        if json_parse['recordsFiltered'] != 0:
            all_list = []
            for elem in json_parse['data']:
                all_list.append(elem)
            newList = self.getUnqueIncidents(all_list)
            self.assignedList = all_list
            lister = []
            for item in newList:
                lister.append("Инцидент:")
                lister.append(f"id: {str(item['id'])}")
                lister.append(f"Название: {item['name']}")
                lister.append(f"Статус: {item['status']}")
                lister.append(f'Значения:{str(item["group_by_value"])}')
                lister.append(f'Ссылка на инцидент: https://{self.IP}/incidents#!/item/{str(item["id"])}' + "\n")
            ans = "\n".join(lister).strip()
            if ans:
                ans = emoji.emojize(":warning: Назначен инцидент! :warning:\n") + ans
                self.bot.send_message(self.CHATID, ans)
            else:
                print("New incidents wasn't found")
        else:
            self.assignedList.clear()

    def getUnqueIncidents(self, newListIncidents):
        """
        Находит уникальные инциденты
        :param newListIncidents: Список новых инцидентов
        :return: self
        """
        nonCollizeList = []
        flag = True
        for i in newListIncidents:
            for j in self.assignedList:
                if i["id"] == j["id"]:
                    flag = False
                    break
            if flag:
                nonCollizeList.append(i)
            flag = True
        return nonCollizeList
        # return self

    def getStatus(self):
        """
        Статус
        :return:
        """
        req_data = {
            "reopen": {"status": "reopen"},
            "in_work": {"status": "in_work"},
            "assigned": {"status": "assigned"},
        }

        headers = {
            'Content-type': 'application/json',
            'Accept': 'text/plain',
            'Content-Encoding': 'utf-8'
        }

        res = dict()
        url = f"https://{self.IP}/api/v1/incidents?_api_key={self.API}"
        res["reopen"] = requests.get(url, verify=False, data=json.dumps(req_data["reopen"]), headers=headers).text
        res["assigned"] = requests.get(url, verify=False, data=json.dumps(req_data["assigned"]), headers=headers).text
        res["in_work"] = requests.get(url, verify=False, data=json.dumps(req_data["in_work"]), headers=headers).text
        res["all"] = requests.get(url, verify=False, headers=headers).text

        res["reopen"] = json.loads(res["reopen"])["recordsFiltered"]
        res["assigned"] = json.loads(res["assigned"])["recordsFiltered"]
        res["in_work"] = json.loads(res["in_work"])["recordsFiltered"]
        res["all"] = json.loads(res["all"])["recordsFiltered"]
        return res

    def sendMessage(self, message):
        """
        test
        :return:
        """
        self.bot.send_message(self.CHATID, message)

    def openTelegramListener(self):
        """
        Подключает модуль обработчика сообщений для группы
        :return: self
        """

        @self.bot.message_handler(content_types=['text'])
        def messageWorker(message):
            if message.text.__contains__("/start"):
                self.bot.send_message(self.CHATID, "Высылаю клавиши управления", reply_markup=self.keyboard)
            if message.text.__contains__("Назначенные инциденты"):
                self.bot.send_message(self.CHATID, self.parseAssigned())
            if message.text.__contains__("Список инцидентов"):
                statusOfIncidents = self.getStatus()
                string = "Все инциденты: " + str(statusOfIncidents["all"]) + "\n"
                string += "В работе: " + str(statusOfIncidents["in_work"]) + "\n"
                string += "Назначен: " + str(statusOfIncidents["assigned"]) + "\n"
                string += "Переоткрытых: " + str(statusOfIncidents["reopen"])
                self.bot.send_message(self.CHATID, string)

        return self

    def start(self):
        """
        Стартует бота
        :return: Self
        """
        self.bot.polling()
        return self



_CHATID = "XXX"
_BOT_TOKEN = "XXX"
_IP_SIEM = "XXX"
_SIEM_API_TOKEN = "XXX"
warnings.filterwarnings("ignore")
ruBot = RuSIEMBot(_BOT_TOKEN, _CHATID, _IP_SIEM, _SIEM_API_TOKEN)


def telegramCommandsListener():
	while True:
		try:
		    ruBot.openTelegramListener()
    		    ruBot.start()	
		except Exception as e:
		    print("Telegram is broken")
    		    time.sleep(5)


def listenerIncedents():
    while True:
        try:
            ruBot.getAssignedIncident()
            time.sleep(60)
        except:
            print("Lost connection to " + ruBot.IP)
            time.sleep(5)


t1 = threading.Thread(target=telegramCommandsListener).start()
t2 = threading.Thread(target=listenerIncedents).start()
