import hashlib

import requests
from PIL import Image
from io import BytesIO
import math


def resize_image(image, target_size):
    # Изменяем размер изображения, сохраняя соотношение сторон
    image.thumbnail((target_size, target_size))
    return image


def merge_images_square(urls):
    images = []
    filename = ""
    # Загрузка изображений
    for url in urls:
        if "Нет изображения" != url:
            filename += url
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
        else:
            image = Image.open("D:\\PROJECTS\\shoparsers\\temp\\default.png")  # todo заменить на путь из .env
        images.append(image)

    # Определение целевого размера (минимальный размер среди всех изображений)
    target_size = min(min(image.size) for image in images)

    # Изменение размера всех изображений до целевого размера
    resized_images = [resize_image(image, target_size) for image in images]

    # Вычисление размера коллажа
    num_images = len(resized_images)
    collage_size = math.ceil(math.sqrt(num_images)) * target_size

    # Создание нового изображения с белым фоном
    new_image = Image.new('RGB', (collage_size, collage_size), (255, 255, 255))

    # Вставка каждого изображения в новый холст
    current_x = 0
    current_y = 0
    for i, image in enumerate(resized_images):
        new_image.paste(image, (current_x, current_y))
        current_x += target_size
        if current_x >= collage_size:
            current_x = 0
            current_y += target_size

    # Сохранение нового изображения
    hash_filename = hashlib.md5(filename.encode()).hexdigest()
    path = "D:\\PROJECTS\\shoparsers\\temp\\" + hash_filename + ".jpg"
    new_image.save(path)  # todo заменить на путь из .env
    return path

# Пример использования
# urls = ['https://example.com/image1.jpg', 'https://example.com/image2.jpg', 'https://example.com/image3.jpg']
# merge_images_square(urls, 'merged_image')
