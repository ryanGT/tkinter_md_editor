#!/usr/bin/env python3
"""
Working on an editor to make it easier to create lecture presentations
in markdown with beamer slides as the assumed output.
"""
import os, glob, rwkos, relpath, re

############################################
#
# Features needed:
#
# - build current slide based on point of cursor
# - move slide up or down based on finding point and slide titles
#     - where does current slide start and end
#     - where does previous or next slide start and end
#     - be careful not to assume unique slide titles
# - eqn editor
# - bookmarks
# - outline view based on slide and section titles
# - status log widget
#     - can we know when latex is done compiling and if the exit was clean
# - button to copy to student folder
#
############################################

############################################
#
# Next Steps:
#
# ----------------
#
# - open current pdf with skim
# - append current to main md and clear
#
#############################################

#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
#
# Issues:
#
#
# Resovled:

#  
#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii


class_prep_root = "/Users/kraussry/class_prep_445_SS22/"

import tkinter
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog
from tkinter.messagebox import askyesno
from tkinter.messagebox import showinfo

import tkinter_utils

from new_lecture_title_dialog import new_lecture_title_dialog

import os, txt_mixin

pad_options = {'padx': 5, 'pady': 5}


mywidth = 10

class_num_pat = "class_%0.2i_*"

## def find_one_glob(glob_pat):
##     matches = glob.glob(glob_pat)
##     assert len(matches) > 0, "did not find a match for %s" % glob_pat
##     assert len(matches) == 1, "found more than one match for %s:\n %s" % (glob_pat, matches)
##     return matches[0]


columns_str = r"""\columnsbegin
\column{.5\textwidth}


\column{.5\textwidth}



\columnsend
"""



def find_class_number_dir(i):
    test_folder_pat = class_num_pat % i
    test_full_pat = os.path.join(class_prep_root, test_folder_pat)
    mylist = glob.glob(test_full_pat)
    assert len(mylist) == 1, "did not find exactly one match for: %s \n mylist %s" % \
           (test_full_pat, mylist)
    return mylist[0]

    
def find_new_class_number():
    for i in range(1,100):
        test_folder_pat = class_num_pat % i
        test_full_pat = os.path.join(class_prep_root, test_folder_pat)
        mylist = glob.glob(test_full_pat)
        if len(mylist) == 0:
            return i


def find_current_class_number():
    i = find_new_class_number()
    j = i-1
    return j


def find_main_file_fno(classnum):
    folder = find_class_number_dir(classnum)
    tex_fn_pat = "class_%0.2i_*_main.tex" % classnum
    tex_full_pat = os.path.join(folder, tex_fn_pat)
    tex_path = rwkos.find_one_glob(tex_full_pat)
    fno, ext = os.path.splitext(tex_path)
    return fno


def find_main_slides_fno(classnum):
    folder = find_class_number_dir(classnum)
    md_fn_pat = "class_%0.2i_*_slides.md" % classnum
    md_full_pat = os.path.join(folder, md_fn_pat)
    md_path = rwkos.find_one_glob(md_full_pat)
    fno, ext = os.path.splitext(md_path)
    return fno


def find_main_pdf(classnum):
    fno = find_main_file_fno(classnum)
    return fno + '.pdf'
    

def find_main_slides_md(classnum):
    fno = find_main_slides_fno(classnum)
    return fno + '.md'


