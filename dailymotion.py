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
    page_icon="🌐",
    layout="centered"
)

# =========================================================
# THEME TOGGLE
# =========================================================
mode = st.sidebar.radio(
    "🌓 Appearance Mode",
    ["Auto (Streamlit Default)", "Day ☀️", "Night 🌙"]
)

if mode == "Day ☀️":
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #F0F2F6;
            color: #111111;
        }

        [data-testid="stHeader"] {
            background-color: #F0F2F6;
        }

        p, h1, h2, h3, h4, h5, h6, label, span {
            color: #111111 !important;
        }
    </style>
    """, unsafe_allow_html=True)

elif mode == "Night 🌙":
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #0E1117;
            color: #FAFAFA;
        }

        [data-testid="stHeader"] {
            background-color: #0E1117;
        }

        p, h1, h2, h3, h4, h5, h6, label, span {
            color: #FAFAFA !important;
        }

        .stCheckbox label {
            color: #FAFAFA !important;
        }

        .stRadio label {
            color: #FAFAFA !important;
        }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# TITLE
# =========================================================
st.title("🌐 Universal Subtitle Downloader")

st.markdown("""
Download subtitles from:

- YouTube
- Dailymotion
- Vimeo
- Other supported sites

Extract subtitles as:

- SRT
- Original Format
- Plain Text
""")

st.caption("✅ Best compatibility: YouTube videos with captions enabled.")

# =========================================================
# SESSION STATE
# =========================================================
if "video_info" not in st.session_state:
    st.session_state.video_info = None

if "last_url" not in st.session_state:
    st.session_state.last_url = ""

if "processed_files" not in st.session_state:
    st.session_state.processed_files = None

if "process_clicked" not in st.session_state:
    st.session_state.process_clicked = False

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def clean_filename(title):
    """
    Removes characters invalid for Windows/Mac filenames.
    """
    return re.sub(r'[\\/*?:"<>|]', "", title)


def clear_processed_cache():
    st.session_state.processed_files = None
    st.session_state.process_clicked = False


def srt_to_text(srt_bytes):
    """
    Convert subtitle file into plain readable text.
    """

    text = srt_bytes.decode(errors="ignore")

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    lines = text.splitlines()

    clean_lines = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            continue

        if stripped.isdigit():
            continue

        if "-->" in stripped:
            continue

        if stripped.upper() == "WEBVTT":
            continue

        if stripped.startswith("Kind:"):
            continue

        if stripped.startswith("Language:"):
            continue

        clean_lines.append(stripped)

    return "\n".join(clean_lines).encode("utf-8")


# =========================================================
# VIDEO INFO FUNCTION
# =========================================================
def get_video_info(url):

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "no_warnings": True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=False)

            subs = {}

            # -------------------------------------------------
            # MANUAL SUBTITLES
            # -------------------------------------------------
            if info.get("subtitles"):

                for lang, tracks in info["subtitles"].items():

                    try:
                        name = tracks[0].get("name", lang)
                    except:
                        name = lang

                    label = f"{name} ({lang})"

                    subs[label] = lang

            # -------------------------------------------------
            # AUTO GENERATED SUBTITLES
            # -------------------------------------------------
            if info.get("automatic_captions"):

                for lang, tracks in info["automatic_captions"].items():

                    try:
                        name = tracks[0].get("name", lang)
                    except:
                        name = lang

                    label = f"{name} ({lang}) [Auto-generated]"

                    if lang not in subs.values():
                        subs[label] = lang

            # -------------------------------------------------
            # AUTO TRANSLATION OPTIONS
            # -------------------------------------------------
            extractor = info.get("extractor", "").lower()

            if "youtube" in extractor or "youtu.be" in url.lower():

                translate_langs = {
                    "English": "en",
                    "Bengali": "bn",
                    "Hindi": "hi",
                    "Spanish": "es",
                    "French": "fr",
                    "Japanese": "ja",
                    "Arabic": "ar",
                    "Russian": "ru",
                    "Portuguese": "pt",
                    "Korean": "ko",
                    "Chinese": "zh-Hans"
                }

                for t_name, t_code in translate_langs.items():

                    label = f"{t_name} ({t_code}) [Auto-Translated]"

                    subs[label] = t_code

            return {
                "id": info.get("id"),
                "title": info.get("title", "Unknown_Title"),
                "channel": info.get(
                    "uploader",
                    info.get("uploader_id", "Unknown Channel")
                ),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail"),
                "available_subs": subs
            }

    except Exception as e:

        st.error(f"DEBUG ERROR:\n\n{str(e)}")

        return None


# =========================================================
# UI
# =========================================================
url = st.text_input(
    "🔗 Paste Video URL Here:"
)

# Reset if URL changes
if url != st.session_state.last_url:

    st.session_state.video_info = None
    st.session_state.processed_files = None
    st.session_state.process_clicked = False
    st.session_state.last_url = url

# =========================================================
# FETCH BUTTON
# =========================================================
if st.button("🚀 Start", type="primary"):

    if not url.strip():

        st.warning("Please enter a valid video URL.")

    else:

        with st.spinner("Fetching video details..."):

            info = get_video_info(url)

            if info:

                st.session_state.video_info = info
                st.session_state.processed_files = None
                st.success("Video loaded successfully!")

            else:
                st.error("Failed to fetch video details.")

# =========================================================
# VIDEO DISPLAY
# =========================================================
if st.session_state.video_info:

    info = st.session_state.video_info

    st.markdown("---")

    col1, col2 = st.columns([1, 2])

    # -----------------------------------------------------
    # THUMBNAIL
    # -----------------------------------------------------
    with col1:

        if info["thumbnail"]:
            st.image(
                info["thumbnail"],
                use_container_width=True
            )
        else:
            st.info("No thumbnail available.")

    # -----------------------------------------------------
    # VIDEO DETAILS
    # -----------------------------------------------------
    with col2:

        st.subheader(info["title"])

        st.write(f"**👤 Channel:** {info['channel']}")

        duration_str = str(
            datetime.timedelta(seconds=info["duration"])
        )

        st.write(f"**⏱️ Runtime:** {duration_str}")

    # =====================================================
    # SUBTITLE SETTINGS
    # =====================================================
    st.markdown("## 📝 Subtitle Settings")

    subs_map = info["available_subs"]

    if not subs_map:

        st.warning("No subtitles found for this video.")

    else:

        all_langs = list(subs_map.keys())

        # -------------------------------------------------
        # FORMAT
        # -------------------------------------------------
        format_choice = st.radio(
            "1️⃣ Choose Output Format",
            [
                "SRT (Recommended)",
                "Raw (Original Format)",
                "Text Only (No Timestamps)"
            ],
            on_change=clear_processed_cache
        )

        # -------------------------------------------------
        # SELECT ALL
        # -------------------------------------------------
        select_all = st.checkbox(
            "✅ Select All Languages",
            on_change=clear_processed_cache
        )

        # -------------------------------------------------
        # MULTISELECT
        # -------------------------------------------------
        if select_all:

            selected_langs = all_langs

            st.info(f"{len(all_langs)} languages selected.")

        else:

            selected_langs = st.multiselect(
                "2️⃣ Choose Languages",
                options=all_langs,
                default=[all_langs[0]] if all_langs else [],
                on_change=clear_processed_cache
            )

        # =================================================
        # PROCESS BUTTON
        # =================================================
        if selected_langs:

            if st.button("⚙️ Process Subtitles"):

                st.session_state.process_clicked = True

            # ---------------------------------------------
            # PROCESS
            # ---------------------------------------------
            if st.session_state.process_clicked:

                with st.spinner("Processing subtitles..."):

                    safe_title = clean_filename(
                        info["title"]
                    )

                    selected_lang_codes = [
                        subs_map[label]
                        for label in selected_langs
                    ]

                    with tempfile.TemporaryDirectory() as temp_dir:

                        ydl_opts = {
                            "quiet": True,
                            "skip_download": True,
                            "writesubtitles": True,
                            "writeautomaticsub": True,
                            "subtitleslangs": selected_lang_codes,
                            "outtmpl": os.path.join(
                                temp_dir,
                                "%(id)s.%(ext)s"
                            )
                        }

                        # ---------------------------------
                        # FORMAT OPTIONS
                        # ---------------------------------
                        if format_choice == "Raw (Original Format)":

                            ydl_opts["subtitlesformat"] = "best"

                        else:

                            ydl_opts["subtitlesformat"] = "srt/best"
                            ydl_opts["convertsubtitles"] = "srt"

                        try:

                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:

                                ydl.download([url])

                            processed = []

                            # -----------------------------
                            # READ GENERATED FILES
                            # -----------------------------
                            for file in os.listdir(temp_dir):

                                # Ignore junk files
                                if file.endswith(
                                    (
                                        ".json",
                                        ".mp4",
                                        ".webm",
                                        ".mkv",
                                        ".part"
                                    )
                                ):
                                    continue

                                file_path = os.path.join(
                                    temp_dir,
                                    file
                                )

                                with open(file_path, "rb") as f:

                                    data = f.read()

                                # Better filename parsing
                                name_without_ext, ext = os.path.splitext(file)

                                original_file_ext = ext.replace(".", "")

                                lang_code = (
                                    name_without_ext.split(".")[-1]
                                )

                                # -------------------------
                                # TEXT CONVERSION
                                # -------------------------
                                if format_choice == "Text Only (No Timestamps)":

                                    data = srt_to_text(data)

                                    final_ext = "txt"

                                elif format_choice == "SRT (Recommended)":

                                    if original_file_ext != "srt":

                                        st.warning(
                                            f"Saved as {original_file_ext.upper()} because FFmpeg conversion failed."
                                        )

                                    final_ext = original_file_ext

                                else:

                                    final_ext = original_file_ext

                                # -------------------------
                                # OUTPUT NAME
                                # -------------------------
                                if len(selected_langs) == 1:

                                    final_name = (
                                        f"{safe_title}.{final_ext}"
                                    )

                                else:

                                    final_name = (
                                        f"{safe_title} [{lang_code}].{final_ext}"
                                    )

                                processed.append(
                                    (
                                        final_name,
                                        data
                                    )
                                )

                            # -----------------------------
                            # NO FILES
                            # -----------------------------
                            if not processed:

                                st.error(
                                    "No subtitle files were generated."
                                )

                            else:

                                st.session_state.processed_files = processed

                                st.success(
                                    "✅ Subtitles processed successfully!"
                                )

                        except Exception as e:

                            st.error(
                                f"Error processing subtitles:\n\n{str(e)}"
                            )

        # =================================================
        # DOWNLOAD SECTION
        # =================================================
        if st.session_state.processed_files:

            processed_files = st.session_state.processed_files

            safe_title = clean_filename(info["title"])

            # ---------------------------------------------
            # SINGLE FILE
            # ---------------------------------------------
            if len(processed_files) == 1:

                file_name, data = processed_files[0]

                st.download_button(
                    label=f"⬇️ Download {file_name}",
                    data=data,
                    file_name=file_name,
                    mime="text/plain"
                )

            # ---------------------------------------------
            # MULTIPLE FILES -> ZIP
            # ---------------------------------------------
            else:

                zip_buffer = io.BytesIO()

                with zipfile.ZipFile(
                    zip_buffer,
                    "w",
                    zipfile.ZIP_DEFLATED
                ) as zip_file:

                    for file_name, data in processed_files:

                        zip_file.writestr(
                            file_name,
                            data
                        )

                st.download_button(
                    label=f"⬇️ Download ZIP ({len(processed_files)} Files)",
                    data=zip_buffer.getvalue(),
                    file_name=f"{safe_title}_Subtitles.zip",
                    mime="application/zip"
                )
