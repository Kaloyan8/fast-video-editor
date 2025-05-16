#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fast Video Editor

A lightweight, high-speed video editing GUI leveraging FFmpeg directly for trimming,
merging, duplicating, audio patching, image sequences, and fade effects.

"""
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import customtkinter as ctk
import sys
from PIL import Image
import os
import tempfile

if sys.platform.startswith("win"):
    os.add_dll_directory(r"C:\Program Files\VideoLAN\VLC")
import vlc

try:
    import vlc
    _has_vlc = True
except (ImportError, FileNotFoundError):
    _has_vlc = False

# UI setup
ctk.set_appearance_mode("Dark")
ws = ctk.CTk()
ws.geometry('600x480')
ws.title("Fast Video Editor")


def run_ffmpeg(cmd, progress=None):
    subprocess.run(cmd, check=True)
    if progress:
        progress.stop()
        progress.destroy()


def format_time(sec):
    """Convert seconds to MM:SS"""
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"



def trim_video():
    path = filedialog.askopenfilename(
        title="Select Media to Trim",
        filetypes=[("Media files", "*.mp4;*.mkv;*.avi;*.mp3;*.wav;*.m4a")]
    )
    if not path:
        return
    try:
        dur = float(subprocess.check_output([
            'ffprobe','-v','error',
            '-show_entries','format=duration',
            '-of','default=noprint_wrappers=1:nokey=1', path
        ]))
    except subprocess.CalledProcessError:
        return messagebox.showerror("Error", "Could not read media duration.")

    win = tk.Toplevel(ws)
    win.title("Trim & Preview")

    start = tk.DoubleVar(value=0.0)
    end   = tk.DoubleVar(value=dur)

    if _has_vlc:
        vlc_inst = vlc.Instance()
        player   = vlc_inst.media_player_new()
        player.set_media(vlc_inst.media_new(path))

        vid_frame = tk.Frame(win, bg='black', width=1080, height=720)
        vid_frame.grid(row=0, column=0, columnspan=4, pady=(10,0), padx=10)
        win.update_idletasks()

        if sys.platform.startswith('linux'):
            player.set_xwindow(vid_frame.winfo_id())
        elif sys.platform == 'win32':
            player.set_hwnd(vid_frame.winfo_id())
        else:
            player.set_nsobject(vid_frame.winfo_id())

        ttk.Button(win, text="▶ Play",  command=player.play).grid(row=1, column=0)
        ttk.Button(win, text="⏸ Pause", command=player.pause).grid(row=1, column=1)
    else:
        ttk.Label(win, text="Preview unavailable (install VLC)").grid(
            row=0, column=0, columnspan=4, pady=20)

    def fmt(t):
        m = int(t // 60)
        s = int(t % 60)
        return f"{m:02d}:{s:02d}"

    frm = ttk.Frame(win)
    frm.grid(row=2, column=0, columnspan=4, padx=10, pady=10)

    # Start
    ttk.Label(frm, text="Start:").grid(row=0, column=0, sticky='e')
    slab = ttk.Label(frm, text=fmt(0))
    slab.grid(row=0, column=1, sticky='w')
    sscale = ttk.Scale(frm, from_=0, to=dur, variable=start, length=300)
    sscale.grid(row=1, column=0, columnspan=4)
    if _has_vlc:
        start.trace_add('write', lambda *a: (
            slab.config(text=fmt(start.get())),
            player.set_time(int(start.get() * 1000))
        ))
    else:
        start.trace_add('write', lambda *a: slab.config(text=fmt(start.get())))


    ttk.Label(frm, text="End:").grid(row=2, column=0, sticky='e')
    elab = ttk.Label(frm, text=fmt(dur))
    elab.grid(row=2, column=1, sticky='w')
    escale = ttk.Scale(frm, from_=0, to=dur, variable=end, length=300)
    escale.set(dur)
    escale.grid(row=3, column=0, columnspan=4)
    if _has_vlc:
        end.trace_add('write', lambda *a: (
            elab.config(text=fmt(end.get())),
            player.set_time(int(end.get() * 1000))
        ))
    else:
        end.trace_add('write', lambda *a: elab.config(text=fmt(end.get())))


    cur = {'var': None}
    for slider, var in ((sscale, start), (escale, end)):
        slider.bind('<Button-1>', lambda e, v=var: cur.update(var=v))
    def dec(e):
        v = cur.get('var')
        if v: v.set(max(0, v.get() - 1))
    def inc(e):
        v = cur.get('var')
        if v: v.set(min(dur, v.get() + 1))
    for key in ('<Left>','<Down>'):
        win.bind(key, dec)
    for key in ('<Right>','<Up>'):
        win.bind(key, inc)

    ttk.Label(frm, text="Output name:").grid(row=4, column=0, sticky='e')
    out_ent = ttk.Entry(frm, width=30)
    out_ent.grid(row=4, column=1, columnspan=3, sticky='w')


    def do_trim():
        raw = out_ent.get().strip()
        if not raw:
            return messagebox.showwarning("No Output", "Specify a filename.")


        outp = raw if os.path.isabs(raw) else os.path.join(os.path.dirname(path), raw)
        ext = os.path.splitext(outp)[1].lower()

        s = start.get()
        e = end.get()
        if e <= s:
            return messagebox.showerror("Invalid Range", "End must be after Start.")
        length = e - s

        cmd = ['ffmpeg','-y','-ss',f"{s:.3f}",'-i',path,'-t',f"{length:.3f}"]

        if ext in ('.wav','.mp3','.m4a'):
            cmd.append('-vn')
            if ext == '.wav':
                cmd += ['-c:a','pcm_s16le']
            elif ext == '.mp3':
                cmd += ['-c:a','libmp3lame','-b:a','192k']
            else:  
                cmd += ['-c:a','aac','-b:a','192k']

        else:
            cmd += [
                '-c:v','libx264','-preset','ultrafast',
                '-c:a','aac','-b:a','192k',
                '-movflags','+faststart'
            ]

        cmd.append(outp)

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as err:
            return messagebox.showerror("Error", f"ffmpeg failed:\n{err}")


        win.destroy()
        messagebox.showinfo("Done", f"Trim complete:\n{outp}")


    ttk.Button(frm, text="Trim", command=do_trim).grid(row=5, column=0, columnspan=4, pady=10)


trim_btn = ctk.CTkButton(ws, text="Trim Video", command=trim_video)
trim_btn.pack(pady=10)


def merge_videos():

    files = filedialog.askopenfilenames(
        title="Select media to merge",
        filetypes=[("Media files",
            "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;"
            "*.mp3;*.wav;*.m4a;*.aac;*.flac;*.ogg")]
    )
    if not files:
        return

    first_ext = os.path.splitext(files[0])[1].lower()
    output = filedialog.asksaveasfilename(
        defaultextension=first_ext,
        filetypes=[("Media files",
            "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;"
            "*.mp3;*.wav;*.m4a;*.aac;*.flac;*.ogg")]
    )
    if not output:
        return

    files = list(files)
    out_ext = os.path.splitext(output)[1].lower()
    AUDIO_EXTS = ('.wav', '.mp3', '.m4a', '.aac', '.flac', '.ogg')

    progress = ttk.Progressbar(ws, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()

    def _do_merge():
        try:
            if all(os.path.splitext(f)[1].lower() in AUDIO_EXTS for f in files) \
               and out_ext in AUDIO_EXTS:
                normed = []
                for f in files:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                    tmp.close()
                    subprocess.run([
                        'ffmpeg', '-y', '-i', f,
                        '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s16le',
                        tmp.name
                    ], check=True)
                    normed.append(tmp.name)

                list_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
                list_file.close()
                with open(list_file.name, 'w') as L:
                    for nf in normed:
                        L.write(f"file '{nf}'\n")

                subprocess.run([
                    'ffmpeg', '-y',
                    '-protocol_whitelist', 'file,pipe',
                    '-f', 'concat', '-safe', '0', '-i', list_file.name,
                    '-c', 'copy', output
                ], check=True)

                for nf in normed:
                    os.remove(nf)
                os.remove(list_file.name)

            else:
                list_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
                list_file.close()
                with open(list_file.name, 'w') as L:
                    for f in files:
                        L.write(f"file '%s'\n" % f)


                subprocess.run([
                    'ffmpeg', '-y',
                    '-protocol_whitelist', 'file,pipe',
                    '-f', 'concat', '-safe', '0', '-i', list_file.name,
                    '-c', 'copy', output
                ], check=True)

                os.remove(list_file.name)

        except subprocess.CalledProcessError as e:
            ws.after(0, lambda: messagebox.showerror(
                "Merge Failed", f"FFmpeg error:\n{e}"
            ))
        else:
            ws.after(0, lambda: messagebox.showinfo(
                "Done", f"Merged into:\n{output}"
            ))
        finally:
            ws.after(0, lambda: (progress.stop(), progress.destroy()))

    threading.Thread(target=_do_merge, daemon=True).start()

merge_btn = ctk.CTkButton(ws, text="Merge Videos", command=merge_videos)
merge_btn.pack(pady=10)



def duplicate_video():
    file = filedialog.askopenfilename(
        title="Select Video",
        filetypes=[("Media files",
            "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;"
            "*.mp3;*.wav;*.m4a;*.aac;*.flac;*.ogg")]
    )
    if not file:
        return

    N = simpledialog.askinteger(
        "Duplicates", "Number of copies:",
        parent=ws, minvalue=1
    )
    if not N:
        return

    output = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("Media files",
            "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;"
            "*.mp3;*.wav;*.m4a;*.aac;*.flac;*.ogg")]
    )
    if not output:
        return

    cmd = [
        'ffmpeg', '-y',
        '-stream_loop', str(N-1),
        '-i', file,
        '-c', 'copy',
        output
    ]
    run_ffmpeg(cmd)
    messagebox.showinfo("Done", f"Duplicated {N}× into {output}")

dup_btn = ctk.CTkButton(ws, text="Duplicate Video", command=duplicate_video)
dup_btn.pack(pady=10)


import subprocess
import threading
from tkinter import filedialog, messagebox, ttk

def patch_sound():
    video = filedialog.askopenfilename(
        title="Select video",
        filetypes=[("Videos", "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv")]
    )
    if not video:
        return
    audio = filedialog.askopenfilename(
        title="Select audio",
        filetypes=[("Audio", "*.mp3;*.wav;*.m4a;*.aac;*.flac;*.ogg")]
    )
    if not audio:
        return
    output = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not output:
        return
    try:
        adur = float(subprocess.check_output([
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio
        ]).strip())
    except subprocess.CalledProcessError:
        return messagebox.showerror("Error", "Could not probe audio duration.")

    progress = ttk.Progressbar(ws, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()

    def _do_patch():
        # Loop video indefinitely; then trim output to audio length
        cmd = [
            'ffmpeg', '-y',
            '-stream_loop', '-1',
            '-i', video,
            '-i', audio,
            '-c:v', 'copy',
            '-c:a', 'aac', '-b:a', '192k',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-t', f"{adur:.3f}",
            output
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            ws.after(0, lambda: messagebox.showerror("Error", f"FFmpeg failed:\n{e}"))
        else:
            ws.after(0, lambda: messagebox.showinfo("Done", f"Output saved to:\n{output}"))
        finally:
            ws.after(0, lambda: (progress.stop(), progress.destroy()))

    threading.Thread(target=_do_patch, daemon=True).start()

patch_btn = ctk.CTkButton(ws, text="Patch Sound", command=patch_sound)
patch_btn.pack(pady=10)



def create_image_sequence_video():
    files = filedialog.askopenfilenames(
        title="Select images",
        filetypes=[("Images", "*.jpg;*.png")]
    )
    if not files:
        return

    output = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not output:
        return

    dur = simpledialog.askfloat(
        "Duration", "Seconds per image:",
        parent=ws, minvalue=0.1
    )
    if dur is None:
        return
    
    sizes = [Image.open(f).size for f in files]
    W = max(w for w, h in sizes)
    H = max(h for w, h in sizes)


    list_txt = ""
    for f in files:
        list_txt += f"file '{f}'\nduration {dur}\n"
    list_txt += f"file '{files[-1]}'\n"


    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease," \
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2"
    )

    progress = ttk.Progressbar(ws, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()

    def do_seq():
        subprocess.run([
            'ffmpeg', '-y',
            '-protocol_whitelist', 'file,pipe',
            '-f', 'concat', '-safe', '0', '-i', '-',
            '-vf', vf,
            '-c:v', 'libx264',
            '-r', '24',
            '-preset', 'ultrafast',
            output
        ], input=list_txt.encode(), check=True)
        ws.after(0, lambda: (progress.stop(), progress.destroy(),
                             messagebox.showinfo("Done", "Sequence created")))

    threading.Thread(target=do_seq).start()

seq_btn = ctk.CTkButton(ws, text="Image Sequence Video", command=create_image_sequence_video)
seq_btn.pack(pady=10)



def fade_in_video():
    file = filedialog.askopenfilename(
        title="Select video",
        filetypes=[("Videos", "*.mp4;*.mkv;*.avi")]
    )
    if not file:
        return

    output = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not output:
        return

    d = simpledialog.askfloat(
        "Fade In", "Duration (s):", parent=ws, minvalue=0.1
    )
    if d is None:
        return

    cmd = [
        'ffmpeg', '-y',
        '-i', file,
        '-vf', f'fade=t=in:st=0:d={d}',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-c:a', 'copy',
        output
    ]
    run_ffmpeg(cmd)
    messagebox.showinfo("Done", "Fade-in applied")

fadein_btn = ctk.CTkButton(ws, text="Fade In", command=fade_in_video)
fadein_btn.pack(pady=10)


def fade_out_video():
    file = filedialog.askopenfilename(
        title="Select video",
        filetypes=[("Videos", "*.mp4;*.mkv;*.avi")]
    )
    if not file:
        return

    output = filedialog.asksaveasfilename(
        defaultextension=".mp4",
        filetypes=[("MP4 files", "*.mp4")]
    )
    if not output:
        return


    dur = float(subprocess.check_output([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file
    ]))

    d = simpledialog.askfloat(
        "Fade Out", "Duration (s):", parent=ws, minvalue=0.1
    )
    if d is None:
        return

    start = max(0, dur - d)
    cmd = [
        'ffmpeg', '-y',
        '-i', file,
        '-vf', f'fade=t=out:st={start}:d={d}',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-c:a', 'copy',
        output
    ]
    run_ffmpeg(cmd)
    messagebox.showinfo("Done", "Fade-out applied")

fadeout_btn = ctk.CTkButton(ws, text="Fade Out", command=fade_out_video)
fadeout_btn.pack(pady=10)

from tkinter import simpledialog, filedialog, messagebox, ttk
import threading, subprocess, os, customtkinter as ctk

# Supported formats
AUDIO_EXTS = ('wav','mp3','m4a','flac','aac','ogg')
VIDEO_EXTS = ('mp4','mkv','avi','mov','webm','flv')

def convert_media():

    src = filedialog.askopenfilename(
        title="Select media to convert",
        filetypes=[("All media", "*.mp4;*.mkv;*.avi;*.mov;*.webm;*.flv;*.mp3;*.wav;*.m4a;*.aac;*.ogg;*.flac")]
    )
    if not src:
        return


    fmt = simpledialog.askstring(
        "Target Format",
        f"Enter desired extension ({', '.join(AUDIO_EXTS + VIDEO_EXTS)}):",
        parent=ws
    )
    if not fmt:
        return
    fmt = fmt.lower().lstrip('.')
    if fmt not in AUDIO_EXTS + VIDEO_EXTS:
        return messagebox.showwarning("Invalid Format", f"Choose one of: {', '.join(AUDIO_EXTS + VIDEO_EXTS)}")


    base = os.path.splitext(os.path.basename(src))[0]
    kind = "audio" if fmt in AUDIO_EXTS else "video"
    initial = f"{base}_converted.{fmt}"
    out = filedialog.asksaveasfilename(
        title=f"Save {kind} as",
        defaultextension=f".{fmt}",
        initialfile=initial,
        filetypes=[(f"{fmt.upper()} files", f"*.{fmt}")]
    )
    if not out:
        return

    cmd = ['ffmpeg', '-y', '-i', src]

    # If converting to an audio format, strip video
    if fmt in AUDIO_EXTS:
        cmd.append('-vn')
        # audio codec choices
        if fmt == 'wav':
            cmd += ['-c:a','pcm_s16le']
        elif fmt == 'mp3':
            cmd += ['-c:a','libmp3lame','-b:a','192k']
        elif fmt in ('m4a','aac'):
            cmd += ['-c:a','aac','-b:a','192k']
        elif fmt == 'flac':
            cmd += ['-c:a','flac']
        elif fmt == 'ogg':
            cmd += ['-c:a','libvorbis','-qscale:a','5']
    else:
        # Video container: keep video + audio
        if fmt == 'mp4' or fmt == 'mov':
            cmd += ['-c:v','libx264','-preset','ultrafast','-c:a','aac','-b:a','192k']
        elif fmt == 'mkv':
            cmd += ['-c:v','libx264','-preset','ultrafast','-c:a','copy']
        elif fmt == 'avi':
            cmd += ['-c:v','mpeg4','-qscale:v','5','-c:a','libmp3lame','-b:a','192k']
        elif fmt == 'webm':
            cmd += ['-c:v','libvpx','-b:v','1M','-c:a','libvorbis','-qscale:a','5']
        elif fmt == 'flv':
            cmd += ['-c:v','flv','-c:a','aac','-b:a','128k']

    cmd.append(out)


    progress = ttk.Progressbar(ws, mode='indeterminate')
    progress.pack(pady=10)
    progress.start()

    def _worker():
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            ws.after(0, lambda: messagebox.showerror("Conversion Failed", f"FFmpeg error:\n{e}"))
        else:
            ws.after(0, lambda: messagebox.showinfo("Done", f"Saved to {out}"))
        finally:
            ws.after(0, lambda: (progress.stop(), progress.destroy()))

    threading.Thread(target=_worker, daemon=True).start()


conv_media_btn = ctk.CTkButton(ws, text="Convert Media", command=convert_media)
conv_media_btn.pack(pady=10)

ws.mainloop()
