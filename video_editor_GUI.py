#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 17 13:36:45 2022

@author: koko
"""
from moviepy.editor import VideoFileClip
from moviepy.editor import ImageClip
from tkinter import Spinbox
import subprocess
import tkinter as tk
from tkinter import filedialog
from moviepy.editor import *
import moviepy.editor as mp
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename
import os
import glob
import threading
from tkinter.messagebox import showinfo
import customtkinter #use this module to improve the design
import moviepy.editor as mp


ws = customtkinter.CTk()
ws.geometry('600x480')
customtkinter.set_appearance_mode("Dark") # Other: "Light", "System" (only macOS)

# Create a notebook that holds the tabs


# Place widgets in tab1



def trim_video():
    # Prompt the user to select a file
    file_path = filedialog.askopenfilename()

    # Use FFprobe to get the duration of the video
    ffprobe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', file_path]
    duration = float(subprocess.check_output(ffprobe_cmd))

    # Create a new window to get the start and end times for the trim
    trim_window = tk.Toplevel()
    trim_window.title("Trim Video")

    # Add a label for the start time
    start_label = tk.Label(trim_window, text="Start time (mm:ss)")
    start_label.pack()

    # Add a label for the end time
    end_label = tk.Label(trim_window, text="End time (mm:ss)")
    end_label.pack()

    # Add a label and entry field for the output file name
    output_label = tk.Label(trim_window, text="Output file name")
    output_label.pack()
    output_entry = tk.Entry(trim_window)
    output_entry.pack()

    # Add a slider for the start time
    start_slider = tk.Scale(trim_window, from_=0, to=duration, orient=tk.HORIZONTAL, resolution=1, length=400, label="Start Time")
    start_slider.pack()

    # Add a slider for the end time
    end_slider = tk.Scale(trim_window, from_=0, to=duration, orient=tk.HORIZONTAL, resolution=1, length=400, label="End Time")
    end_slider.pack()

    # Add a "Trim" button
    def trim():
        start_time = int(start_slider.get())
        end_time = int(end_slider.get())
        duration = end_time - start_time
        output_file = output_entry.get()

        # Use FFmpeg to trim the video
        subprocess.run(['ffmpeg', '-i', file_path, '-ss', str(start_time), '-t', str(duration), '-c:v', 'copy', '-c:a', 'copy', output_file])

        # Destroy the trim window
        trim_window.destroy()

    trim_button = tk.Button(trim_window, text="Trim", command=trim)
    trim_button.pack()

    # Start the main event loop for the trim window
    trim_window.mainloop()
  

Button(text="Cut Video", command=trim_video).pack(pady=20, padx=20)



def merge_videos():
    files = filedialog.askopenfilenames(title="Select videos to merge", filetypes=[("Video files", "*.mp4;*.mkv;*.avi")])
    if not files:
        return

    output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
    if not output_file:
        return

    # Create a progress bar
    progress = ttk.Progressbar(mode="indeterminate")
    progress.pack()
    progress.start()

    list_file_path = os.path.join(os.getcwd(),"list.txt")

    def run_ffmpeg(files):
        nonlocal output_file
        nonlocal list_file_path
        files = sorted(files)
        list_file = open(list_file_path, "w")
        for file in files:
            list_file.write("file '" + file + "'\n")
        list_file.close()
        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", list_file_path, "-c", "copy", output_file])
    thread = threading.Thread(target=run_ffmpeg, args=(files,))
    thread.start()


    while thread.is_alive():
        ws.update()
    
        
    def check_thread():
        if thread.is_alive():
            ws.after(100, check_thread)
        else:
            progress.stop()
            progress.destroy()
            showinfo("Merging complete", "The video files have been merged successfully.")

    check_thread()

merge_button = tk.Button(text="Merge Videos", command=merge_videos)
merge_button.pack()



def patch_sound():
    # Prompt the user to select the video file
    video_path = filedialog.askopenfilename(title="Select video file", filetypes=[("Video files", "*.mp4;*.mkv;*.avi")])
    if not video_path:
        return

    # Prompt the user to select the audio file
    audio_path = filedialog.askopenfilename(title="Select audio file", filetypes=[("Audio files", "*.mp3;*.wav")])
    if not audio_path:
        return
    
    # Prompt the user to enter the output file name and location
    output_path = filedialog.asksaveasfilename(title="Save merged file as", filetypes=[("Video files", "*.mp4;*.mkv;*.avi")])
    if not output_path:
        return

    # Get the duration of the video and audio streams
    video_duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]))
    audio_duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]))

    # Set the duration of the output file to the shortest input stream
    duration = min(video_duration, audio_duration)

    # Merge the video and audio files with ffmpeg
    subprocess.run(["ffmpeg", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-t", str(duration), output_path])

    # Show a message box when the process is complete
    showinfo("Merge Complete", "The audio has been merged with the video.")


Button(ws, text="Patch Sound (for videos)", command=patch_sound).pack(pady=20, padx=20)


def patch_sound2():
    # Prompt the user to select the video file
    video_path = filedialog.askopenfilename(title="Select video file", filetypes=[("Video files", "*.mp4;*.mkv;*.avi")])
    if not video_path:
        return

    # Prompt the user to select the audio file
    audio_path = filedialog.askopenfilename(title="Select audio file", filetypes=[("Audio files", "*.mp3;*.wav")])
    if not audio_path:
        return
    
    # Prompt the user to enter the output file name and location
    output_path = filedialog.asksaveasfilename(title="Save merged file as", filetypes=[("Video files", "*.mp4;*.mkv;*.avi")])
    if not output_path:
        return

    # Merge the video and audio files with ffmpeg
    subprocess.run(["ffmpeg", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", output_path])



Button(text="Patch Sound (for image sequence)", command=patch_sound2).pack(pady=20, padx=20)


def create_image_sequence_video():
    # Prompt user to select image files
    filetypes = (("JPEG files", "*.jpg"), ("PNG files", "*.png"))
    files = filedialog.askopenfilenames(title="Select image files", filetypes=filetypes)

    if not files:
        return

    # Prompt user to select output file name
    output_file = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")])
    if not output_file:
        return

    # Prompt user to select the duration of each image
    duration_window = tk.Toplevel()
    duration_window.title("Image Duration")
    duration_label = tk.Label(duration_window, text="Duration (in seconds)")
    duration_label.pack()
    duration_spinbox = tk.Spinbox(duration_window, from_=1, to=60, increment=1)
    duration_spinbox.pack()

    def create_video():
        duration = float(duration_spinbox.get())
        clips = [ImageClip(file).set_duration(duration) for file in files]
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(output_file, fps=24)

        duration_window.destroy()

    duration_button = tk.Button(duration_window, text="Create Video", command=create_video)
    duration_button.pack()

    
    
    
Button(ws, text="Create Image Sequence Video", command=create_image_sequence_video).pack(pady=20, padx=20)





def fade_in_video():
    # Prompt the user to select a file
    file_path = filedialog.askopenfilename()

    # Create a new window to get the output file name
    fade_in_window = tk.Toplevel()
    fade_in_window.title("Fade In Video")
    output_label = tk.Label(fade_in_window, text="Output file name")
    output_label.pack()
    output_entry = tk.Entry(fade_in_window)
    output_entry.pack()

    def fade_in():
        output_file = output_entry.get()
        # Open the video file
        clip = VideoFileClip(file_path)
        # Create a new subclip that starts at 2 seconds and has the same duration as the original video
        subclip = clip.subclip(2)
        # Apply the fade in effect on the audio
        audio = clip.audio.audio_fadein(2)
        # Set the audio of the subclip to the audio of the original clip with the fade effect applied
        subclip = subclip.set_audio(audio)

        # Use ffmpeg to copy the video, audio, and subtitles to the new file
        subprocess.run(["ffmpeg", "-i", file_path, '-vf', "fade=in:0:30", '-c:a', 'copy', output_file])






        fade_in_window.destroy()
        
    fade_in_button = tk.Button(fade_in_window, text="Fade In", command=fade_in)
    fade_in_button.pack()




def fade_out_video():
    # Prompt the user to select a file
    file_path = filedialog.askopenfilename()

    # Create a new window to get the output file name
    fade_out_window = tk.Toplevel()
    fade_out_window.title("Fade Out Video")
    output_label = tk.Label(fade_out_window, text="Output file name")
    output_label.pack()
    output_entry = tk.Entry(fade_out_window)
    output_entry.pack()

    def fade_out():
        output_file = output_entry.get()
        # Use FFmpeg to add fade out effect
        subprocess.run(['ffmpeg', '-i', file_path, '-af', 'afade=out:st=8:d=2', '-c:v', 'copy', '-c:a', 'copy', output_file])
        fade_out_window.destroy()

    fade_out_button = tk.Button(fade_out_window, text="Fade Out", command=fade_out)
    fade_out_button.pack()
    
    
Button(text="Fade In", command=fade_in_video).pack(pady=20, padx=20)
Button(text="Fade Out", command=fade_out_video).pack(pady=20, padx=20)








 
# Create label
#l = Label(tab2, text = "Select Videos")
#l.config(font =("Courier", 14))
 
"""Fact = A man can be arrested in
Italy or elsewhere for wearing a skirt in public."""
 
# Create button for next text.
#b1 = Button(tab2, text = "Open",
#            command = open_file)
 
# Create an Exit button.
#b2 = Button(tab2, text = "Save",
#            command = save_file
ws.mainloop() 
