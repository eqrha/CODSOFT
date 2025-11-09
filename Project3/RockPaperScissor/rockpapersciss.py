import tkinter as tk
import random

# -----------------------------
# Main Window
# -----------------------------
root = tk.Tk()
root.title("🎮 Rock Paper Scissors 🎮")
root.geometry("500x450")
root.config(bg="#121212")  # Dark gaming background
root.resizable(False, False)  # Fixed size window

# -----------------------------
# Scores
# -----------------------------
user_score = 0
computer_score = 0

# -----------------------------
# Functions
# -----------------------------
def computer_choice():
    return random.choice(["Rock", "Paper", "Scissors"])

def play(user_choice):
    global user_score, computer_score

    comp_choice = computer_choice()
    result_text = ""

    if user_choice == comp_choice:
        result_text = "Draw!"
        color = "#FFD700"  # Gold
    elif (user_choice == "Rock" and comp_choice == "Scissors") or \
         (user_choice == "Paper" and comp_choice == "Rock") or \
         (user_choice == "Scissors" and comp_choice == "Paper"):
        result_text = "You Win!"
        color = "#00FF00"  # Neon Green
        user_score += 1
    else:
        result_text = "You Lose!"
        color = "#FF0000"  # Neon Red
        computer_score += 1

    lbl_result.config(text=f"{result_text}\nYou: {user_choice} | Computer: {comp_choice}", fg=color)
    lbl_user_score.config(text=f"Your Score: {user_score}")
    lbl_comp_score.config(text=f"Computer Score: {computer_score}")

def reset_game():
    global user_score, computer_score
    user_score = 0
    computer_score = 0
    lbl_result.config(text="Make your move!", fg="#FFFFFF")
    lbl_user_score.config(text="Your Score: 0")
    lbl_comp_score.config(text="Computer Score: 0")

# -----------------------------
# Title
# -----------------------------
tk.Label(root, text="🎮 Rock Paper Scissors 🎮", font=("Orbitron", 20, "bold"), bg="#121212", fg="#00FFFF").pack(pady=15)

# -----------------------------
# Result Label
# -----------------------------
lbl_result = tk.Label(root, text="Make your move!", font=("Arial", 14, "bold"), bg="#121212", fg="#FFFFFF")
lbl_result.pack(pady=10)

# -----------------------------
# Buttons Frame
# -----------------------------
frame_buttons = tk.Frame(root, bg="#121212")
frame_buttons.pack(pady=15)

# Neon-style buttons
btn_rock = tk.Button(frame_buttons, text="Rock 🪨", width=12, height=2, font=("Arial", 12, "bold"),
                     bg="#FF4500", fg="#FFFFFF", activebackground="#FF6347", command=lambda: play("Rock"))
btn_rock.grid(row=0, column=0, padx=10, pady=5)

btn_paper = tk.Button(frame_buttons, text="Paper 📄", width=12, height=2, font=("Arial", 12, "bold"),
                      bg="#1E90FF", fg="#FFFFFF", activebackground="#00BFFF", command=lambda: play("Paper"))
btn_paper.grid(row=0, column=1, padx=10, pady=5)

btn_scissors = tk.Button(frame_buttons, text="Scissors ✂️", width=12, height=2, font=("Arial", 12, "bold"),
                         bg="#32CD32", fg="#FFFFFF", activebackground="#00FF00", command=lambda: play("Scissors"))
btn_scissors.grid(row=0, column=2, padx=10, pady=5)

# -----------------------------
# Scoreboard
# -----------------------------
lbl_user_score = tk.Label(root, text="Your Score: 0", font=("Arial", 12, "bold"), bg="#121212", fg="#00FF00")
lbl_user_score.pack(pady=5)

lbl_comp_score = tk.Label(root, text="Computer Score: 0", font=("Arial", 12, "bold"), bg="#121212", fg="#FF0000")
lbl_comp_score.pack(pady=5)

# -----------------------------
# Reset & Exit Buttons
# -----------------------------
frame_reset = tk.Frame(root, bg="#121212")
frame_reset.pack(pady=15)

btn_reset = tk.Button(frame_reset, text="Reset Game 🔄", font=("Arial", 12, "bold"), bg="#FF69B4", fg="#FFFFFF",
                      activebackground="#FF1493", width=15, command=reset_game)
btn_reset.grid(row=0, column=0, padx=10)

btn_exit = tk.Button(frame_reset, text="Exit 🚪", font=("Arial", 12, "bold"), bg="#8B0000", fg="#FFFFFF",
                     activebackground="#FF0000", width=15, command=root.quit)
btn_exit.grid(row=0, column=1, padx=10)

# -----------------------------
# Run the app
# -----------------------------
root.mainloop()
