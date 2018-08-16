import json
import time
import vk_api
import datetime
import os
import requests


class VkClient:
    def __init__(self, login, password, messages_with_groups):
        self.__login = login
        self.__password = password
        file = open('./message_files/' + messages_with_groups, 'r')
        self.__messages_with_groups = json.load(file)
        file.close()

    def get_login(self):
        return self.__login

    def get_password(self):
        return self.__password

    def get_messages_with_groups(self):
        return self.__messages_with_groups


class PipLine:
    def __init__(self):
        self.__clients = list()
        self.__time_for_sleep = 3600

    def add(self, client):
        assert isinstance(client, VkClient)
        self.__clients.append(client)

    def set_time_for_sleep(self, time_for_sleep):
        assert isinstance(time_for_sleep, int)
        self.__time_for_sleep = time_for_sleep

    def get_clients(self):
        return self.__clients

    def get_time_for_sleep(self):
        return self.__time_for_sleep


class WorkWithVk:
    def __init__(self):
        self._opened_session = list()

    def open_sessions(self, clients):
        for client in clients:
            vk = vk_api.VkApi(login=client.get_login(), password=client.get_password(),
                              auth_handler=self._auth_handler, captcha_handler=self._captcha_handler)
            vk.auth()
            vk_helper = vk.get_api()
            self._opened_session.append(
                {
                    'login': client.get_login(),
                    'id_and_messanges': client.get_messages_with_groups(),
                    'session': vk_helper
                }
            )

    def _auth_handler(self):
        """ При двухфакторной аутентификации вызывается эта функция."""

        # Код двухфакторной аутентификации
        key = input("Enter authentication code: ")
        # Если: True - сохранить, False - не сохранять.
        remember_device = True

        return key, remember_device

    def _captcha_handler(self, captcha):
        """ При возникновении капчи вызывается эта функция и ей передается объект
            капчи. Через метод get_url можно получить ссылку на изображение.
            Через метод try_again можно попытаться отправить запрос с кодом капчи
        """

        key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()

        # Пробуем снова отправить запрос с капчей

        return captcha.try_again(key)

    def get_count_of_opened_session(self):
        return len(self._opened_session)

    def get_sessions(self):
        return self._opened_session

    def process_messanges(self, session, response):
        for chat in response['items']:
            if chat['conversation']['peer']['type'] == 'user':

                vk_id = chat['conversation']['peer']['id']
                message_for_send = 'default_message'
                for group in session['id_and_messanges']['groups']:
                    if vk_id in session['id_and_messanges']['groups'][group]['list_of_id']:
                        message_for_send = session['id_and_messanges']['groups'][group]['message']

                if message_for_send == 'default_message':
                    if vk_id in session['id_and_messanges']['constant_groups']['ignored']['list_of_id']:
                        pass
                    else:
                        message_for_send = session['id_and_messanges']['constant_groups']['other']['message']

                if message_for_send != 'default_message':
                    if chat['conversation']['can_write']:
                        result = session['session'].messages.send(user_id=int(vk_id), message=message_for_send, captcha_handler=self._captcha_handler)
                        print('Отправленно сообщение к', vk_id)
                    else:
                        print('Не могу отправить сообщение. Нет доступа или прав!')


class Facade:
    def __init__(self):
        self._pipline = PipLine()
        self._workwithvk = WorkWithVk()

    def add(self, client):
        self._pipline.add(client)

    def set_time_for_sleep(self, time_for_sleep):
        self._pipline.set_time_for_sleep(time_for_sleep)

    def start(self):
        while True:
            if self._workwithvk.get_count_of_opened_session() == 0:
                self._workwithvk.open_sessions(self._pipline.get_clients())

            for session in self._workwithvk.get_sessions():
                response = session['session'].messages.getConversations(filter='unread')
                if response['count'] > 0:
                    print(str(datetime.datetime.now()), 'У тебя есть новые сообщения в профиле', session['login'], '!',
                          'Количество новых сообщений:', response['count'] )
                    self._workwithvk.process_messanges(session, response)

            time.sleep(self._pipline.get_time_for_sleep())