class CustomText(tk.Text):
    '''A text widget with a new method, highlight_pattern()

    example:

    text = CustomText()
    text.tag_configure("red", foreground="#ff0000")
    text.highlight_pattern("this should be red", "red")

    The highlight_pattern method is a simplified python
    version of the tcl code at http://wiki.tcl.tk/3246
    '''
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

    def highlight_pattern(self, pattern, tag, start="1.0", end="end",
                          regexp=False):
        """Apply the given tag to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression according to Tcl's regular expression syntax.
        """

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            if count.get() == 0: break # degenerate pattern which matches zero-length strings
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")

    
class md_gui(tk.Tk, tkinter_utils.abstract_window):
    def set_class_number(self, classnum=None):
        if classnum is None:
            classnum = find_current_class_number()
            
        self.classnum = classnum
        self.class_dir = find_class_number_dir(classnum)
        os.chdir(self.class_dir)


    def set_pdf_and_tex_names_from_md_name(self, md_name):
        self.main_tex_name = md_name.replace("_slides.md", "_main.tex")
        self.main_pdf_name = self.main_tex_name.replace(".tex", ".pdf")
        


    def print_attrs(self, attr_list=['class_dir', 'classnum', 'main_tex_name', 'main_pdf_name']):
        for var in attr_list:
            val = getattr(self, var)
            print("%s: %s" % (var, val))


    def get_classnum_from_md_path(self, md_path):
        folder, md_name = os.path.split(md_path)
        p = re.compile("^class_([0-9]+)_.*_slides.md$")
        q = p.match(md_name)
        if q is not None:
            self.classnum = int(q.group(1))
        else:
            print("md_name did not match pattern: %s" % md_name)


    def set_main_folder_and_files(self, md_path):
        """Set the main md and pdf files along with the working
        directory based on the fullpath of the main md_file."""
        folder, md_name = os.path.split(md_path)
        assert "_slides.md" in md_name, \
               "This does not apprear to be a valid md slides filename: %s" % md_path
        # if we aren't in a class prep folder, classnum is irrelevant
        if class_prep_root in md_path:
            self.classnum = self.get_classnum_from_md_path(md_path)
        else:
            self.classnum = -1#this becomes a flag for non-class prep usage 
        self.class_dir = folder
        self.main_md_name = md_name
        os.chdir(self.class_dir)
        self.set_pdf_and_tex_names_from_md_name(md_name)
        self.print_attrs()


    def insert_text(self, text, pos='end'):
        self.text.insert(pos, text)


    def insert_text_top(self, text):
        if text[-1] != '\n':
            text += '\n'
        self.insert_text(text, pos='1.0')


    def insert_text_end(self, text):
        self.insert_text(text, pos='end')


    def start_new_pres(self, new_title):
        # - open the main md file
        # - insert # title
        # - self flag that main is open
        self.open_main_md_here()
        title_line = '# %s' % new_title
        self.insert_text_top(title_line)
        


    def find_main_files_in_folder(self, folderpath):
        """The new_lecture_title_dialog calls my new_md_beamer_pres.py
        script in a folder.  But the script does not return the new md
        file name.  This function seeks to find the *_slides.md file
        in folderpath, asserting that there is only one match.  It
        then sets all the main files if only one slides file is found."""
        slides_pat = os.path.join(folderpath, "*_slides.md")
        main_md_path = rwkos.find_one_glob(slides_pat)
        self.set_main_folder_and_files(main_md_path)
        

    def guess_main_folder_and_files(self):
        self.classnum = find_current_class_number()
        self.class_dir = find_class_number_dir(self.classnum)
        self.main_md_name = find_main_slides_md(self.classnum)
        self.set_pdf_and_tex_names_from_md_name(self.main_md_name)
        self.print_attrs()


    def get_filename(self, attr):
        # - What is my flag for guessing based on classnum?
        # - how do I know if I need to guess?
        # --> self.classnum is the flag (for now I guess....)
        if self.classnum is None:
            self.guess_main_folder_and_files()
        val = getattr(self, attr)
        return val


    def get_main_md_name(self):
        return self.get_filename('main_md_name')


    def get_main_pdf_name(self):
        return self.get_filename('main_pdf_name')


    def get_main_tex_name(self):
        return self.get_filename('main_tex_name')
    
        
    def __init__(self):
        super().__init__()
        self.option_add('*tearOff', False)
        self.geometry("600x400")
        self.mylabel = 'Tkinter Markdown Slides GUI'
        self.title("MD Beamer Presentation")
        self.resizable(1, 1)

        # configure the grid
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=4)

        self.options = {'padx': 5, 'pady': 5}

        self.menubar = tk.Menu(self)
        self['menu'] = self.menubar
        self.menu_file = tk.Menu(self.menubar)
        self.menu_edit = tk.Menu(self.menubar)
        self.build_menu = tk.Menu(self.menubar)
        
        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_edit, label='Edit')
        self.menubar.add_cascade(menu=self.build_menu, label='Build')        
        self.menu_file.add_command(label='New Lecture', command=self.on_new_lecture_menu)
        self.menu_file.add_command(label='Save', command=self.on_save_menu)
        self.menu_file.add_command(label='Open Current Slide (pdf)', command=self.on_open_current_slide)
        self.menu_file.add_command(label='Open Main Presentation (pdf)', \
                                   command=self.on_open_main_presentation)        
        self.menu_file.add_command(label='Open Main Markdown (Here)', \
                                   command=self.open_main_md_here)        
        self.menu_file.add_command(label='Open Main Markdown (emacs)', \
                                   command=self.open_main_md_in_emacs)
        self.menu_file.add_command(label='Save Main Markdown file', \
                                   command=self.save_main_md_file)
        self.build_menu.add_command(label="Build Current Slide", command=self.build_current_slide)
        self.build_menu.add_command(label="Build Full Presentation", \
                                    command=self.build_full_pres)        


        self.menu_edit.add_command(label="Append Current Text to Main md", \
                                   command=self.append_current_to_main)
        self.menu_edit.add_command(label="Insert Image", \
                                   command=self.insert_image)
        self.menu_edit.add_command(label="Insert Columns", \
                                   command=self.insert_columns)
        self.menu_edit.add_command(label='Run Highlighting', \
                                   command=self.run_highlights)
        
        #self.menu_file.add_command(label='Load', command=self.on_load_menu)        
        #menu_file.add_command(label='Open...', command=openFile)
        self.menu_file.add_command(label='Quit', command=self._quit)
        self.bind('<Control-q>', self._quit)
        self.bind('<Control-s>', self.on_save_menu)
        self.bind('<Control-n>', self.on_new_lecture_menu)
        self.bind('<Control-b>', self.build_current_slide)
        self.bind('<Control-B>', self.build_full_pres)        
        self.bind('<Control-o>', self.on_open_current_slide)
        self.bind('<Control-O>', self.on_open_main_presentation)
        self.bind('<Control-e>', self.open_main_md_in_emacs)
        self.bind('<Control-E>', self.open_main_md_here)
        #self.bind('<Control-E>', self.save_main_md_file)
        self.bind('<Control-a>', self.append_current_to_main)
        self.bind('<Control-i>', self.insert_image)
        
        self.bind('<Control-h>', self.run_highlights)
        #self.bind('<Control-l>', self.on_load_menu)
        
        # configure the root window
        self.make_widgets()
        self.set_highlights()
        #self.set_class_number()
        self.classnum = None
        #self.load_params()



    def set_highlights(self, *args, **kwargs):
        self.text.tag_configure("titles", foreground="blue", font=("Times New Roman bold", 22))


    def run_highlights(self, *args, **kwargs):
        print("running set_highlights")
        self.text.highlight_pattern("^##.*$", "titles", regexp=True)


    ## def load_params(self):
    ##     """Load parameters for the gui from the txt file specified in
    ##     `pybd_gui.params_path`.  The parameters are saved as key:value
    ##     strings."""
    ##     myfile = txt_mixin.txt_file_with_list(self.params_path)
    ##     mylist = myfile.list
    ##     mydict = pybd.break_string_pairs_to_dict(mylist)
    ##     for key, value in mydict.items():
    ##         setattr(self, key, value)

    ##     if 'csv_path' in mydict:
    ##         #load the model from csv
    ##         print("loading: %s" % self.csv_path)
    ##         self.load_model_from_csv(self.csv_path)
    ##         # draw the BD
    ##         self.on_draw_btn()
            

    ## def save_params(self):
    ##     """Save parameters from pybd_gui.param_list to a txt values as
    ##     key:value string pairs."""
    ##     mydict = self.build_save_params_dict()
    ##     my_string_list = dict_to_key_value_strings(mydict)
    ##     txt_mixin.dump(self.params_path, my_string_list)
        
        
    ## def build_save_params_dict(self):
    ##     """Build a dictionary of parameters to save to a txt file so
    ##     that various things in the gui are preserved from session to
    ##     session.  The parameters are listed in pybd_gui.param_list."""
    ##     mydict = {}
    ##     for key in self.param_list:
    ##         if hasattr(self, key):
    ##             value = str(getattr(self, key))
    ##             if value:
    ##                 mydict[key] = value
    ##     return mydict

    def open_main_md_here(self, *args, **kwargs):
        # Approach:
        # - clear self.text
        # - find main md file
        # - read in main file
        # - put md text in self.text
        self.clear_text()
        main_md = self.get_main_md_name()
        f = open(main_md, 'r')
        all_lines = f.read()
        f.close()
        self.text.insert('1.0',all_lines)
        self.run_highlights()
        self.main_md_open = True
        

    def save_main_md_file(self, *args, **kwargs):
        all_text = self.get_current_text()
        main_md = self.get_main_md_name()
        f = open(main_md, 'w')
        f.write(all_text)
        f.close()
        
        

    def open_main_md_in_emacs(self, *args, **kwargs):
        #md_name = find_main_slides_md(self.classnum)
        main_md = self.get_main_md_name()
        cmd = 'emacs %s &' % main_md
        print(cmd)
        os.system(cmd)


    def insert_image(self, *args, **kwargs):
        fname = tk.filedialog.askopenfilename(filetypes=(("image files", "*.jpg;*.jpeg;*.pdf;*.png"), \
                                                         ("pdf files", "*.pdf"), \
                                                         ("jpg files", "*.jpg"), \
                                                         ("png files", "*.png"), \
                                                         ("All files", "*.*") ),\
                                              initialdir=(self.class_dir))
        if fname:
            rp = relpath.relpath(fname, self.class_dir)
            print("rp = %s" % rp)
            figline = '\\myvfig{0.8\\textheight}{%s}' % rp
            cursor = self.get_cursor_position()
            self.text.insert(cursor,figline)


    def get_cursor_position(self, *args, **kwargs):
        cursor = self.text.index(tk.INSERT)
        return cursor

    def insert_columns(self, *args, **kwargs):
        cursor = self.get_cursor_position()
        print("cursor = %s" % cursor)
        self.text.insert(cursor, columns_str)
        

    def append_current_to_main(self, *args, **kwargs):
        # - get current text
        # - append it to the main md file
        #     - will need to get the main md file name
        # - save the main slides md file
        # - clear text widget
        all_text = self.get_current_text()
        md_path = find_main_slides_md(self.classnum)
        # check the newline situation in the existing main md content
        f0 = open(md_path, 'r')
        instr = f0.read()
        f0.close()

        f1 = open(md_path, 'a')
        n = 0
        if len(instr) > 2:
            if instr [-1] != '\n':
                n = 2
            elif instr[-2] != '\n':
                n = 1

            if n > 0:
                f1.write('\n'*n)

        # append new text
        f1.write(all_text)
        f1.close()

        # clear the text widget
        self.clear_text()


    def clear_text(self, *args, **kwargs):
        self.text.delete('1.0', 'end')
        

    def on_open_current_slide(self, *args, **kwargs):
        pdfname = "current_slide_main.pdf"
        cmd = "skim %s &" % pdfname
        print(cmd)
        os.system(cmd)

        
    def on_open_main_presentation(self, *args, **kwargs):
        pdfname = find_main_pdf(self.classnum)
        cmd = "skim %s &" % pdfname
        print(cmd)
        os.system(cmd)


    def get_current_text(self):
        all_text = self.text.get("1.0","end")
        return all_text


    def build_full_pres(self, *args, **kwargs):
        # save if open:
        if self.main_md_open:
            self.save_main_md_file()
        md_name = self.get_main_md_name()
        #md_name = find_main_slides_md(self.classnum)
        # build current slide
        cmd = "md_to_beamer_pres.py %s" % md_name
        print(cmd)
        os.system(cmd)
        

    def build_current_slide(self, *args, **kwargs):
        # - copy template files for md and tex if needed
        # - write text connect to md file
        # - call script that builds slide
        main_name = "current_slide_main.tex"
        slides_fno = "current_slide_slides"
        slides_md_name = slides_fno + ".md"
        slides_tex_name = slides_fno + ".tex"

        # template file stuff
        if not os.path.exists(main_name):
            repo_root = os.path.expanduser("~/git/report_generation/")
            template_fn = "pandoc_beamer_main_no_title_template.tex"
            template_path = os.path.join(repo_root, template_fn)
            f = open(template_path,'r')
            in_str = f.read()
            f.close()

            out_str = in_str.replace("%%%TITLE%%%", self.pres_title)
            out_str = out_str.replace("%%%SLIDEFILENAME.TEX%%%", slides_tex_name)

            f2 = open(main_name, 'w')
            f2.write(out_str)
            f2.close()


        # write text editor content to md file
        all_text = self.get_current_text()
        f3 = open(slides_md_name, 'w')
        f3.write(all_text)
        f3.close()

            
        # build current slide
        cmd = "md_to_beamer_pres.py %s" % slides_md_name
        print(cmd)
        os.system(cmd)




    def set_pres_title(self, mytitle):
        self.pres_title = mytitle


    def on_new_lecture_menu(self, *args, **kwargs):
        print("in on_new_lecture_menu")
        new_class_num = find_new_class_number()
        mydialog = new_lecture_title_dialog(parent=self, classnum=new_class_num, \
                                            class_prep_root=class_prep_root)
        mydialog.grab_set()


