"""Tkinter offline-only UI. Launch: python -m flowpilot_universal.gui.

This module imports without creating a window, so headless CI can validate it.
"""
from __future__ import annotations
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from .session import backup_history, recent_history, run_session, verify_history_entry


class App:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("FlowPilot Universal | 로컬 파일 납품 검수")
        self.master.geometry("890x670")
        self.root = tk.StringVar()
        self.manifest = tk.StringVar()
        self.output = tk.StringVar()
        self.consent = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="대기 · 읽기 전용 / 외부 전송 없음")
        self.events: queue.Queue = queue.Queue()
        self.stop = threading.Event()
        self.worker: threading.Thread | None = None
        self.history_rows: list[dict] = []
        main = ttk.Frame(master, padding=18)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text="FlowPilot Universal", font=("", 20, "bold")).pack(anchor="w")
        ttk.Label(main, text="승인된 폴더만 스캔합니다. 원본은 수정하지 않으며 결과와 기록은 선택한 외부 폴더에 저장합니다.",
                  wraplength=820).pack(anchor="w", pady=(0, 12))
        for title, var, kind in (
            ("검사할 폴더 (PC·USB·OS에 연결된 SMB)", self.root, "folder"),
            ("납품 요구사항 JSON (schema v1)", self.manifest, "file"),
            ("보고서·이력 저장 폴더 (검사 폴더 외부)", self.output, "folder")
        ):
            ttk.Label(main, text=title).pack(anchor="w", pady=(6, 1))
            bar = ttk.Frame(main)
            bar.pack(fill="x")
            ttk.Entry(bar, textvariable=var).pack(side="left", fill="x", expand=True)
            action = (lambda v=var: v.set(filedialog.askdirectory() or v.get())) if kind == "folder" else (
                lambda v=var: v.set(filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*")]) or v.get()))
            ttk.Button(bar, text="찾기", command=action).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(main, text="이 폴더에 대한 합법적 읽기 권한이 있으며 해당 범위의 검사를 승인합니다.",
                        variable=self.consent).pack(anchor="w", pady=(18, 12))
        actions = ttk.Frame(main)
        actions.pack(fill="x")
        self.start_button = ttk.Button(actions, text="새 검수 시작 / 안전한 처음부터 재검사", command=self.start)
        self.start_button.pack(side="left")
        self.cancel_button = ttk.Button(actions, text="취소 요청", command=self.stop.set, state="disabled")
        self.cancel_button.pack(side="left", padx=8)
        ttk.Button(actions, text="저장된 검수 이력", command=self.show_history).pack(side="left")
        ttk.Button(actions, text="이력 백업", command=self.backup).pack(side="left", padx=(8, 0))
        ttk.Button(actions, text="선택 이력 검증", command=self.verify_selected_history).pack(side="left", padx=(8, 0))
        ttk.Label(main, textvariable=self.status, wraplength=820).pack(anchor="w", pady=(16, 8))
        ttk.Label(main, text="검사 이력 (현재 PC의 선택한 저장 폴더에만 보관)").pack(anchor="w")
        frame = ttk.Frame(main)
        frame.pack(fill="both", expand=True)
        self.history = tk.Listbox(frame, height=12, activestyle="none")
        self.history.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, command=self.history.yview)
        scrollbar.pack(side="right", fill="y")
        self.history.configure(yscrollcommand=scrollbar.set)
        ttk.Label(main, text="취소는 현재 파일 읽기 완료 후 처리될 수 있습니다. '재검사'는 기존 해시를 재사용하지 않는 완전 새 검사입니다.",
                  wraplength=820).pack(anchor="w", pady=(10, 0))
        self.master.after(100, self.drain)

    def start(self):
        if self.worker is not None and self.worker.is_alive():
            return
        if not self.consent.get():
            messagebox.showerror("승인 필요", "검사할 폴더에 대한 권한과 범위를 확인해 주세요.")
            return
        values = [self.root.get().strip(), self.manifest.get().strip(), self.output.get().strip()]
        if not all(values):
            messagebox.showerror("입력 필요", "검사 폴더, 요구사항 JSON, 보고서 폴더를 지정해 주세요.")
            return
        self.stop.clear()
        self.start_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        self.status.set("검사 중 · 원본 읽기 전용")
        self.worker = threading.Thread(target=self.work, args=tuple(map(Path, values)), daemon=True)
        self.worker.start()

    def work(self, root, manifest, output):
        try:
            result = run_session(root, manifest, output, consent=True, cancel=self.stop.is_set,
                                 progress=lambda count, bytes_seen: self.events.put(("progress", count, bytes_seen)))
            self.events.put(("done", result))
        except Exception as exc:
            self.events.put(("error", f"{type(exc).__name__}: {exc}"))

    def drain(self):
        try:
            while True:
                kind, *data = self.events.get_nowait()
                if kind == "progress":
                    count, nbytes = data
                    self.status.set(f"검사 중: {count}개 파일, {nbytes:,}바이트 읽음")
                elif kind == "done":
                    result = data[0]
                    self.start_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")
                    self.status.set(f"{result.status} · {result.scanned}개 · 이슈 {result.issues}개 · {result.json_path}")
                    self.show_history(silent=True)
                elif kind == "error":
                    self.start_button.configure(state="normal")
                    self.cancel_button.configure(state="disabled")
                    self.status.set("HOLD · " + data[0])
                    messagebox.showerror("검수 보류", data[0])
        except queue.Empty:
            pass
        self.master.after(100, self.drain)

    def backup(self):
        try:
            path = backup_history(Path(self.output.get().strip()))
            messagebox.showinfo("백업 완료", "새 SQLite 백업 생성: " + str(path))
        except Exception as exc:
            messagebox.showerror("백업 보류", str(exc))

    def verify_selected_history(self):
        try:
            selected = self.history.curselection()
            if not selected or selected[0] >= len(self.history_rows):
                raise ValueError("먼저 검증할 이력 한 건을 선택해 주세요.")
            session_id = self.history_rows[selected[0]]["session_id"]
            verified = verify_history_entry(Path(self.output.get().strip()), session_id)
            messagebox.showinfo("로컬 보고서 무결성", "JSON·HTML 검증 통과: " + verified["sha256"])
        except Exception as exc:
            messagebox.showerror("이력 검증 보류", str(exc))

    def show_history(self, silent=False):
        try:
            output = Path(self.output.get().strip())
            rows = recent_history(output)
            self.history_rows = rows
            self.history.delete(0, tk.END)
            for item in rows:
                self.history.insert(tk.END, f"{item['created_utc']} | {item['status']} | "
                                         f"{item['scanned']} files / {item['issues']} issues | {item['json_path']}")
        except Exception as exc:
            if not silent:
                messagebox.showerror("이력 조회 보류", str(exc))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
