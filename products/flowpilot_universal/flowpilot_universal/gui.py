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
from .manifest_editor import create_approved_manifest, render_manifest


class App:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.title("FlowPilot Universal | 로컬 파일 납품 검수")
        self.master.geometry("890x670")
        self.root = tk.StringVar()
        self.manifest = tk.StringVar()
        self.output = tk.StringVar()
        self.consent = tk.BooleanVar(value=False)
        self.resume = tk.BooleanVar(value=False)
        self.pdf = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="대기 · 읽기 전용 / 외부 전송 없음")
        self.events: queue.Queue = queue.Queue()
        self.stop = threading.Event()
        self.worker: threading.Thread | None = None
        self.history_rows: list[dict] = []
        self.editor_window: tk.Toplevel | None = None
        self.editor_title: tk.StringVar | None = None
        self.editor_approval: tk.BooleanVar | None = None
        self.editor_text: tk.Text | None = None
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
        ttk.Button(main, text="납품 요구사항 JSON 직접 작성", command=self.open_template_editor).pack(anchor="w", pady=(5, 0))
        ttk.Checkbutton(main, text="이 폴더에 대한 합법적 읽기 권한이 있으며 해당 범위의 검사를 승인합니다.",
                        variable=self.consent).pack(anchor="w", pady=(18, 6))
        ttk.Checkbutton(main, text="부분 이어하기 (이전 해시는 검토용으로만 재사용, READY 판정은 새 전체 검사 필요)",
                        variable=self.resume).pack(anchor="w", pady=(0, 4))
        ttk.Checkbutton(main, text="한국어 PDF 보고서 추가 생성 (ReportLab 및 OS 한국어 TTF 필요)",
                        variable=self.pdf).pack(anchor="w", pady=(0, 12))
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
        ttk.Label(main, text="이어하기는 완료 파일의 메타데이터·SHA를 검토용으로 재사용하므로 NEEDS_REVIEW입니다. 체크 해제 후 전체 재해시해야 READY입니다.",
                  wraplength=820).pack(anchor="w", pady=(10, 0))
        self.master.after(100, self.drain)

    def open_template_editor(self):
        """Independent checklist only; never derive requirements from scanned files."""
        if self.editor_window is not None and self.editor_window.winfo_exists():
            self.editor_window.lift()
            return
        child = tk.Toplevel(self.master)
        child.title("납품 요구사항 작성 | 검증 전 사용자 승인 필수")
        child.geometry("770x520")
        self.editor_window = child
        self.editor_title = tk.StringVar(master=child, value="납품 파일 검수")
        self.editor_approval = tk.BooleanVar(master=child, value=False)
        frame = ttk.Frame(child, padding=15)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="독립 계약·체크리스트에서 필수 파일을 입력하세요. 스캔된 폴더에서 요구사항을 자동 추출하지 않습니다.",
                  wraplength=740).pack(anchor="w")
        ttk.Label(frame, text="한 줄에 파일 상대경로 1개, 필요하면 TAB 뒤에 SHA-256 64자리. 예: docs/readme.pdf",
                  wraplength=740).pack(anchor="w", pady=(7, 9))
        ttk.Entry(frame, textvariable=self.editor_title).pack(fill="x", pady=(0, 10))
        edit = tk.Text(frame, height=15, wrap="none", undo=True)
        edit.pack(fill="both", expand=True)
        self.editor_text = edit
        ttk.Checkbutton(frame, variable=self.editor_approval,
                        text="스캔 원본과 독립된 계약/납품조건 목록을 직접 확인했고, 이 요구사항을 승인합니다."
                        ).pack(anchor="w", pady=(12, 9))
        ttk.Button(frame, text="승인한 요구사항을 새 JSON으로 저장 (덮어쓰기 금지)",
                   command=self.save_template_editor).pack(anchor="w")

    def save_template_editor(self):
        if (self.editor_window is None or not self.editor_window.winfo_exists()
                or self.editor_text is None or self.editor_title is None
                or self.editor_approval is None):
            return
        try:
            raw_root = self.root.get().strip()
            if not raw_root:
                raise ValueError("먼저 검사할 권한이 있는 원본 폴더를 선택하세요.")
            title = self.editor_title.get()
            lines = self.editor_text.get("1.0", "end-1c")
            approval = self.editor_approval.get()
            # Validate and request explicit approval BEFORE showing any save dialog.
            render_manifest(title, lines, approved=approval)
            target = filedialog.asksaveasfilename(
                parent=self.editor_window, title="새 납품 요구사항 JSON 저장",
                defaultextension=".json", filetypes=[("JSON", "*.json")])
            if not target:
                return
            created = create_approved_manifest(title, lines, Path(target), Path(raw_root), approved=approval)
            self.manifest.set(str(created))
            messagebox.showinfo("새 검수 요구사항 저장", "사용자 승인 JSON 저장 완료: " + str(created))
            self.editor_window.destroy()
            self.editor_window = None
        except Exception as exc:
            messagebox.showerror("검수 요구사항 저장 보류", str(exc))

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
        self.worker = threading.Thread(target=self.work,
                                       args=(*tuple(map(Path, values)), self.resume.get(), self.pdf.get()), daemon=True)
        self.worker.start()

    def work(self, root, manifest, output, resume=False, pdf=False):
        try:
            result = run_session(root, manifest, output, consent=True, resume=resume, pdf=pdf,
                                 cancel=self.stop.is_set,
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
                    extra = f" · PDF {result.pdf_path}" if result.pdf_path else ""
                    self.status.set(f"{result.status} · {result.scanned}개 · 이슈 {result.issues}개 · {result.json_path}{extra}")
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
            messagebox.showinfo("로컬 보고서 무결성", f"검증된 보고서 {verified['reports_verified']}개 (JSON/HTML/PDF 선택): " + verified["sha256"])
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
