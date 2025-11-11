import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import collections
from datetime import datetime
import json
import re

def schedule_golf_groups(players, reservations, group_size):
    """예약자 기능을 포함한 최적의 골프 조를 편성하는 로직"""
    play_counts = collections.defaultdict(int)
    reservation_counts = collections.defaultdict(int)
    for _, reserved_player in reservations:
        if reserved_player:
            reservation_counts[reserved_player] += 1
    schedule = {}
    last_round_players = set()

    for date, reserved_player in reservations:
        current_group = []
        if reserved_player and reserved_player in players:
            current_group.append(reserved_player)

        needed = group_size - len(current_group)
        if needed > 0:
            available_players = [p for p in players if p not in last_round_players and p not in current_group]
            if len(available_players) < needed:
                candidates = [p for p in players if p not in current_group]
            else:
                candidates = available_players
            candidates.sort(key=lambda p: (play_counts[p], -reservation_counts[p], p))
            current_group.extend(candidates[:needed])

        schedule[date] = sorted(current_group)
        for player in current_group:
            play_counts[player] += 1
        last_round_players = set(current_group)

    return schedule, play_counts

class GolfSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("골프 조 편성 프로그램 (저장/스크롤 기능)")
        self.root.geometry("900x650")

        # --- 스크롤 기능 설정 --- #
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        container = ttk.Frame(main_frame, padding="20")
        container.pack(fill=tk.BOTH, expand=True)

        # Create two main panels for left and right content
        left_panel = ttk.Frame(container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right_panel = ttk.Frame(container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.style = ttk.Style()
        self.style.configure("TLabel", font=("맑은 고딕", 10))
        self.style.configure("TButton", font=("맑은 고딕", 10))
        self.style.configure("TEntry", font=("맑은 고딕", 10))

        input_frame = ttk.LabelFrame(left_panel, text="입력 정보", padding="15")
        input_frame.pack(fill=tk.X, pady=10)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="참여 인원 수 (1-10명):").grid(row=0, column=0, sticky=tk.W, pady=5)
        num_players_frame = ttk.Frame(input_frame)
        num_players_frame.grid(row=0, column=1, sticky=tk.EW)
        self.num_players_entry = ttk.Entry(num_players_frame, width=10)
        self.num_players_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.update_players_button = ttk.Button(num_players_frame, text="인원 확정", command=self.update_player_entries)
        self.update_players_button.pack(side=tk.LEFT, padx=5)

        self.player_entries_frame = ttk.Frame(input_frame)
        self.player_entries_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=5)
        self.player_name_entries = []

        ttk.Label(input_frame, text="예약 날짜 (예: 8/12/4 또는 8/12/4/예약자)").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.dates_text = tk.Text(input_frame, height=4, width=40, font=("맑은 고딕", 10))
        self.dates_text.grid(row=3, column=0, columnspan=2, sticky=tk.EW)

        ttk.Label(input_frame, text="한 조 인원:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.group_size_entry = ttk.Entry(input_frame)
        self.group_size_entry.grid(row=4, column=1, sticky=tk.EW)

        button_frame = ttk.Frame(left_panel)
        button_frame.pack(fill=tk.X, pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)

        self.generate_button = ttk.Button(button_frame, text="조 편성 생성", command=self.generate_schedule)
        self.generate_button.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))

        self.save_button = ttk.Button(button_frame, text="결과 저장하기", command=self.save_to_txt)
        self.save_button.grid(row=0, column=1, sticky=tk.EW, padx=(5, 0))

        self.save_input_button = ttk.Button(button_frame, text="입력 정보 저장", command=self.save_input_data)
        self.save_input_button.grid(row=1, column=0, sticky=tk.EW, padx=(0, 5), pady=5)

        self.load_input_button = ttk.Button(button_frame, text="입력 정보 불러오기", command=self.load_input_data)
        self.load_input_button.grid(row=1, column=1, sticky=tk.EW, padx=(5, 0), pady=5)

        output_frame = ttk.LabelFrame(right_panel, text="편성 결과", padding="15")
        output_frame.pack(fill=tk.BOTH, expand=True)
        self.result_text = tk.Text(output_frame, height=15, width=60, font=("맑은 고딕", 10), state="disabled")
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        self.num_players_entry.insert(0, "4")
        self.update_player_entries()
        self.save_button.config(state="disabled")


    def update_player_entries(self, *args):
        try:
            num_players = int(self.num_players_entry.get())
            if not 1 <= num_players <= 10:
                messagebox.showerror("입력 오류", "참여 인원은 1명에서 10명 사이여야 합니다.")
                return
        except ValueError:
            messagebox.showerror("입력 오류", "참여 인원 수에 올바른 숫자를 입력해주세요.")
            return

        for widget in self.player_entries_frame.winfo_children():
            widget.destroy()
        self.player_name_entries.clear()

        ttk.Label(self.player_entries_frame, text="플레이어 이름:").pack(anchor=tk.W)
        for i in range(num_players):
            frame = ttk.Frame(self.player_entries_frame)
            frame.pack(fill=tk.X, pady=2)
            label = ttk.Label(frame, text=f"  - 플레이어 {i+1}:")
            label.pack(side=tk.LEFT, padx=5)
            entry = ttk.Entry(frame)
            entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
            self.player_name_entries.append(entry)

    def generate_schedule(self):
        try:
            self.players = [entry.get().strip() for entry in self.player_name_entries]
            if not all(self.players):
                messagebox.showerror("입력 오류", "모든 플레이어의 이름을 입력해주세요.")
                return

            self.date_str = self.dates_text.get("1.0", tk.END).strip()
            if not self.date_str:
                messagebox.showerror("입력 오류", "예약 날짜를 하나 이상 입력해주세요.")
                return

            reservations = []
            raw_dates = [d.strip() for d in re.split(r'[, ]+', self.date_str) if d.strip()]
            for item in raw_dates:
                parts = item.replace('.', '/').split('/')
                if len(parts) in [3, 4]:
                    date_part = '/'.join(parts[:3])
                    reserved_player = parts[3].strip() if len(parts) == 4 else None
                    if reserved_player and reserved_player not in self.players:
                        messagebox.showerror("입력 오류", f"예약자 '{reserved_player}'는(은) 플레이어 목록에 없습니다.")
                        return
                    reservations.append((date_part, reserved_player))
                else:
                    messagebox.showerror("입력 오류", f"날짜 형식이 잘못되었습니다: '{item}'. '월/일/시' 또는 '월/일/시/예약자' 형식으로 입력해주세요.")
                    return
            
            print(f"Debug: Reservations before sorting: {reservations}")
            reservations.sort(key=lambda x: tuple(map(int, x[0].split('/'))))
            print(f"Debug: Reservations after sorting: {reservations}")

            self.group_size = self.group_size_entry.get()
            group_size_int = int(self.group_size)
            if not 1 <= group_size_int <= len(self.players):
                messagebox.showerror("입력 오류", f"조별 인원은 1에서 {len(self.players)} 사이여야 합니다.")
                return

        except (ValueError, IndexError):
            messagebox.showerror("입력 오류", "입력 형식을 확인해주세요.")
            return

        schedule, play_counts = schedule_golf_groups(self.players, reservations, group_size_int)
        print(f"Debug: Generated schedule: {schedule}")

        result_str = """--- 최종 골프 조 편성 결과 ---
"""
        for date_str, group in schedule.items():
            print(f"Debug: Processing date_str: {date_str}, group: {group}")
            month, day, hour = map(int, date_str.split('/'))
            ampm = "오후" if 1 <= hour <= 6 or hour == 12 else "오전"
            result_str += f"[{month}월 {day}일 {ampm} {hour:02d}시]: {', '.join(group)}\n"

        player_schedules = collections.defaultdict(list)
        for date, group in schedule.items():
            for player in group:
                month, day, hour = map(int, date.split('/'))
                ampm = "오후" if 1 <= hour <= 6 or hour == 12 else "오전"
                player_schedules[player].append(f"{month}월 {day}일 {ampm} {hour:02d}시")

        result_str += """\n--- 플레이어별 참여 상세 정보 ---
"""
        sorted_players = sorted(play_counts.keys(), key=lambda p: (-play_counts[p], p))
        for player in sorted_players:
            count = play_counts[player]
            dates_participated = ", ".join(player_schedules[player])
            result_str += f"- {player}: {count}회 ({dates_participated})\n"

        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert(tk.END, result_str)
        self.result_text.config(state="disabled")
        self.save_button.config(state="normal")

    def save_to_txt(self):
        result_content = self.result_text.get("1.0", tk.END).strip()
        if not result_content:
            messagebox.showwarning("저장 오류", "저장할 결과가 없습니다. 먼저 조 편성을 생성해주세요.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("텍스트 문서", "*.txt"), ("모든 파일", "*.*")],
            title="결과를 텍스트 파일로 저장"
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"## 골프 조 편성 결과 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ##\n\n")
                f.write("""--- 입력 정보 ---
""")
                f.write(f"- 참여 인원: {self.num_players_entry.get()}명\n")
                f.write(f"- 플레이어: {', '.join(self.players)}\n")
                f.write(f"- 예약 날짜 원본: {self.date_str}\n")
                f.write(f"- 한 조 인원: {self.group_size}명\n\n")
                f.write("""--- 편성 결과 ---
""")
                f.write(result_content)
            
            messagebox.showinfo("저장 완료", f"결과가 다음 파일에 성공적으로 저장되었습니다:\n{filepath}")
        except Exception as e:
            messagebox.showerror("저장 실패", f"파일을 저장하는 중 오류가 발생했습니다:\n{e}")

    def save_input_data(self):
        input_data = {
            "num_players": self.num_players_entry.get(),
            "player_names": [entry.get().strip() for entry in self.player_name_entries],
            "dates_text": self.dates_text.get("1.0", tk.END).strip(),
            "group_size": self.group_size_entry.get()
        }
        try:
            with open("golf_scheduler_input.json", "w", encoding="utf-8") as f:
                json.dump(input_data, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("저장 완료", "입력 정보가 'golf_scheduler_input.json'에 저장되었습니다.")
        except Exception as e:
            messagebox.showerror("저장 실패", f"입력 정보를 저장하는 중 오류가 발생했습니다:\n{e}")

    def load_input_data(self):
        try:
            with open("golf_scheduler_input.json", "r", encoding="utf-8") as f:
                input_data = json.load(f)
            
            self.num_players_entry.delete(0, tk.END)
            self.num_players_entry.insert(0, input_data.get("num_players", "4"))
            self.update_player_entries() # Update player name entries based on loaded num_players

            # Populate player names
            loaded_player_names = input_data.get("player_names", [])
            for i, name in enumerate(loaded_player_names):
                if i < len(self.player_name_entries):
                    self.player_name_entries[i].delete(0, tk.END)
                    self.player_name_entries[i].insert(0, name)

            self.dates_text.delete("1.0", tk.END)
            self.dates_text.insert("1.0", input_data.get("dates_text", ""))

            self.group_size_entry.delete(0, tk.END)
            self.group_size_entry.insert(0, input_data.get("group_size", ""))

            messagebox.showinfo("불러오기 완료", "입력 정보가 성공적으로 불러와졌습니다.")

        except FileNotFoundError:
            # messagebox.showinfo("정보", "저장된 입력 정보 파일이 없습니다.")
            pass # No saved data, just proceed with defaults
        except Exception as e:
            messagebox.showerror("불러오기 실패", f"입력 정보를 불러오는 중 오류가 발생했습니다:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GolfSchedulerApp(root)
    app.load_input_data() # Call load_input_data on startup
    root.mainloop()