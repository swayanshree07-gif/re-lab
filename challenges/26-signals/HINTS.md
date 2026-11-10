# 26-signals: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

It crashes on purpose. Those faults are the control flow.

</details>

<details><summary>Level 2: Direction</summary>

Handlers for SIGSEGV, SIGFPE and SIGILL do the real work and change the saved context.

</details>

<details><summary>Level 3: Near-spoiler</summary>

`strace` shows the signal sequence. In gdb use `handle SIGSEGV nostop noprint pass`, then read each handler.

</details>

