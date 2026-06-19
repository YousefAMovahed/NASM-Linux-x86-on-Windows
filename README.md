# 🖥️ NASM Linux x86_64 on Windows (Autograder & Runner)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, robust Windows application designed for students and educators to seamlessly write, compile, and evaluate **Linux x86_64 assembly code (NASM)** directly on Windows. No heavy Virtual Machines, Docker containers, or WSL configurations required.

---

## 🚀 Why This Exists?
Writing and testing Linux assembly (`elf64`) on a Windows machine is historically painful for students. This tool bridges the gap by providing a standalone, zero-dependency IDE/Evaluator. It compiles x86_64 NASM code locally, links it via `ld.lld`, and runs rigorous test cases in an isolated emulated Linux environment directly on bare Windows.

Perfect for university grading systems, Operating Systems (OS) courses, and computer architecture labs.

---

## 📥 Download & Installation

You do not need Python, NASM, or any external packages installed on your PC. Everything is statically compiled.

* **Primary Download:** Go to the [GitHub Releases](../../releases/latest) page and download `Autograder_Windows.exe`.
* **Alternative Mirror (High Speed):** [Download from Secure Storage Mirror](https://my.files.ir/drive/s/Qdr4WQtq6d4vrOWkvlffkAhi8IJIrG)

---

## ✨ Core Features & Strict Production-Grade Architecture

This is not just a basic compiler script; it is a battle-hardened, **Asynchronous Anti-Deadlock Autograder**.

* **🧰 Built-in Linux Emulation:** Bundles a lightweight Linux kernel emulator (`Blink`) alongside LLVM's `ld.lld` and `NASM` for seamless offline compilation.
* **🔒 Encrypted Test Architecture (Anti-Cheat):** Supports locked test matrices. Instructors can bundle hidden test cases into encrypted `.dat` structures using AES-based `Fernet` cryptography, preventing students from hardcoding outputs.
* **🛡️ Zombie-Proof Execution Engine:** The runner utilizes fully asynchronous sub-processes (`asyncio`). It creates isolated process groups via `os.setsid()` to guarantee that orphaned or background child processes are never left leaking memory.
* **⏱️ Dual-Layer Timeout Management:**
  * **Compile Timeout:** Hard-locked to **4.0 seconds** to instantly terminate infinite macro loops during assembly compilation.
  * **Runtime Timeout:** Every single test case runs on an independent, isolated micro-timer (e.g., **2.0 seconds**). If an infinite loop or deadlock occurs, the binary is violently executed at the kernel level (`SIGKILL`), forcing the queue to move forward safely.
* **🧱 Security Guardrails:** Includes strict text-bomb and DoS protection with a maximum source code submission buffer size of 50KB.

---

## 🛠️ Educator Guide: Creating Encrypted Tests

Instructors can use the built-in utility script (`test_builder.py`) found in the `utils/` directory to generate tamper-proof test suites for assignments.

### 1. Compile the Test Matrix
Run the utility to serialize and encrypt your test inputs/expected outputs:

```python
# Save your cases in utils/test_builder.py and run it
test_cases = [
    {"input": "radar\n", "expected_output": "yes"},
    {"input": "hello\n", "expected_output": "no"}
]

```

### 2. Distribute the Asset

The script outputs an encrypted payload (e.g., `hw1_palindrome.dat`). Simply upload this single `.dat` file to your LMS (e.g., Moodle/Canvas). Students load this file into their Windows app to test their assembly code locally without seeing the raw evaluation keys!

---

## 🧪 Student Guide: Sample Assembly Structure

Students can load the `examples/template.asm` file. Ensure your entry points use the standard Linux x86_64 system call interface (`syscall` via `rax`), not the old 32-bit `int 0x80` system interrupts.

Example structure for exiting a program cleanly:

```assembly
section .text
    global _start

_start:
    mov rax, 60         ; sys_exit system call ID
    mov rdi, 0          ; exit return code 0
    syscall

```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

---

**Keywords (for global search engines):** Write Linux assembly on Windows, NASM x86_64 Windows IDE, evaluate linux assembly offline, assembly autograder, run elf64 on Windows without WSL, University of Tehran Computer Engineering.

