import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
from tkinter import Listbox
from pytube import Search
import yt_dlp
import vlc
import threading

# Store video details in a dictionary
video_details = {}
current_player = None
current_index = None

def search_videos():
    query = search_entry.get()
    search_results = Search(query).results
    video_list.delete(0, tk.END)
    for video in search_results:
        title = video.title
        url = video.watch_url
        video_details[title] = url
        video_list.insert(tk.END, title)

def add_to_playlist():
    selected_video = video_list.get(video_list.curselection())
    video_url = video_details[selected_video]
    playlist.append(video_url)
    playlist_listbox.insert(tk.END, selected_video)
    # Clear search entry for the next search
    search_entry.delete(0, tk.END)

def clear_searches():
    search_entry.delete(0, tk.END)
    video_list.delete(0, tk.END)

def update_time_label():
    if current_player and current_player.is_playing():
        current_time = current_player.get_time() // 1000  # Current time in seconds
        duration = current_player.get_length() // 1000    # Total duration in seconds

        current_min, current_sec = divmod(current_time, 60)
        duration_min, duration_sec = divmod(duration, 60)

        time_str = f"{current_min:02}:{current_sec:02} / {duration_min:02}:{duration_sec:02}"
        time_label.config(text=time_str)
        
        # Schedule the next update
        root.after(1000, update_time_label)
    else:
        time_label.config(text="00:00 / 00:00")

def play_next_in_playlist():
    global current_player, current_index
    if playlist:
        if current_index is not None:
            # Remove highlight from the previous song
            playlist_listbox.itemconfig(current_index, bg="white")
        video_url = playlist[0]
        current_index = 0
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(video_url, download=False)
                play_url = info_dict['url']
                # Using VLC to stream audio
                current_player = vlc.MediaPlayer(play_url)
                current_player.play()
                # Highlight the currently playing song
                playlist_listbox.itemconfig(current_index, bg="light green")
                
                def on_end(event):
                    playlist.pop(0)
                    playlist_listbox.delete(0)
                    play_next_in_playlist()

                event_manager = current_player.event_manager()
                event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, on_end)

                # Start updating the time label
                root.after(1000, update_time_label)
        except Exception as e:
            print(f"Error playing {video_url}: {e}")
            playlist.pop(0)
            playlist_listbox.delete(0)
            play_next_in_playlist()  # Try the next video if there is an error

def start_playlist():
    play_next_in_playlist()

def clear_playlist():
    global current_player, current_index
    playlist.clear()
    playlist_listbox.delete(0, tk.END)
    if current_player:
        current_player.stop()
    current_index = None

def remove_selected():
    global current_player, current_index
    selected_index = playlist_listbox.curselection()
    if selected_index:
        selected_index = selected_index[0]
        if selected_index == current_index and current_player:
            current_player.stop()
            playlist.pop(selected_index)
            playlist_listbox.delete(selected_index)
            current_index = None
            play_next_in_playlist()
        else:
            if selected_index < current_index:
                current_index -= 1
            del playlist[selected_index]
            playlist_listbox.delete(selected_index)

def save_playlist():
    playlist_name = simpledialog.askstring("Save Playlist", "Enter playlist name:")
    if playlist_name:
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=f"{playlist_name}.txt")
        if filepath:
            with open(filepath, 'w') as file:
                for url in playlist:
                    file.write(url + '\n')

def load_playlist():
    global current_player, current_index
    filepath = filedialog.askopenfilename(defaultextension=".txt")
    if filepath:
        # Clear current playlist and stop any playing stream
        clear_playlist()
        with open(filepath, 'r') as file:
            urls = file.readlines()
        for url in urls:
            url = url.strip()
            playlist.append(url)
            # Find the title of the video from the URL (this part can be improved)
            try:
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    title = info_dict.get('title', url)
                playlist_listbox.insert(tk.END, title)
            except Exception as e:
                playlist_listbox.insert(tk.END, url)
        current_index = None  # Reset the current index

# Setup GUI
root = tk.Tk()
root.title("YouTube Music Streamer by Washer.")
root.geometry("600x600")
root.resizable(False, False)  # Disable window resizing

style = ttk.Style()
style.theme_use("clam")  # You can change the theme to "clam", "default", etc.

# Add padding around widgets
padding = {"padx": 10, "pady": 5}

search_frame = ttk.Frame(root)
search_frame.pack(fill=tk.X, **padding)

search_label = ttk.Label(search_frame, text="Search for a Song:")
search_label.pack(side=tk.LEFT)

search_entry = ttk.Entry(search_frame, width=50)
search_entry.pack(side=tk.LEFT, expand=True)

search_button = ttk.Button(search_frame, text="Search", command=search_videos)
search_button.pack(side=tk.LEFT)

# Bind the Enter key to the search_entry widget
search_entry.bind('<Return>', lambda event: search_videos())

result_frame = ttk.Frame(root)
result_frame.pack(fill=tk.BOTH, expand=True, **padding)

result_label = ttk.Label(result_frame, text="Search Results:")
result_label.pack()

video_list = Listbox(result_frame, width=100, height=10)
video_list.pack(fill=tk.BOTH, expand=True)

# Bind double-click event to add the selected video to the playlist
video_list.bind('<Double-1>', lambda event: add_to_playlist())

# Create a frame to hold the buttons side by side
button_frame = ttk.Frame(result_frame)
button_frame.pack(fill=tk.X, **padding)

# Add the "Clear Searches" button to the button_frame
clear_searches_button = ttk.Button(button_frame, text="Clear Searches", command=clear_searches)
clear_searches_button.pack(side=tk.LEFT)

# Add the "Add to Playlist" button and place it at specific coordinates
add_button = ttk.Button(button_frame, text="Add to Playlist", command=add_to_playlist)
add_button.place(x=240, y=0)  # Adjust the x and y values as needed

playlist_frame = ttk.Frame(root)
playlist_frame.pack(fill=tk.BOTH, expand=True, **padding)

playlist_label = ttk.Label(playlist_frame, text="Playlist:")
playlist_label.pack()

playlist_listbox = Listbox(playlist_frame, width=100, height=10)
playlist_listbox.pack(fill=tk.BOTH, expand=True)

play_button = ttk.Button(root, text="Play Playlist", command=lambda: threading.Thread(target=start_playlist).start())
play_button.pack(**padding)

control_frame = ttk.Frame(root)
control_frame.pack(fill=tk.X, **padding)

clear_button = ttk.Button(control_frame, text="Clear Playlist", command=clear_playlist)
clear_button.pack(side=tk.LEFT, **padding)

remove_button = ttk.Button(control_frame, text="Remove Selected", command=remove_selected)
remove_button.pack(side=tk.LEFT, **padding)

save_button = ttk.Button(control_frame, text="Save Playlist", command=save_playlist)
save_button.pack(side=tk.LEFT, **padding)

load_button = ttk.Button(control_frame, text="Load Playlist", command=load_playlist)
load_button.pack(side=tk.LEFT, **padding)

# This spacer frame will push the time_label to the far right
spacer = ttk.Frame(control_frame)
spacer.pack(side=tk.LEFT, expand=True)

time_label = ttk.Label(control_frame, text="00:00 / 00:00")
time_label.pack(side=tk.LEFT, padx=10)

playlist = []

root.mainloop()
