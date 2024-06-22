import requests
from PIL import Image
from io import BytesIO


def resize_image(image, target_height):
    # Рассчитываем соотношение сторон
    aspect_ratio = image.width / image.height
    # Вычисляем новую ширину, сохраняя соотношение сторон
    new_width = int(target_height * aspect_ratio)
    # Изменяем размер изображения
    resized_image = image.resize((new_width, target_height))
    return resized_image


def merge_images_horizontally(url1, url2, output_path):
    if "Нет изображения" != url1:
        response1 = requests.get(url1)
        image1 = Image.open(BytesIO(response1.content))
    else:
        image1 = Image.open("D:\\PROJECTS\\shoparsers\\temp\\default.png")  # todo
    if "Нет изображения" != url2:
        response2 = requests.get(url2)
        image2 = Image.open(BytesIO(response2.content))
    else:
        image2 = Image.open("D:\\PROJECTS\\shoparsers\\temp\\default.png")  # todo
    target_height = min(image1.height, image2.height)
    image1_resized = resize_image(image1, target_height)
    image2_resized = resize_image(image2, target_height)
    width1, height1 = image1_resized.size
    width2, height2 = image2_resized.size
    total_width = width1 + width2
    new_image = Image.new('RGB', (total_width, target_height), (255, 255, 255))
    new_image.paste(image1_resized, (0, 0))
    new_image.paste(image2_resized, (width1, 0))

    path = "D:\\PROJECTS\\shoparsers\\temp\\" + output_path + ".jpg"
    new_image.save(path)  # todo заменить на путь из .env
    return path


# Пример использования
# merge_images_horizontally('https://example.com/image1.jpg', 'https://example.com/image2.jpg', 'merged_image.jpg')
