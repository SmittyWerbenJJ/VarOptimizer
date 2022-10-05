
from PIL import Image, ImageOps


class ImageUtils:

    @staticmethod
    def resizeImage(image: Image.Image, newImageSize: int):
        if image.width <= newImageSize or image.height <= newImageSize:
            return image
        return ImageOps.contain(image, (newImageSize, newImageSize))

    @staticmethod
    def extractConvertArchivedImage(image):
        pass
