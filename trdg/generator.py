import cv2
import os
import numpy as np 
import random

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from trdg.generators import (
    GeneratorFromStrings,
)

class FakeTextGenerator():
    def __init__(self, corpus, font_type='cmnd', text_size=28, skewing_angle=10, distorsion_orientation=3, blur=2):
        self.corpus = corpus
        self.font_type = font_type
        self.text_size = text_size
        self.skewing_angle = skewing_angle
        self.distorsion_orientation = distorsion_orientation
        self.blur = blur

    def gen(self, batch_size=16):
        samples = random.sample(self.corpus, k=batch_size)
        generator = GeneratorFromStrings(
            samples,
            count=len(samples),
            blur=self.blur,
            random_blur=True,
            size=self.text_size,
            skewing_angle=self.skewing_angle,
            random_skew=True,
            distorsion_orientation=self.distorsion_orientation,
            language=self.font_type)

        images = []
        labels = []
        for image, label in generator:
            image = np.array(image)[..., ::-1]
            images.append(image)
            labels.append(label)

        return images, labels

if __name__ == "__main__":
    corpus = []
    for i in range(32):
        seq = ''
        num_space = random.randint(1,4)
        for j in range(random.randint(1, 9)):
            seq += str(random.randint(0, 9999)) + ' '*num_space
        corpus.append(seq)

    generator = FakeTextGenerator(corpus=corpus)

    while True:
        img, lbl=generator.gen(batch_size=16)
        print(lbl)
   