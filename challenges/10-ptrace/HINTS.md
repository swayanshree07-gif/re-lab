# 10-ptrace: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

Under gdb the program behaves differently, and it doesn't tell you.

</details>

<details><summary>Level 2: Direction</summary>

Something runs before `main`. Check `.init_array`.

</details>

<details><summary>Level 3: Near-spoiler</summary>

`PTRACE_TRACEME` fails when you're already traced. Patch the result, use `catch syscall ptrace` and set `$rax`, or solve it statically.

</details>

