# 🖥️ NASM Linux x86_64 on Windows (Autograder & Runner)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, robust Windows application designed for students and developers to seamlessly write, compile, and evaluate **Linux x86_64 assembly code (NASM)** directly on Windows. No need to install heavy Virtual Machines or configure WSL.

## 🚀 Why This Exists?
Writing Linux assembly (`elf64`) on a Windows machine is historically painful. This tool bridges the gap by providing a direct client/evaluator that compiles NASM code, links it via `ld`, and runs rigorous test cases in an isolated Linux environment (Backend). 

Perfect for university assignments, OS courses, and architecture labs.

## 📥 Download & Installation
You don't need Python or any dependencies to run this.
1. Go to the **Releases** page on the right side of this repository.
2. Download the latest `Autograder_Windows.exe`.
3. Run the executable and start coding!

## ✨ Core Features & Strict Evaluation System

This is not just a compiler; it is an **Asynchronous Anti-Deadlock Autograder**. 

* **⚙️ Seamless NASM Compilation:** Automatically handles `nasm -f elf64` and `ld` linking.
* **🛡️ Zombie-Proof Execution:** The backend utilizes fully asynchronous evaluation (`asyncio`). It strictly isolates processes to prevent ghost connections and memory leaks.
* **⏱️ Strict Timeout Management:** * **Compile Timeout:** Hardware-locked to **4.0 seconds** to prevent infinite macro loops during compilation.
  * **Runtime Timeout:** Each individual test case has an isolated timer (e.g., **2.0 seconds**). If an infinite loop is detected, the process is instantly killed at the kernel level (`SIGKILL`), ensuring the queue never freezes.
* **🧪 JSON-Based Test Cases:** Evaluates student code against structured inputs/outputs via a `tests.json` file.
* **🧱 Text Bomb Protection:** Hard limit on source code size (50KB) to prevent DoS attacks on the evaluator.

## 🛠️ How to Use (For Instructors & Students)

### 1. Structuring `tests.json`
Instructors can define test cases using a simple JSON format. The evaluator feeds the `input` to the compiled binary via standard input (STDIN) and strictly matches the `expected` output.

```json
{
  "Question_1_Addition": [
    {
      "input": "10 20",
      "expected": "30",
      "timeout": 2.0
    },
    {
      "input": "5000 5000",
      "expected": "10000",
      "timeout": 3.5
    }
  ]
}


```

### 2. Evaluation

Click **Evaluate**. The system will securely transmit the code, compile it, run it against all test cases, and return a clean console summary of passed/failed tests.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Keywords (for search engines):** Write Linux assembly on Windows, NASM x86_64 Windows IDE, evaluate linux assembly, assembly autograder, run elf64 on Windows.

```
