import cv2
import math
import os
import random as rnd
import numpy as np
from skimage import util
from PIL import Image, ImageDraw, ImageFilter


def gaussian_noise(height, width, image_dir="./"):
    """
    Create a background with Gaussian noise (to mimic paper)
    """

    # We create an all white image
    image = np.ones((height, width)) * 255

    # We add gaussian noise
    cv2.randn(image, rnd.randint(190, 240), rnd.randint(0,50))

    return Image.fromarray(image).convert("RGBA")


def plain_white(height, width, image_dir="./"):
    """
    Create a plain white background
    """

    return Image.new("L", (width, height), 255).convert("RGBA")


def quasicrystal(height, width, image_dir="./"):
    """
    Create a background with quasicrystal (https://en.wikipedia.org/wiki/Quasicrystal)
    """

    image = Image.new("L", (width, height))
    pixels = image.load()

    frequency = rnd.random() * 30 + 20  # frequency
    phase = rnd.random() * 2 * math.pi  # phase
    rotation_count = rnd.randint(10, 20)  # of rotations

    for kw in range(width):
        y = float(kw) / (width - 1) * 4 * math.pi - 2 * math.pi
        for kh in range(height):
            x = float(kh) / (height - 1) * 4 * math.pi - 2 * math.pi
            z = 0.0
            for i in range(rotation_count):
                r = math.hypot(x, y)
                a = math.atan2(y, x) + i * math.pi * 2.0 / rotation_count
                z += math.cos(r * math.sin(a) * frequency + phase)
            c = int(255 - round(255 * z / rotation_count))
            pixels[kw, kh] = c  # grayscale
    return image.convert("RGBA")


def image(height: int, width: int, image_dir: str) -> Image:
    """
    Create a background with a image
    """
    images = os.listdir(image_dir)

    if len(images) > 0:
        pic = Image.open(
            os.path.join(image_dir, images[rnd.randint(0, len(images) - 1)])
        )

        if pic.size[0] < width:
            pic = pic.resize(
                [width, int(pic.size[1] * (width / pic.size[0]))],
                Image.Resampling.LANCZOS,
            )
        if pic.size[1] < height:
            pic = pic.resize(
                [int(pic.size[0] * (height / pic.size[1])), height],
                Image.Resampling.LANCZOS,
            )

        if pic.size[0] == width:
            x = 0
        else:
            x = rnd.randint(0, pic.size[0] - width)
        if pic.size[1] == height:
            y = 0
        else:
            y = rnd.randint(0, pic.size[1] - height)

        return pic.crop((x, y, x + width, y + height))
    else:
        raise Exception("No images where found in the images folder!")


def salt_and_pepper(height, width, image_dir="./"):


    '''
    Function: Add a variety of random noise to float pictures
    Parameters:
    image: Enter the picture (will be converted to floating point), ndarray type
    mode: choose,strType indicates the type of noise to be added
        gaussian: Gaussian noise
        localvar: additive noise Gaussian distribution with the specified local variance at each point of "image".
        poisson: Poisson regeneration
        salt: Salt noise, the pixel value becomes random1
        pepper: pepper noise, the pixel value becomes random0or-1, Depending on whether the signed value matrix
        s&p: salt and pepper noise
        speckle: uniform noise (variance mean mean variance), out=image+n*image
        
    seed: Optional,intType, if selected, will generate the noise before the first set in order to avoid pseudo-random random seed
    clip: Optional,boolType, if it isTrueAfter adding the mean, Poisson and Gaussian noise, clipping the image data will be within an appropriate range. If someoneFalse, Then the value may exceed the output matrix[-1,1]
    mean: Optional,floatType, mean parameters of the Gaussian noise and the noise mean default value=0
    var: Alternatively,floatType, mean Gaussian noise and noise variance defaults=0.01(Note: not the standard deviation)
    local_vars: Alternatively, ndarry type local variance is used to define each pixel, using the localvar
    amount: Optional,floatType, salt and pepper noise is the proportion of defaults=0.05
    salt_vs_pepper: Optional,floatType, salt and pepper noise ratio, a larger value indicates more salts of noise, the default value=0.5That the same amount of salt and pepper
    --------
    Return Value: ndarry type and value[0,1]or[-1,1]Between, depending on whether there is a signed number
    -------
    Note: slightly (see source)
    '''


    # img=Image.open('outputFile.jpg')
    # img=np.array(img)

    # We create an all white image
    # image = np.ones((img.shape[0], img.shape[1]))
    image = np.ones((height, width)) * 255

    noise_gs_img=util.random_noise(image,mode='s&p', amount=rnd.uniform(0, 0.02), salt_vs_pepper=rnd.random()) #or we can write noise on exists image `img`
    # noise_gs_img=util.random_noise(img,mode='poisson', clip=False)

    noise_gs_img=noise_gs_img*255  # Since the output is [0,1] floating-point, first transferred to greyscale (my input is grayscale)
    # noise_gs_img=noise_gs_img.astype(np.int)   # Then into an array of integers
    # cv2.imwrite(os.path.join(save_dir,image_name),noise_gs_img)  # Save the new folder

    return Image.fromarray(noise_gs_img).convert("RGBA")

def random_all(height, width, image_dir):
    lst_func = [salt_and_pepper, image, quasicrystal, plain_white, gaussian_noise]
    return rnd.choice(lst_func)(height, width, image_dir)  