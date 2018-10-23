#!/usr/bin/env python3

from PIL import Image
import os
from matplotlib import pyplot as plt
import numpy as np
import pytesseract
from pprint import pprint

import json

images_dir = 'images'
white_cards_idx = range(3, 25 + 1)
black_cards_idx = range(26, 30 + 1)


def extract_images(indexes):
    texts = []
    for idx in indexes:
        print(idx)
        idx = str(idx).zfill(2)
        fname = f'CAH_PortugueseByMarcelo-{idx}.png'
        fname = os.path.join(images_dir, fname)
        img = Image.open(fname)

        offset = (54, 105)
        card_size = (397, 397)
        for j in range(5):
            for i in range(4):
                left = offset[0] + card_size[0] * i
                top = offset[1] + card_size[1] * j
                right = offset[0] + card_size[0] * (i + 1)
                bottom = offset[1] + card_size[1] * (j + 1)
                bottom -= 72

                cropped = img.crop((left, top, right, bottom))
                #  plt.imshow(np.asarray(cropped))
                #  plt.show()
                #  cropped.show()
                #  print(cropped)
                text = pytesseract.image_to_string(cropped, lang='por')
                text = text.splitlines()
                text = [l.strip() for l in text]
                text = ' '.join(text)
                texts.append(text)
    return texts

white_cards_texts = extract_images(white_cards_idx)
print('white')
pprint(white_cards_texts)
print(len(white_cards_texts))

with open('white.json', 'w') as fout:
    json.dump(white_cards_texts, fout, indent=4)


black_cards_texts = extract_images(black_cards_idx)
print('black')
pprint(black_cards_texts)
print(len(black_cards_texts))

with open('black.json', 'w') as fout:
    json.dump(black_cards_texts, fout, indent=4)
