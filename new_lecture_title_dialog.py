import tkinter
import tkinter as tk
from tkinter import ttk

from tkinter import ttk
from tkinter.messagebox import showinfo

from tkinter_utils import my_toplevel_window

import py_block_diagram as pybd

import copy

import rwkos, os


class new_lecture_title_dialog(my_toplevel_window):
    def __init__(self, parent, classnum, class_prep_root, title="New Lecture Title Dialog", \
                 geometry='500x150', max_loops=3, \
                 ):        
        super().__init__(parent, title=title, geometry=geometry)
        self.columnconfigure(0, weight=4)
        self.parent = parent
        self.classnum = classnum
        self.class_prep_root = class_prep_root
        self.make_widgets()
        self.bind('<Control-q>', self.on_cancel_btn)
        self.bind('<Control-g>', self.on_go_btn)        
        

    def make_widgets(self):
        mycol = 0
        currow = 0
        self.make_label_and_grid_sw("New Lecture Title", currow, mycol)#, root=self.left_frame)
        currow += 1
        self.make_entry_and_var_grid_nw("new_title", currow, mycol, sticky='ew')#, root=None, **grid_opts)
        starting_title = "Class %0.2i: " % self.classnum
        self.new_title_var.set(starting_title)
        self.button_frame1 = ttk.Frame(self)
        self.make_button_and_grid("Cancel", 0, 0, root=self.button_frame1, command=self.on_cancel_btn)
        self.make_button_and_grid("Go", 0, 1, root=self.button_frame1, command=self.on_go_btn)
        self.button_frame1.grid(row=10, column=0)
        

    def on_go_btn(self, *args, **kwargs):
        # - make the folder
        # - create the main latex tex file and slides md file
        print("in on_go_btn")
        new_title = self.new_title_var.get()
        folder_name = rwkos.clean_filename(new_title)
        folder_name = folder_name.lower()
        if '_ht' in folder_name:
            folder_name = folder_name.replace('_ht','_HT')
            
        print("new_title: %s" % new_title)
        print("folder_name: %s" % folder_name)
        folder_path = os.path.join(self.class_prep_root, folder_name)
        rwkos.make_dir(folder_path)
        # try creating the toplevel files in new dir
        os.chdir(folder_path)
        cmd = 'new_md_beamer_pres.py "%s"' % new_title
        print(cmd)
        os.system(cmd)
        self.parent.set_pres_title(new_title)
        self.parent.find_main_files_in_folder(folder_path)
        self.parent.start_new_pres(new_title)
        self.destroy()

        

    def on_cancel_btn(self, *args, **kwargs):
        print("in on_canel_btn")
        self.destroy()
