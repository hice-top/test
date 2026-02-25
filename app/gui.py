#!/usr/bin/env python3
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from app.deployer import Deployer, create_project_from_sample
from tools.validate_manifest import ValidationError, validate_manifest


class InstallerGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Windows 一键安装器（GUI 原型）")
        self.geometry("980x700")

        self.manifest_var = tk.StringVar(value="runtime/manifest.json")
        self.runtime_var = tk.StringVar(value="runtime")
        self.resume_var = tk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill="both", expand=True)

        top = ttk.LabelFrame(root, text="基础配置", padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Manifest 文件").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.manifest_var, width=90).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(top, text="浏览", command=self._pick_manifest).grid(row=0, column=2)

        ttk.Label(top, text="Runtime 目录").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(top, textvariable=self.runtime_var, width=90).grid(row=1, column=1, sticky="ew", padx=8, pady=(8, 0))
        ttk.Button(top, text="浏览", command=self._pick_runtime).grid(row=1, column=2, pady=(8, 0))

        top.columnconfigure(1, weight=1)

        btns = ttk.Frame(root)
        btns.pack(fill="x", pady=12)
        ttk.Button(btns, text="1) 从示例初始化 Manifest", command=self._init_manifest).pack(side="left")
        ttk.Button(btns, text="2) 校验 Manifest", command=self._validate_manifest).pack(side="left", padx=8)
        ttk.Button(btns, text="3) 执行安装流程", command=self._install).pack(side="left")
        ttk.Checkbutton(btns, text="失败后断点续跑（--resume）", variable=self.resume_var).pack(side="left", padx=16)

        pane = ttk.PanedWindow(root, orient="horizontal")
        pane.pack(fill="both", expand=True)

        left = ttk.LabelFrame(pane, text="Manifest 编辑", padding=8)
        right = ttk.LabelFrame(pane, text="运行日志 / 结果", padding=8)
        pane.add(left, weight=2)
        pane.add(right, weight=3)

        self.manifest_text = tk.Text(left, wrap="none", height=30)
        self.manifest_text.pack(fill="both", expand=True)

        self.log_text = tk.Text(right, wrap="word", height=30)
        self.log_text.pack(fill="both", expand=True)

        bar = ttk.Frame(root)
        bar.pack(fill="x", pady=(8, 0))
        ttk.Button(bar, text="加载 Manifest 到编辑器", command=self._load_manifest_to_editor).pack(side="left")
        ttk.Button(bar, text="保存编辑器内容到 Manifest", command=self._save_editor_to_manifest).pack(side="left", padx=8)
        ttk.Button(bar, text="打开 runtime/report.json", command=self._open_report).pack(side="left")

    def _log(self, message: str) -> None:
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

    def _pick_manifest(self) -> None:
        p = filedialog.askopenfilename(title="选择 Manifest", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if p:
            self.manifest_var.set(p)

    def _pick_runtime(self) -> None:
        p = filedialog.askdirectory(title="选择 Runtime 目录")
        if p:
            self.runtime_var.set(p)

    def _manifest_path(self) -> Path:
        return Path(self.manifest_var.get()).expanduser()

    def _runtime_path(self) -> Path:
        return Path(self.runtime_var.get()).expanduser()

    def _init_manifest(self) -> None:
        try:
            path = create_project_from_sample(self._manifest_path())
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("初始化失败", str(exc))
            return
        self._log(f"已生成 Manifest: {path}")
        self._load_manifest_to_editor()

    def _validate_manifest(self) -> None:
        p = self._manifest_path()
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            validate_manifest(data)
        except FileNotFoundError:
            messagebox.showerror("校验失败", f"文件不存在: {p}")
            return
        except (json.JSONDecodeError, ValidationError) as exc:
            messagebox.showerror("校验失败", str(exc))
            self._log(f"Manifest 校验失败: {exc}")
            return

        self._log("Manifest 校验通过")
        messagebox.showinfo("校验成功", "Manifest VALID")

    def _install(self) -> None:
        manifest = self._manifest_path()
        runtime = self._runtime_path()
        try:
            engine = Deployer.from_file(manifest, runtime)
            report = engine.run(resume=self.resume_var.get())
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("安装失败", str(exc))
            self._log(f"安装失败: {exc}")
            return

        failed = [s for s in report["steps"] if s["status"] == "failed"]
        self._log(f"安装完成，步骤={len(report['steps'])}，失败={len(failed)}")
        self._log(f"报告位置: {runtime / 'report.json'}")
        if failed:
            messagebox.showwarning("安装完成", "存在失败步骤，请检查日志")
        else:
            messagebox.showinfo("安装完成", "部署流程执行成功")

    def _load_manifest_to_editor(self) -> None:
        p = self._manifest_path()
        try:
            text = p.read_text(encoding="utf-8")
        except FileNotFoundError:
            messagebox.showerror("加载失败", f"文件不存在: {p}")
            return
        self.manifest_text.delete("1.0", "end")
        self.manifest_text.insert("1.0", text)
        self._log(f"已加载 Manifest: {p}")

    def _save_editor_to_manifest(self) -> None:
        p = self._manifest_path()
        content = self.manifest_text.get("1.0", "end").strip()
        if not content:
            messagebox.showerror("保存失败", "编辑器内容为空")
            return
        try:
            json.loads(content)
        except json.JSONDecodeError as exc:
            messagebox.showerror("保存失败", f"JSON 格式错误: {exc}")
            return

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content + "\n", encoding="utf-8")
        self._log(f"已保存 Manifest: {p}")

    def _open_report(self) -> None:
        report = self._runtime_path() / "report.json"
        if not report.exists():
            messagebox.showwarning("提示", f"报告不存在: {report}")
            return
        text = report.read_text(encoding="utf-8")
        self.log_text.insert("end", "\n===== report.json =====\n")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")


def main() -> int:
    app = InstallerGUI()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
