# 13-env-checks: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

It knows about gdb, LD_PRELOAD and its parent. Where would that information come from?

</details>

<details><summary>Level 2: Direction</summary>

Raw `syscall` instructions read `/proc/self/status`, the environment and the parent's `comm`.

</details>

<details><summary>Level 3: Near-spoiler</summary>

`strace` shows which files it opens. Then either patch each check's result or solve the key derivation statically.

</details>

