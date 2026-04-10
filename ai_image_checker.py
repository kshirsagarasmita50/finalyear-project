# filename: ai_image_checker.py
# pip install streamlit opencv-python numpy pillow
# streamlit run ai_image_checker.py

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import tempfile
import threading
import time 
import requests

# ---------- Page Config ----------
st.set_page_config(
    page_title="Advanced AI Image & Video Checker",
    page_icon="🧠",
    layout="centered"
)

st.title("🧠 Advanced AI Image & Video Checker")
st.subheader("Detect AI-edited media with visual proof + advanced comparison tool")

# ======================================================
# AI HEURISTIC FUNCTION
# ======================================================

def analyze_image(img_array):
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.mean(edges) / 255

    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_var = laplacian.var()

    edge_score = min(edge_density * 300, 100)
    noise_score = min(laplacian_var / 10, 100)

    ai_score = (edge_score * 0.6 + noise_score * 0.4)
    ai_percentage = int(min(max(ai_score, 0), 100))
    manual_percentage = 100 - ai_percentage

    return ai_percentage, manual_percentage, edges, laplacian

# ======================================================
# TIC TAC TOE GAME WITH AI
# ======================================================

def init_game():
    if "board" not in st.session_state:
        st.session_state.board = [""] * 9
        st.session_state.current_player = None  # set after user chooses X or O
        st.session_state.winner = None
        st.session_state.user_choice = None
        st.session_state.ai_choice = None
        st.session_state.game_started = False

def check_winner(board):
    win_patterns = [
        (0,1,2),(3,4,5),(6,7,8),
        (0,3,6),(1,4,7),(2,5,8),
        (0,4,8),(2,4,6)
    ]
    for a,b,c in win_patterns:
        if board[a] == board[b] == board[c] and board[a] != "":
            return board[a]
    return None

def ai_move():
    # Simple AI: pick first empty cell
    for i in range(9):
        if st.session_state.board[i] == "":
            st.session_state.board[i] = st.session_state.ai_choice
            break

def render_board():
    for i in range(3):
        cols = st.columns(3)
        for j in range(3):
            idx = i*3 + j
            if cols[j].button(st.session_state.board[idx] or " ", key=f"cell_{idx}"):
                if st.session_state.board[idx] == "" and not st.session_state.winner and st.session_state.game_started:
                    # User move
                    st.session_state.board[idx] = st.session_state.user_choice
                    winner = check_winner(st.session_state.board)
                    if winner:
                        st.session_state.winner = winner
                        return
                    # AI move
                    ai_move()
                    winner = check_winner(st.session_state.board)
                    if winner:
                        st.session_state.winner = winner
                        return

# ======================================================
# MODE SELECTION
# ======================================================

mode = st.radio("Select Mode:", ["🖼️ Single Image", "🆚 Compare Two Images", "🎥 Video"])

# ======================================================
# SINGLE IMAGE ANALYSIS
# ======================================================

if mode == "🖼️ Single Image":

    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file).convert("RGB")
        img_array = np.array(image)

        st.image(image, caption="Uploaded Image", width=250)

        if st.button("🔍 Analyze Image"):

            with st.spinner("Analyzing image..."):
                ai_perc, manual_perc, edges, laplacian = analyze_image(img_array)
# ======================================================
# COMPARE TWO IMAGES
# ======================================================

if mode == "🆚 Compare Two Images":

    st.subheader("Upload Two Images")

    col1, col2 = st.columns(2)

    with col1:
        img1_file = st.file_uploader("Image 1", type=["jpg", "png"], key="img1")

    with col2:
        img2_file = st.file_uploader("Image 2", type=["jpg", "png"], key="img2")

    if img1_file and img2_file:

        img1 = Image.open(img1_file).convert("RGB")
        img2 = Image.open(img2_file).convert("RGB")
        img2 = img2.resize(img1.size)

        img1_array = np.array(img1)
        img2_array = np.array(img2)

        st.image([img1, img2], caption=["Image 1", "Image 2"])

        if st.button("🔍 Compare"):

            diff = cv2.absdiff(img1_array, img2_array)
            diff_gray = cv2.cvtColor(diff, cv2.COLOR_RGB2GRAY)

            similarity = max(0, 100 - int(np.mean(diff_gray)))

            st.metric("Similarity %", f"{similarity}%")
            st.progress(similarity / 100)

# ======================================================
# VIDEO + TIC TAC TOE (AI) + BACKGROUND PROCESSING
# ======================================================

if mode == "🎥 Video":

    uploaded_video = st.file_uploader("Upload Video", type=["mp4", "avi", "mov"])

    if uploaded_video is not None:

        tfile = tempfile.NamedTemporaryFile(delete=False)
        tfile.write(uploaded_video.read())

        st.video(uploaded_video)

        st.subheader("🎮 Play Tic Tac Toe Against AI While Video is Processing")
        init_game()

        # Pre-game choice
        if not st.session_state.get("game_started", False):
            st.subheader("Choose your symbol to start the game")
            col1, col2 = st.columns(2)
            if col1.button("❌ X"):
                st.session_state.user_choice = "X"
                st.session_state.ai_choice = "O"
                st.session_state.current_player = "X"
                st.session_state.game_started = True
            if col2.button("⭕ O"):
                st.session_state.user_choice = "O"
                st.session_state.ai_choice = "X"
                st.session_state.current_player = "O"
                st.session_state.game_started = True

        if st.session_state.get("game_started", False):
            render_board()
            if st.session_state.winner:
                st.success(f"🏆 Winner: {st.session_state.winner}")

            if st.button("🔄 Reset Game"):
                st.session_state.board = [""] * 9
                st.session_state.winner = None
                st.session_state.user_choice = None
                st.session_state.ai_choice = None
                st.session_state.current_player = None
                st.session_state.game_started = False

        # Video processing in background
        progress_bar = st.empty()
        status_text = st.empty()
        result_text = st.empty()

        def analyze_video():
            cap = cv2.VideoCapture(tfile.name)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            current_frame = 0
            total_ai_score = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ai_perc, _, _, _ = analyze_image(frame_rgb)
                total_ai_score += ai_perc
                current_frame += 1
                if total_frames > 0:
                    progress = current_frame / total_frames
                    progress_bar.progress(progress)
                    status_text.text(f"Processing Frame {current_frame}/{total_frames}")
                time.sleep(0.01)

            cap.release()

            avg_ai = int(total_ai_score / current_frame) if current_frame > 0 else 0
            avg_manual = 100 - avg_ai

            result_text.success("✅ Video Analysis Complete")
            col1, col2 = st.columns(2)
            col1.metric("🤖 AI Influence", f"{avg_ai}%")
            col2.metric("✋ Manual", f"{avg_manual}%")
            progress_bar.progress(avg_ai / 100)

        if st.button("🔍 Analyze Video in Background"):
            thread = threading.Thread(target=analyze_video, daemon=True)
            thread.start()
            st.info("Video analysis started! Keep playing the game.")

st.markdown("---")
st.caption("Built using Python + Streamlit | AI Image Forensics Tool + AI Tic Tac Toe 🎮")