class TestingOfInitialConditions:
    def run_all_test(self):
        self.path_exist()
        self.account_config_exist()
        self.config_exist()
        self.check_correct_of_account_config()
        self.check_correct_of_message_config()
        self.check_internet()

    def path_exist(self):
        if not os.path.exists('./accounts/'):
            os.makedirs('./accounts/')

        if not os.path.exists('./message_files'):
            os.makedirs('./message_files')

    def account_config_exist(self):
        if len(os.listdir('./accounts/')) == 0:
            raise HaveNotFile

        if len(os.listdir('./message_files/')) == 0:
            raise HaveNotFile

    def config_exist(self):
        if not os.path.exists('config.json'):
            data = {
                'time_for_sleep': 3600
            }
            with open('config.json', 'w') as file:
                json.dump(data, file)
            raise HaveNotConfig

    def check_correct_of_account_config(self):
        paths = os.listdir('./accounts/')
        for path in paths:
            file = open('./accounts/' + path)
            data = json.load(file)

            tmp_data = {
                'login': 'example@example.example',
                'password': 'example',
                'message_file': 'example.json'
            }

            try:
                _ = data['login']
            except KeyError:
                with open('./accounts/exapmle.json', 'w') as file:
                    json.dump(tmp_data, file)
                raise IncorrectAccountConfig

            try:
                _ = data['password']
            except KeyError:
                with open('./accounts/exapmle.json', 'w') as file:
                    json.dump(tmp_data, file)
                raise IncorrectAccountConfig

            try:
                _ = data['message_file']
            except KeyError:
                with open('./accounts/exapmle.json', 'w') as file:
                    json.dump(tmp_data, file)
                raise IncorrectAccountConfig

    def check_correct_of_message_config(self):
        paths = os.listdir('./message_files/')
        for path in paths:
            file = open('./message_files/' + path)
            data = json.load(file)

            tmp_data = {
                        "groups": {
                            "family": {
                                "message": "some text to family",
                                "list_of_id": []
                            },
                            "work": {
                                "message": "some text to worker",
                                "list_of_id": []
                            },
                            "friends": {
                                "message": "some text to friends",
                                "list_of_id": []
                            }
                        },
                        "constant_groups": {
                            "other": {
                                "message": "some text to other"
                            },
                            "ignored": {
                                "list_of_id": []
                            }
                        }
                    }

            try:
                _ = data['groups']
            except KeyError:
                with open('./message_files/exapmle.json', 'w') as file:
                    json.dump(tmp_data, file)
                raise IncorrectMessageConfig

            try:
                groups = data['constant_groups']
            except KeyError:
                with open('./message_files/exapmle.json', 'w') as file:
                    json.dump(tmp_data, file)
                raise IncorrectMessageConfig

            try:
                _ = data['constant_groups']['other']
            except KeyError:
                with open('./message_files/exapmle.json', 'w') as file:
                    json.dump(tmp_data, file)
                raise IncorrectMessageConfig

            try:
                _ = data['constant_groups']['ignored']
            except KeyError:
                with open('./message_files/exapmle.json', 'w') as file:
                    json.dump(tmp_data, file)
                raise IncorrectMessageConfig

    def check_internet(self):
        for i in range(200):
            try:
                _ = requests.get('http://yandex.ru', timeout=10)
                return True
            except requests.ConnectionError:
                print('Нет интернета. Ждем 10 минут!', 'Была попытка номер', i)
                time.sleep(600)
        try:
            _ = requests.get('http://yandex.ru', timeout=10)
            return True
        except requests.ConnectionError:
            raise NoInternet


class HaveNotFile(Exception):
    '''Нет нужных файлов в папках accounts или message_files'''
    pass


class HaveNotConfig(Exception):
    '''Нет файла конфигурации в корне. Будет создан автоматически'''
    pass


class IncorrectAccountConfig(Exception):
    '''Неправильный файл конфигурации. Ознакомьтесь с exapmle.json в accounts.'''
    pass


class IncorrectMessageConfig(Exception):
    '''Неправильный файл конфигурации. Ознакомьтесь с exapmle.json в message_files.'''
    pass

class NoInternet(Exception):
    '''Нет интернета'''
    pass


class MainConfig:
    def get_time_for_sleep(self):
        file = open('config.json', 'r')
        data = json.load(file)
        return data['time_for_sleep']

    def load_vk_cliens(self):
        vk_clients = list()
        files = os.listdir('./accounts/')

        for path in files:
            file = open('./accounts/' + path, 'r')
            data = json.load(file)
            tmp_client = VkClient(data['login'], data['password'], data['message_file'])
            vk_clients.append(tmp_client)
        return vk_clients


