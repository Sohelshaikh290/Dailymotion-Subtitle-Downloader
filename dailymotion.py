import streamlit as st
import yt_dlp
import re
import io
import zipfile
import datetime
import os
import tempfile

# --- Theme Toggle (Day / Night Mode) ---
st.set_page_config(page_title="Universal Subtitle Downloader", page_icon="🌐", layout="centered")

mode = st.sidebar.radio("🌓 Appearance Mode", ["Auto (Streamlit Default)", "Day ☀️", "Night 🌙"])
if mode == "Day ☀️":
    st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] { background-color: #F0F2F6; color: #111111; }
            [data-testid="stHeader"] { background-color: #F0F2F6; }
            p, h1, h2, h3, h4, h5, h6, label, span { color: #111111 !important; }
        </style>
    """, unsafe_allow_html=True)
elif mode == "Night 🌙":
    st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] { background-color: #0E1117; color: #FAFAFA; }
            [data-testid="stHeader"] { background-color: #0E1117; }
            p, h1, h2, h3, h4, h5, h6, label, span { color: #FAFAFA !important; }
            .stCheckbox label { color: #FAFAFA !important; }
            .stRadio label { color: #FAFAFA !important; }
        </style>
    """, unsafe_allow_html=True)

st.title("🌐 Universal Subtitle Downloader")
st.markdown("Download subtitles from **YouTube**, **Dailymotion**, and more. Extract as SRT, Raw Format, or Plain Text!")

# --- Helper Functions ---
def get_video_info(url):
    """Fetches video metadata and available subtitles using yt-dlp"""
    ydl_opts = {'quiet': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Parse available subtitles
            subs = {}
            all_available_codes = []
            
            if 'subtitles' in info and info['subtitles']:
                for lang, tracks in info['subtitles'].items():
                    name = tracks[0].get('name', lang)
                    subs["{} ({})".format(name, lang)] = lang
                    all_available_codes.append(lang)
            
            if 'automatic_captions' in info and info['automatic_captions']:
                for lang, tracks in info['automatic_captions'].items():
                    name = tracks[0].get('name', lang)
                    label = "{} ({}) [Auto-generated]".format(name, lang)
                    if lang not in subs.values():
                        subs[label] = lang
                    all_available_codes.append(lang)
            
            # Add auto-translation options to the main list if it's YouTube
            if 'youtube' in info.get('extractor', '').lower() or 'youtu.be' in url.lower():
                if all_available_codes:  # If there are ANY subs to translate from
                    translate_langs = {
                        "English": "en", "Bengali": "bn", "Hindi": "hi", 
                        "Spanish": "es", "French": "fr", "Japanese": "ja", 
                        "Arabic": "ar", "Russian": "ru", "Portuguese": "pt", 
                        "Korean": "ko", "Chinese (Simplified)": "zh-Hans"
                    }
                    for t_name, t_code in translate_langs.items():
                        label = "{} ({}) [Auto-Translated]".format(t_name, t_code)
                        # Check if yt-dlp already provided the exact translation key (e.g., 'hi-bn', 'en-bn')
                        exact_matches = [c for c in all_available_codes if c.endswith("-{}".format(t_code))]
                        if exact_matches:
                            subs[label] = exact_matches[0] # Use the exact key provided by YouTube
                        else:
                            # Fallback to regex: Match ANY base language translating to target
                            subs[label] = ".*-{}".format(t_code)
            
            return {
                'id': info.get('id'),
                'title': info.get('title', 'Unknown_Title'),
                # Safely attempts to find 'uploader' (YouTube) or falls back to 'uploader_id' (Dailymotion)
                'channel': info.get('uploader', info.get('uploader_id', 'Unknown Channel')),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
                'available_subs': subs
            }
    except Exception as e:
        return None

def clean_filename(title):
    """Removes ONLY characters that break Windows/Mac file systems."""
    return re.sub(r'[\\/*?:"<>|]', "", title)

def clear_processed_cache():
    """Clears generated files if user changes selections."""
    st.session_state.processed_files = None

def srt_to_text(srt_bytes):
    """Strips timestamps, sequence numbers, and HTML tags from SRT/VTT to provide pure text."""
    text = srt_bytes.decode('utf-8', errors='ignore')
    # Remove HTML formatting tags (like <i>, <font>)
    text = re.sub(r'<[^>]+>', '', text)
    lines = text.splitlines()
    
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.isdigit():  # Skip sequence numbers
            continue
        if '-->' in stripped:   # Skip timestamp lines
            continue
        if stripped.upper() == 'WEBVTT': # Skip VTT headers
            continue
        if stripped.startswith('Kind:') or stripped.startswith('Language:'):
            continue
        clean_lines.append(stripped)
        
    return '\n'.join(clean_lines).encode('utf-8')

# --- Session State Management ---
if "video_info" not in st.session_state:
    st.session_state.video_info = None
if "last_url" not in st.session_state:
    st.session_state.last_url = ""
if "processed_files" not in st.session_state:
    st.session_state.processed_files = None

# --- UI Layout ---
url = st.text_input("🔗 Paste YouTube or Dailymotion Video Link Here:")

if url != st.session_state.last_url:
    st.session_state.video_info = None
    st.session_state.processed_files = None
    st.session_state.last_url = url

if st.button("🚀 Start", type="primary"):
    if url.strip() == "":
        st.warning("Please enter a valid Video URL first.")
    else:
        with st.spinner("Fetching video details and subtitles..."):
            info = get_video_info(url)
            if info:
                st.session_state.video_info = info
                st.session_state.processed_files = None
            else:
                st.error("Failed to fetch video details. Please check the link.")

# --- Display Metadata and Subtitles ---
if st.session_state.video_info:
    info = st.session_state.video_info
    
    st.markdown("---")
    col1, col2 = st.columns([1, 2])
    with col1:
        if info['thumbnail']:
            st.image(info['thumbnail'], use_container_width=True)
        else:
            st.info("No thumbnail available.")
    with col2:
        st.subheader(info['title'])
        st.write("**👤 Channel:** {}".format(info['channel']))
        duration_str = str(datetime.timedelta(seconds=info['duration']))
        st.write("**⏱️ Runtime:** {}".format(duration_str))

    st.markdown("### 📝 Subtitle Settings")
    
    subs_map = info['available_subs']
    if not subs_map:
        st.warning("No subtitles found for this video.")
    else:
        all_langs = list(subs_map.keys())
        
        # 1. Format Selection
        format_choice = st.radio(
            "1️⃣ Choose Output Format:", 
            ["SRT (SubRip - Recommended)", "Raw (Original File Format)", "Text Only (No Timestamps)"],
            on_change=clear_processed_cache
        )
        
        # 2. Language Selection
        select_all = st.checkbox("✅ Select All Available Languages", on_change=clear_processed_cache)
        
        if select_all:
            selected_langs = all_langs
            st.info("{} languages selected.".format(len(all_langs)))
        else:
            selected_langs = st.multiselect(
                "2️⃣ Pick specific languages:", 
                options=all_langs, 
                default=[all_langs[0]] if all_langs else [],
                on_change=clear_processed_cache
            )

        # Download Logic
        if selected_langs:
            if st.button("⚙️ Process Subtitles", type="secondary"):
                with st.spinner("Extracting & Processing..."):
                    safe_title = clean_filename(info['title'])
                    
                    # The translation logic is now handled perfectly during info extraction
                    # We just pass the exact string or regex directly to yt-dlp!
                    selected_lang_codes = [subs_map[label] for label in selected_langs]
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Configure yt-dlp based on selected format
                        ydl_opts = {
                            'quiet': True,
                            'skip_download': True,
                            'writesubtitles': True,
                            'writeautomaticsub': True,
                            'subtitleslangs': selected_lang_codes,
                            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                        }
                        
                        if format_choice == "Raw (Original File Format)":
                            ydl_opts['subtitlesformat'] = 'best'
                        else:
                            # For SRT or Text, request SRT first. If FFmpeg is missing, yt-dlp ignores this and outputs vtt.
                            ydl_opts['subtitlesformat'] = 'srt/best'
                            ydl_opts['convertsubtitles'] = 'srt'
                        
                        try:
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([url])
                            
                            processed = []
                            for file in os.listdir(temp_dir):
                                # Skip any non-subtitle files that might accidentally be generated
                                if file.endswith('.json') or file.endswith('.mp4') or file.endswith('.webm'):
                                    continue
                                    
                                with open(os.path.join(temp_dir, file), 'rb') as f:
                                    data = f.read()
                                
                                # Identify language code from file (e.g., id.en.srt)
                                parts = file.split('.')
                                lang_code = parts[-2] if len(parts) >= 3 else "sub"
                                original_file_ext = parts[-1]
                                
                                # Fallback check: If we asked for SRT but got VTT, FFmpeg might be missing
                                if format_choice == "SRT (SubRip - Recommended)" and original_file_ext != "srt":
                                    st.warning(f"Note: Saved as {original_file_ext.upper()} because FFmpeg is missing on the server.")
                                
                                # Apply Text parsing if requested
                                if format_choice == "Text Only (No Timestamps)":
                                    data = srt_to_text(data)
                                    final_ext = "txt"
                                elif format_choice == "Raw (Original File Format)":
                                    final_ext = original_file_ext
                                else:
                                    final_ext = original_file_ext # Use what yt-dlp gave us (srt or fallback vtt)
                                    
                                # Name perfectly based on number of files
                                if len(selected_langs) == 1:
                                    final_name = "{}.{}".format(safe_title, final_ext)
                                else:
                                    final_name = "{} [{}].{}".format(safe_title, lang_code, final_ext)
                                    
                                processed.append((final_name, data))
                            
                            if not processed:
                                st.error("Failed to extract subtitles. The selected language might not be available for this video.")
                            else:
                                st.session_state.processed_files = processed
                                
                        except Exception as e:
                            st.error("Error processing subtitles: {}".format(e))
            
            # Streamlit download buttons
            if st.session_state.processed_files:
                st.success("✅ Processed successfully!")
                processed_files = st.session_state.processed_files
                safe_title = clean_filename(info['title'])
                
                if len(processed_files) == 1:
                    file_name, data = processed_files[0]
                    st.download_button(
                        label="⬇️ Download {}".format(file_name),
                        data=data,
                        file_name=file_name,
                        mime="text/plain"
                    )
                else:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for file_name, data in processed_files:
                            zip_file.writestr(file_name, data)
                    
                    st.download_button(
                        label="⬇️ Download {} Files (ZIP Folder)".format(len(processed_files)),
                        data=zip_buffer.getvalue(),
                        file_name="{}_Subtitles.zip".format(safe_title),
                        mime="application/zip"
                    )
