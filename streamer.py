#!/usr/bin/env python3
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
from itertools import cycle
import numpy as np
import sys
import argparse


class Application(tk.Tk):

    def __init__(self, flip, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        self.flip = flip

        self.title('mrob_viewer')
        self.geometry("836x870")
        self.resizable(width=False, height=False)
        #self.label = tk.Label(self)
        #self.label.pack()

        self.label1 = tk.Label(self)
        self.label1.grid(row=1, column=1)
        self.label2 = tk.Label(self)
        self.label2.grid(row=1, column=2)
        
        self.label3 = tk.Label(self)
        self.label3.grid(row=2, column=1)
        self.label4 = tk.Label(self)
        self.label4.grid(row=2, column=2)

        self.label5 = tk.Label(self)
        self.label5.grid(row=3, column=1)
        self.label6 = tk.Label(self)
        self.label6.grid(row=3, column=2)

        self.duration_ms = 100
        self.n = 1

    #def set_image_directory(self, path):
    #    global next_image
    #    image_paths = Path(path).glob("*color.jpg")
    #    self.imnames = cycle(map(lambda p: p.name, image_paths))
    #    self.imbufs = cycle(map(ImageTk.PhotoImage, map(Image.open, image_paths)))
    #    next_image = next(self.imbufs)


    def display_next_slide(self):
        #image_paths = Path('/tmp').glob("*color.jpg")
        #self.imnames = cycle(map(lambda p: p.name, image_paths))
        #self.imbufs = cycle(map(ImageTk.PhotoImage, map(Image.open, image_paths)))
        #next_image = next(self.imbufs)
        #name, next_image = next(self.images)
        #name = next(self.imnames)
        #next_image = next(self.imbufs)
        def rescale(array):
            out = 255.0 / (array.max() - array.min()) * (array - array.min())
            return out.astype(np.uint8)
        
        try:
            image = Image.open('/tmp/000583592412_color.jpg')
            image = image.resize((int(image.size[0]/2.5), int(image.size[1]/2.5)))
            if self.flip:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            self.next_image = ImageTk.PhotoImage(image)
            self.label1.config(image=self.next_image)
            
            array = np.fromfile('/tmp/000583592412_depth.bin', dtype=np.uint16)
            array = rescale(array)            
            image = Image.fromarray(array.reshape(576,640)[::2,::2])
            if self.flip:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            self.next_image2 = ImageTk.PhotoImage(image)
            self.label2.config(image=self.next_image2)

            image = Image.open('/tmp/000905794612_color.jpg')
            image = image.resize((int(image.size[0]/2.5), int(image.size[1]/2.5)))
            if self.flip:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            self.next_image3 = ImageTk.PhotoImage(image)
            self.label3.config(image=self.next_image3)
            
            array = np.fromfile('/tmp/000905794612_depth.bin', dtype=np.uint16)
            array = rescale(array)
            image = Image.fromarray(array.reshape(576,640)[::2,::2])
            if self.flip:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            self.next_image4 = ImageTk.PhotoImage(image)
            self.label4.config(image=self.next_image4)

            image = Image.open('/tmp/000489713912_color.jpg')
            image = image.resize((int(image.size[0]/2.5), int(image.size[1]/2.5)))
            if self.flip:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            self.next_image5 = ImageTk.PhotoImage(image)
            self.label5.config(image=self.next_image5)
            
            array = np.fromfile('/tmp/000489713912_depth.bin', dtype=np.uint16)
            array = rescale(array)
            image = Image.fromarray(array.reshape(576,640)[::2,::2])
            if self.flip:
                image = image.transpose(Image.FLIP_LEFT_RIGHT)
            self.next_image6 = ImageTk.PhotoImage(image)
            self.label6.config(image=self.next_image6)
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