## ############################
##     def key_pressed(self, event):
##         print("pressed:")
##         print(repr(event.char))
##         print("keycode:")
##         print(event.keycode)
##         print("keysym:")
##         print(event.keysym)
##         print("keysym_num:")
##         print(event.keysym_num)


    def on_save_menu(self, *args, **kwargs):
        print("in menu save")
        self.save_main_md_file()
        ## if hasattr(self, 'csv_path'):
        ##     self.bd.save_model_to_csv(self.csv_path)
        ## else:
        ##     self.on_save_as_menu()


    def _quit(self, *args, **kwargs):
        print("in _quit")
        ##self.save_params()
        self.quit()     # stops mainloop
        self.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate


    def make_widgets(self):
        # don't assume that self.parent is a root window.
        # instead, call `winfo_toplevel to get the root window
        #self.winfo_toplevel().title("Simple Prog")
        #self.wm_title("Python Block Diagram GUI")        


        # column 0
        self.label = ttk.Label(self, text=self.mylabel)
        self.label.grid(row=0,column=0,sticky='NW', **self.options)

        #self.text = tk.Text(self, width=40, height=10, font=("Times New Roman", 18))
        self.text = CustomText(self, width=40, height=10, font=("Times New Roman", 18))
        self.text.grid(row=1,column=0,sticky='NEWS', **self.options)
        #self.big_button = ttk.Button(self, text='Big Button')
        #self.big_button.grid(row=1,column=0,sticky='news',**self.options)
        self.button_frame1 = ttk.Frame(self)
        self.quit_button = ttk.Button(self.button_frame1, text="Quit", width=mywidth, \
                                      command=self._quit)
        self.quit_button.grid(column=0, row=0,  **self.options)

        ## self.xlim_label = ttk.Label(self.button_frame1, text="xlim:")
        ## self.xlim.grid(row=0,column=2,sticky='E')
        ## self.xlim_var = tk.StringVar()
        ## self.xlim_box = ttk.Entry(self.button_frame1, textvariable=self.xlim_var)
        ## self.xlim_box.grid(column=3, row=0, sticky="W", padx=(0,5))

        
        self.button_frame1.grid(row=20, column=0)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # configure the root window
        self.title('My Awesome App')
        self.geometry('900x600')
        #self.columnconfigure(0, weight=3)
        #self.columnconfigure(1, weight=1)
        #self.rowconfigure(1, weight=3)
        #self.grid_columnconfigure(0, weight=3)

if __name__ == "__main__":
    app = md_gui()
    app.mainloop()
