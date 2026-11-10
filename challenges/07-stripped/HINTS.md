# 07-stripped: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

No symbols. Start at `__libc_start_main`'s first argument to find `main`.

</details>

<details><summary>Level 2: Direction</summary>

The constants aren't immediates. They're loaded from `.data`.

</details>

<details><summary>Level 3: Near-spoiler</summary>

The check is linear modulo a number. Compute a modular inverse (`pow(a, -1, m)`) to go backwards.

</details>

