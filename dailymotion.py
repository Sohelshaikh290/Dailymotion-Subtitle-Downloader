import streamlit as st
import yt_dlp
import re
import io
import zipfile
import datetime
import os
import tempfile

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Universal Subtitle Downloader",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# =========================================================
# PREMIUM CSS UI
# =========================================================
st.markdown("""
<style>

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Main App Background */
.stApp {
    background: linear-gradient(135deg, #0f172a 0%, #111827 40%, #1e293b 100%);
    color: white;
}

/* Container */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 900px;
}

/* Hero Section */
.hero-box {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 40px;
    border-radius: 30px;
    backdrop-filter: blur(12px);
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35);
    margin-bottom: 30px;
}

/* Main Title */
.main-title {
    font-size: 3.4rem;
    font-weight: 800;
    background: linear-gradient(to right, #60a5fa, #8b5cf6, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 15px;
}

/* Subtitle */
.subtitle {
    color: #d1d5db;
    font-size: 1.1rem;
    line-height: 1.8;
}

/* Feature Cards */
.feature-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 22px;
    padding: 22px;
    text-align: center;
    transition: 0.3s ease;
    height: 100%;
}

.feature-card:hover {
    transform: translateY(-6px);
    background: rgba(255,255,255,0.08);
}

/* Text Input */
.stTextInput input {
    background-color: rgba(255,255,255,0.06) !important;
    color: white !important;
    border-radius: 18px !important;
    border: 2px solid rgba(255,255,255,0.1) !important;
    padding: 14px !important;
    font-size: 16px !important;
}

/* Buttons */
.stButton > button {
    width: 100%;
    border-radius: 18px;
    border: none;
    padding: 14px;
    font-size: 18px;
    font-weight: 700;
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    color: white;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: scale(1.02);
    box-shadow: 0 0 25px rgba(99,102,241,0.6);
}

/* Download Button */
.stDownloadButton > button {
    width: 100%;
    border-radius: 18px;
    padding: 14px;
    font-size: 18px;
    font-weight: 700;
    border: none;
    background: linear-gradient(90deg, #10b981, #06b6d4);
    color: white;
}

/* Radio & Checkbox */
label, .stRadio label, .stCheckbox label {
    color: #f9fafb !important;
}

/* Video Info Box */
.info-box {
    background: rgba(255,255,255,0.05);
    border-radius: 22px;
    padding: 20px;
    border: 1px solid rgba(255,255,255,0.08);
    margin-top: 20px;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 35px;
    color: #9ca3af;
    font-size: 14px;
}

hr {
    border-color: rgba(255,255,255,0.08);
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HERO SECTION
# =========================================================
st.markdown("""
<div class="hero-box">
    <div class="main-title">🎬 Universal Subtitle Downloader</div>
    <div class="subtitle">
        Download subtitles from <b>YouTube</b>, <b>Dailymotion</b>, and more.<br>
        Export subtitles as <b>SRT</b>, <b>TXT</b>, or original formats instantly.
    </div>
</div>
""", unsafe_allow_html=True)

# =========================================================
# FEATURES
# =========================================================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h3>⚡ Fast</h3>
        <p>Lightning fast subtitle extraction powered by yt-dlp.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <h3>🌍 Multi-language</h3>
        <p>Supports manual, auto-generated, and translated subtitles.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <h3>🎨 Premium UI</h3>
        <p>Modern glassmorphism inspired interface design.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def get_video_info(url):
    """Fetches video metadata and available subtitles using yt-dlp"""

    ydl_opts = {
        'quiet': True,
        'skip_download': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            subs = {}

            # Manual subtitles
            if 'subtitles' in info and info['subtitles']:
                for lang, tracks in info['subtitles'].items():
                    name = tracks[0].get('name', lang)
                    subs[f"{name} ({lang})"] = lang

            # Auto subtitles
            if 'automatic_captions' in info and info['automatic_captions']:
                for lang, tracks in info['automatic_captions'].items():
                    name = tracks[0].get('name', lang)

                    label = f"{name} ({lang}) [Auto-generated]"

                    if lang not in subs.values():
                        subs[label] = lang

            return {
                'id': info.get('id'),
                'title': info.get('title', 'Unknown_Title'),
                'channel': info.get('uploader', info.get('uploader_id', 'Unknown Channel')),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
                'available_subs': subs
            }

    except Exception:
        return None


def clean_filename(title):
    return re.sub(r'[\\\\/*?:"<>|]', "", title)


def clear_processed_cache():
    st.session_state.processed_files = None


def srt_to_text(srt_bytes):

    text = srt_bytes.decode('utf-8', errors='ignore')

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    lines = text.splitlines()

    clean_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.isdigit():
            continue

        if '-->' in stripped:
            continue

        clean_lines.append(stripped)

    return '\n'.join(clean_lines).encode('utf-8')


# =========================================================
# SESSION STATE
# =========================================================
if "video_info" not in st.session_state:
    st.session_state.video_info = None

if "last_url" not in st.session_state:
    st.session_state.last_url = ""

if "processed_files" not in st.session_state:
    st.session_state.processed_files = None

# =========================================================
# URL INPUT
# =========================================================
url = st.text_input(
    "🔗 Paste Video URL",
    placeholder="https://youtube.com/watch?v=..."
)

if url != st.session_state.last_url:
    st.session_state.video_info = None
    st.session_state.processed_files = None
    st.session_state.last_url = url

# =========================================================
# START BUTTON
# =========================================================
if st.button("🚀 Fetch Video Details"):

    if url.strip() == "":
        st.warning("Please enter a valid video URL.")

    else:
        with st.spinner("Fetching video information..."):

            info = get_video_info(url)

            if info:
                st.session_state.video_info = info
                st.session_state.processed_files = None

            else:
                st.error("Failed to fetch video details.")

# =========================================================
# VIDEO DETAILS
# =========================================================
if st.session_state.video_info:

    info = st.session_state.video_info

    st.markdown("<hr>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:

        if info['thumbnail']:
            st.image(info['thumbnail'], use_container_width=True)

    with col2:

        st.markdown(f"""
        <div class="info-box">
            <h3>{info['title']}</h3>
            <p><b>👤 Channel:</b> {info['channel']}</p>
            <p><b>⏱️ Duration:</b> {str(datetime.timedelta(seconds=info['duration']))}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("## 📝 Subtitle Settings")

    subs_map = info['available_subs']

    if not subs_map:
        st.warning("No subtitles available for this video.")

    else:

        all_langs = list(subs_map.keys())

        # FORMAT
        format_choice = st.radio(
            "1️⃣ Choose Output Format",
            [
                "SRT (Recommended)",
                "Raw (Original Format)",
                "Text Only (No Timestamps)"
            ],
            on_change=clear_processed_cache
        )

        # SELECT ALL
        select_all = st.checkbox(
            "✅ Select All Languages",
            on_change=clear_processed_cache
        )

        if select_all:
            selected_langs = all_langs
            st.info(f"{len(all_langs)} languages selected.")

        else:
            selected_langs = st.multiselect(
                "2️⃣ Select Subtitle Languages",
                options=all_langs,
                default=[all_langs[0]] if all_langs else [],
                on_change=clear_processed_cache
            )

        # PROCESS BUTTON
        if selected_langs:

            if st.button("⚙️ Process Subtitles"):

                with st.spinner("Downloading and processing subtitles..."):

                    safe_title = clean_filename(info['title'])

                    selected_lang_codes = [
                        subs_map[label]
                        for label in selected_langs
                    ]

                    with tempfile.TemporaryDirectory() as temp_dir:

                        ydl_opts = {
                            'quiet': True,
                            'skip_download': True,
                            'writesubtitles': True,
                            'writeautomaticsub': True,
                            'subtitleslangs': selected_lang_codes,
                            'outtmpl': os.path.join(temp_dir, '%(id)s.%(ext)s'),
                        }

                        # RAW FORMAT
                        if format_choice == "Raw (Original Format)":

                            ydl_opts['subtitlesformat'] = 'best'
                            target_ext = None

                        else:

                            ydl_opts['subtitlesformat'] = 'srt/best'
                            ydl_opts['convertsubtitles'] = 'srt'
                            target_ext = '.srt'

                        try:

                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                ydl.download([url])

                            processed = []

                            for file in os.listdir(temp_dir):

                                if target_ext is None or file.endswith(target_ext):

                                    with open(os.path.join(temp_dir, file), 'rb') as f:
                                        data = f.read()

                                    parts = file.split('.')

                                    lang_code = parts[-2] if len(parts) >= 3 else "sub"

                                    original_file_ext = parts[-1]

                                    # TEXT MODE
                                    if format_choice == "Text Only (No Timestamps)":

                                        data = srt_to_text(data)
                                        final_ext = "txt"

                                    elif format_choice == "Raw (Original Format)":

                                        final_ext = original_file_ext

                                    else:

                                        final_ext = "srt"

                                    # FILE NAME
                                    if len(selected_langs) == 1:

                                        final_name = f"{safe_title}.{final_ext}"

                                    else:

                                        final_name = f"{safe_title} [{lang_code}].{final_ext}"

                                    processed.append((final_name, data))

                            if not processed:

                                st.error(
                                    "No subtitle files generated.\n"
                                    "Make sure FFmpeg is installed properly."
                                )

                            else:

                                st.session_state.processed_files = processed

                        except Exception as e:

                            st.error(f"Error processing subtitles:\n{e}")

            # =========================================================
            # DOWNLOAD BUTTONS
            # =========================================================
            if st.session_state.processed_files:

                st.success("✅ Subtitles processed successfully!")

                processed_files = st.session_state.processed_files

                safe_title = clean_filename(info['title'])

                # SINGLE FILE
                if len(processed_files) == 1:

                    file_name, data = processed_files[0]

                    st.download_button(
                        label=f"⬇️ Download {file_name}",
                        data=data,
                        file_name=file_name,
                        mime="text/plain"
                    )

                # MULTIPLE FILES ZIP
                else:

                    zip_buffer = io.BytesIO()

                    with zipfile.ZipFile(
                        zip_buffer,
                        "w",
                        zipfile.ZIP_DEFLATED
                    ) as zip_file:

                        for file_name, data in processed_files:
                            zip_file.writestr(file_name, data)

                    st.download_button(
                        label=f"⬇️ Download {len(processed_files)} Files (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name=f"{safe_title}_Subtitles.zip",
                        mime="application/zip"
                    )

# =========================================================
# FOOTER
# =========================================================
st.markdown("""
<div class="footer">
Made with ❤️ using Streamlit + yt-dlp + FFmpeg
</div>
""", unsafe_allow_html=True)
