import streamlit as st
import random
import time
import pandas as pd
import os

ROWS, COLS = 5, 10
GAME_DURATION = 10
LEADERBOARD_FILE = "leaderboard.csv"

REWARDS = {"🍊": 50, "🍎": 20, "🍋": 10, "🏀": 0}

# --- Load / Save Leaderboard ---
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        return pd.read_csv(LEADERBOARD_FILE)
    else:
        return pd.DataFrame(columns=["name", "score"])

def save_leaderboard(df):
    df.to_csv(LEADERBOARD_FILE, index=False)

# --- Generate Grid ---
def generate_randomized_grid(rows, cols):
    grid = [["" for _ in range(cols)] for _ in range(rows)]
    placed = set()

    def place_item(symbol, count, cluster=False):
        attempts = 0
        while count > 0 and attempts < 1000:
            r, c = random.randint(0, rows - 1), random.randint(0, cols - 1)
            if (r, c) in placed:
                attempts += 1
                continue
            grid[r][c] = symbol
            placed.add((r, c))
            count -= 1
            if cluster:
                neighbors = [(r+dr, c+dc) for dr in [-1,0,1] for dc in [-1,0,1] if not (dr==0 and dc==0)]
                random.shuffle(neighbors)
                for nr, nc in neighbors:
                    if 0 <= nr < rows and 0 <= nc < cols and count > 0 and (nr, nc) not in placed:
                        grid[nr][nc] = symbol
                        placed.add((nr, nc))
                        count -= 1

    place_item("🍊", 5)
    place_item("🍎", 10)
    place_item("🍋", 20, cluster=True)
    place_item("🏀", 15, cluster=True)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "":
                grid[r][c] = "🏀"

    return grid

# --- Session State Init ---
if "grid" not in st.session_state:
    st.session_state.grid = generate_randomized_grid(ROWS, COLS)
    st.session_state.started = False
    st.session_state.start_time = None
    st.session_state.remaining_time = GAME_DURATION
    st.session_state.score = 0
    st.session_state.click_path = []
    st.session_state.leaderboard = load_leaderboard()

# --- Custom CSS to make buttons small ---
st.markdown("""
    <style>
        div[data-testid="column"] button {
            font-size: 20px !important;
            padding: 4px 6px !important;
            height: auto !important;
            line-height: 1 !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("🍊 Visual Foraging Game")
st.write("Click **Start** to begin. Forage fruits to score! You have **10 seconds**.")

st.markdown("""
### 📝 Scoring Instructions:
- 🍊 **Orange**: +50 points  
- 🍎 **Apple**: +20 points  
- 🍋 **Lemon**: +10 points  
- 🏀 **Basketball (decoy)**: **0 points**  

Click on the fruits to collect them. Maximize your score before time runs out!
""")

# --- Timer Placeholder ---
timer_placeholder = st.empty()

# --- Start Button ---
if not st.session_state.started:
    if st.button("▶️ Start Game"):
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.rerun()

# --- Update Timer ---
if st.session_state.started:
    elapsed = int(time.time() - st.session_state.start_time)
    st.session_state.remaining_time = max(0, GAME_DURATION - elapsed)
    timer_placeholder.markdown(f"⏳ Time left: **{st.session_state.remaining_time}s**")

# --- Game Grid (Responsive with Emojis) ---
half = COLS // 2
for i in range(ROWS):
    first_half = st.columns(half)
    second_half = st.columns(COLS - half)
    for j in range(half):
        cell_id = f"{i}-{j}"
        fruit = st.session_state.grid[i][j]
        clicked_coords = [(r, c) for r, c, _ in st.session_state.click_path]
        if (i, j) in clicked_coords:
            index = clicked_coords.index((i, j))
            display = f"{fruit}({index+1})"
            first_half[j].button(display, key=cell_id, disabled=True)
        else:
            if st.session_state.started and st.session_state.remaining_time > 0:
                if first_half[j].button(fruit, key=cell_id):
                    st.session_state.click_path.append((i, j, fruit))
                    st.session_state.score += REWARDS[fruit]
                    st.rerun()
            else:
                first_half[j].button(fruit, key=cell_id, disabled=True)

    for j in range(half, COLS):
        cell_id = f"{i}-{j}"
        fruit = st.session_state.grid[i][j]
        clicked_coords = [(r, c) for r, c, _ in st.session_state.click_path]
        if (i, j) in clicked_coords:
            index = clicked_coords.index((i, j))
            display = f"{fruit}({index+1})"
            second_half[j - half].button(display, key=cell_id, disabled=True)
        else:
            if st.session_state.started and st.session_state.remaining_time > 0:
                if second_half[j - half].button(fruit, key=cell_id):
                    st.session_state.click_path.append((i, j, fruit))
                    st.session_state.score += REWARDS[fruit]
                    st.rerun()
            else:
                second_half[j - half].button(fruit, key=cell_id, disabled=True)

# --- Path and Score ---
if st.session_state.started:
    st.subheader("🧭 Path Taken")
    path_display = " → ".join([f"{fruit}({idx+1})" for idx, (_, _, fruit) in enumerate(st.session_state.click_path)])
    st.write(path_display or "No fruits foraged yet.")
    st.metric("Score", st.session_state.score)

# --- End Game ---
if st.session_state.remaining_time == 0:
    st.success("⏱️ Time's up!")

    if "submitted_score" not in st.session_state:
        name = st.text_input("Enter your name to save your score:", max_chars=20)
        if name:
            new_row = pd.DataFrame([{"name": name, "score": st.session_state.score}])
            st.session_state.leaderboard = pd.concat([st.session_state.leaderboard, new_row], ignore_index=True)
            save_leaderboard(st.session_state.leaderboard)
            st.session_state.submitted_score = True
            st.rerun()
    else:
        st.subheader("🏆 Leaderboard (Top 10)")
        top_scores = st.session_state.leaderboard.sort_values(by="score", ascending=False).head(10).reset_index(drop=True)
        for idx, row in top_scores.iterrows():
            st.write(f"{idx+1}. {row['name']} — {row['score']} points")

        if st.button("🔁 Play Again"):
            for key in list(st.session_state.keys()):
                if key not in ["leaderboard"]:
                    del st.session_state[key]
            st.rerun()
