import tkinter
import tkinter as tk
from tkinter import ttk

from tkinter import ttk
from tkinter.messagebox import showinfo

from tkinter_utils import my_toplevel_window

import py_block_diagram as pybd

import copy

import rwkos, os


class get_slide_number_dialog(my_toplevel_window):
    def __init__(self, parent, title="Enter Slide Number", \
                 geometry='275x150', \
                 ):        
        super().__init__(parent, title=title, geometry=geometry)
        self.parent = parent
        self.make_widgets()
        self.bind('<Control-q>', self.on_cancel_btn)
        self.bind('<Control-g>', self.on_go_btn)        
        self.bind('<Return>', self.on_go_btn)


    def make_widgets(self):
        mycol = 0
        currow = 0
        self.make_label_and_grid_sw("Slide Number", currow, mycol)#, root=self.left_frame)
        currow += 1
        self.make_entry_and_var_grid_nw("slide_number", currow, mycol, sticky='ew')
        self.button_frame1 = ttk.Frame(self)
        self.make_button_and_grid("Cancel", 0, 0, root=self.button_frame1, command=self.on_cancel_btn)
        self.make_button_and_grid("Go", 0, 1, root=self.button_frame1, command=self.on_go_btn)
        self.button_frame1.grid(row=10, column=0)
        self.slide_number_entry.focus_set()


    def on_go_btn(self, *args, **kwargs):
        # - make the folder
        # - create the main latex tex file and slides md file
        print("in on_go_btn")
        slide_num = self.slide_number_var.get()
        print("slide_num: %s" % slide_num)
        self.parent.go_to_slide_number(slide_num)
        self.destroy()



    def on_cancel_btn(self, *args, **kwargs):
        print("in on_canel_btn")
        self.destroy()
