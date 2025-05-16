# fast-video-editor

Introducing a simple but powerful video editing program.

Top Features:

Drop MoviePy and temp files; add run_ffmpeg helper

In-memory concat (-f concat -i -) and -stream_loop for duplication

GPU-friendly preset; ultrafast and hardware codecs - wait times reduced to a minimum

Auto-detect canvas size; pad for image sequences; consistent image size

Unified audio and video patching defaulted to audio duration

Trim Video function revamped: vlc player incorporated in menu, easier editing and cutting selection.

Added file conversion option if dealing with different formats

Tools available at the moment:
- merge/duplicate videos into one
- cut videos
- create image sequence videos easily 
- fade in & fade out video
- add sound to video
- File conversion (if dealing with different formats)

# Installation and usage instructions 
1. Python and FFmpeg must be installed.
2. Run in the terminal # pip install -r requirements.txt 
3. Run video_Latest_GUI.py
NB: Program runs on Windows, but is easily adaptable to other operating systems (you might need to change the sys.platform check for vlc)
