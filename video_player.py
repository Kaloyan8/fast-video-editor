import tkinter as tk
from tkinter import filedialog
import os

class VideoPlayerApp:
    def __init__(self, master):
        self.master = master
        master.title("Video Player")

        # Create button to select video file
        self.select_button = tk.Button(master, text="Select Video", command=self.select_file)
        self.select_button.pack()

    def select_file(self):
        # Open file dialog to select video file
        video_file = filedialog.askopenfilename()

        # If a file was selected, play it using FFmpeg
        if video_file:
            os.system(f'ffplay -fs -window_title "Video Player" -autoexit "{video_file}"')

            # Minimize the window
            self.master.wm_state('iconic')

# Create Tkinter window and run main loop
root = tk.Tk()
app = VideoPlayerApp(root)
root.mainloop()


