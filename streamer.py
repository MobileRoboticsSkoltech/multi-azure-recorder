#!/usr/bin/env python3
import tkinter as tk
from PIL import Image, ImageTk
from itertools import cycle
import numpy as np
import sys
import argparse

image_path = '/mnt/mrob_tmpfs/images'
ids = ['000583592412', '000905794612', '000489713912']

class Application(tk.Tk):

    def __init__(self, flip, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.flip = flip

        self.title('mrob_viewer')
        self.geometry("836x870")
        self.resizable(width=False, height=False)
        #self.label = tk.Label(self)
        #self.label.pack()

        self.labels = []
        self.images = [[None, None], [None, None], [None, None]]
        for row in range(1,3+1):
            temp = []
            for column in range(1,2+1):
                label = tk.Label(self)
                label.grid(row=row, column=column)   
                temp.append(label)
            self.labels.append(temp)

        self.duration_ms = 100
        self.n = 1

    def rescale(self, array):
        out = 255.0 / (array.max() - array.min()) * (array - array.min())
        return out.astype(np.uint8)

    def config_label(self, image, image_index, row_index):
        self.images[image_index][row_index] = ImageTk.PhotoImage(image)
        self.labels[image_index][row_index].config(image=self.images[image_index][row_index])
        
    def prepare_color(self, image, image_index):
        image = Image.open(image)
        image = image.resize((int(image.size[0]/2.5), int(image.size[1]/2.5)))
        if self.flip:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        self.config_label(image, image_index, 0)
        
    def prepare_depth(self, image, image_index):
        array = np.fromfile(image, dtype=np.uint16)
        array = self.rescale(array)            
        image = Image.fromarray(array.reshape(576,640)[::2,::2])
        if self.flip:
            image = image.transpose(Image.FLIP_LEFT_RIGHT)
        self.config_label(image, image_index, 1)

    def display_next_slide(self):
        try:
            for i in range(3):
                self.prepare_color(f'{image_path}/{ids[i]}/color/0.jpg', i)
                self.prepare_depth(f'{image_path}/{ids[i]}/depth/0.bin', i)
        except:
            pass

        self.after(self.duration_ms, self.display_next_slide)
 
    def start(self):
        self.display_next_slide()

def main():
    argument_parser = argparse.ArgumentParser("Multiview streamer")
    argument_parser.add_argument("--flip", "-f", type=int, required=False, default=0)
    args = argument_parser.parse_args()
    if args.flip == 0:
        flip = False
    elif args.flip == 1:
        flip = True
    else:
        raise RuntimeError("Only 0 and 1 values allowed for flip parameter")

    application = Application(flip)
    application.start()
    application.mainloop()

if __name__ == '__main__':
    main()
