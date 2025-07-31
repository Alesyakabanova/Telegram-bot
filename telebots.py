import telebot
import webbrowser
from telebot import types
import requests
import json
import time
bot=telebot.TeleBot('8171715913:AAHFpEZvfL8QleS2L6sVjaKw1ay6bJKIobo')
       

@bot.message_handler(commands=['start'])
def main(message):
    
    button1=types.KeyboardButton('Перейти на сайт')
    markup=types.ReplyKeyboardMarkup()
    markup.add(button1)
    
    bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}', reply_markup=markup)
    
    #bot.register_next_step_handler(message, on_click)




@bot.message_handler(content_types=['video'])
def handle_video(message):
    TOKEN = "8171715913:AAHFpEZvfL8QleS2L6sVjaKw1ay6bJKIobo"

    SPEECHFLOW_API_URL = "https://api.speechflow.io/asr/file/v1/create"

    API_KEY_ID = "KKQXbZJzVgsU8lar"
    API_KEY_SECRET = "aH79RWxtjOlFltNh"

    
    video = message.video
    file_id = video.file_id

    
    file_info = bot.get_file(file_id)
    file_path = file_info.file_path
    
    telegram_file_url = f"https://api.telegram.org/file/bot8171715913:AAHFpEZvfL8QleS2L6sVjaKw1ay6bJKIobo/{file_path}"
    response = requests.get(telegram_file_url)

    if response.status_code == 200:
        video_data = response.content

        # Отправляем файл на SpeechFlow
        try:
            
            SPEECHFLOW_API_URL = "https://api.speechflow.io/asr/file/v1/create?lang=ru"  # Язык можно изменить

            
            headers = {
                "keyId": API_KEY_ID,
                "keySecret": API_KEY_SECRET,
            }

            files = {'file': ('video.mp4', video_data)}

            upload_response = requests.post(SPEECHFLOW_API_URL, files=files, headers=headers)
            upload_response.raise_for_status()

            speechflow_response = upload_response.json()

            if 'taskId' in speechflow_response:
                task_id = speechflow_response['taskId']
                bot.send_message(message.chat.id, f"Задача транскрибации создана. ID задачи: {task_id}")

                max_attempts = 20  
                delay = 10  

                for attempt in range(max_attempts):
                        print(f"Попытка {attempt + 1} получения транскрипции...")
                        transcription_result = query(task_id, headers)
                        
                        if transcription_result and 'result' in transcription_result:
                            try:
                                result_json = json.loads(transcription_result['result'])
                                transcribed_text = ""
                                for sentence in result_json['sentences']:
                                    transcribed_text += sentence['s'] + " "
                                transcribed_text = transcribed_text.strip()
                                bot.send_message(message.chat.id, f"Транскрибированный текст:\n{transcribed_text}")
                                return  
                            except json.JSONDecodeError as e:
                                bot.send_message(message.chat.id, f"Ошибка разбора JSON результата: {e}")
                                return

                        elif transcription_result and 'code' in transcription_result and transcription_result['code'] != 10000:
                            error_message = transcription_result.get('msg', 'Неизвестная ошибка')
                            bot.send_message(message.chat.id, f"Ошибка транскрибации: {error_message}")
                            return


                        time.sleep(delay)  

                    
                bot.send_message(message.chat.id, "Не удалось получить результат транскрибации после нескольких попыток.")



            else:
                bot.send_message(message.chat.id, f"Ошибка: SpeechFlow не вернул taskId. Ответ: {speechflow_response}")

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при отправке видео на SpeechFlow: {e}")
            bot.send_message(message.chat.id, f"Ошибка при отправке видео на SpeechFlow: {e}")

    else:
        print(f"Ошибка при скачивании файла из Telegram: {response.status_code}")
        bot.send_message(message.chat.id, f"Ошибка при скачивании файла из Telegram: {response.status_code}")

def get_transcription_result(task_id, headers):
    """Получает результат транскрибации по task_id."""
    transcription_url = f"https://api.speechflow.io/asr/file/v1/query?taskId={task_id}"  
    try:
        response = requests.get(transcription_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе результата транскрибации: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Ошибка при разборе JSON: {e}")
        return None
    


def query(task_id, headers):
    query_url = "https://api.speechflow.io/asr/file/v1/query?taskId=" + task_id + "&resultType=" + str(1)
    print('querying transcription result')
    while (True):
        response = requests.get(query_url, headers=headers)
        if response.status_code == 200:
            query_result = response.json()
            if query_result["code"] == 11000:
                print('transcription result:')
                return query_result
                break
            elif query_result["code"] == 11001:
                print('waiting')
                time.sleep(3)
                continue
            else:
                print(query_result)
                print("transcription error:")
                print(query_result['msg'])
                break
        else:
            print('query request failed: ', response.status_code)



bot.polling(none_stop=True)  