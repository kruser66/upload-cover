import os
import logging
import requests
from telegram import Bot
from time import sleep
import vk_api as vk
from dotenv import load_dotenv
from tg_logs_handler import TgLogsHandler

logger = logging.getLogger('vk-cover')


def get_image_from_url(url, filename):
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)


def fetch_covers_from_album(vk_api, group_id, album_id):
    covers = vk_api.photos.get(
        owner_id=-group_id,
        album_id=album_id)

    relevant_photos = []
    for photos in covers['items']:
        relevant_photos += [
            photo for photo in photos['sizes'] if photo['height'] == 530
        ]

    return relevant_photos


def upload_cover(vk_api, vk_upload, group_id, url, width, height):
    get_image_from_url(url, 'image.jpg')
    vk_upload.photo_cover(
        photo='image.jpg',
        group_id=group_id,
        crop_x=0,
        crop_x2=width,
        crop_y=0,
        crop_y2=height
    )


if __name__ == '__main__':

    load_dotenv()

    # мониторинг ошибок через сообщения в Телеграм
    tg_chat_id = os.environ['TG_CHAT_ID']
    tg_token = os.environ['TG_BOT_TOKEN']
    tg_bot = Bot(token=tg_token)
    logger.addHandler(TgLogsHandler(tg_bot, tg_chat_id))

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    service_token = os.environ['VK_SERVICE_KEY']
    group_token = os.environ['VK_GROUP_TOKEN']
    group_id = int(os.environ['VK_GROUP_ID'])
    album_id = os.environ['VK_ALBUM_WITH_COVER_ID']
    delay = int(os.environ['DELAY'])

    # для работы с альбомами ВК
    vk_service_session = vk.VkApi(token=service_token, api_version='5.131')
    vk_service_api = vk_service_session.get_api()

    # для работы с группой
    vk_session = vk.VkApi(token=group_token, api_version='5.131')
    vk_api = vk_session.get_api()
    vk_upload = vk.VkUpload(vk_session)

    logger.info('Запущен модуль смены обложек vk-cover')

    while True:
        try:
            covers = fetch_covers_from_album(
                vk_service_api,
                group_id,
                album_id
            )
        except Exception as error:
            logger.exception(f'VK_COVER: Ошибка {error}')

        for cover in covers:
            try:
                cover.pop('type', None)
                upload_cover(vk_api, vk_upload, group_id, **cover)
            except Exception as error:
                logger.exception(f'VK_COVER: Ошибка {error}')
            sleep(delay)
