# 16-cff-manual: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

Every block returns to one big dispatcher. Find the state variable.

</details>

<details><summary>Level 2: Direction</summary>

Each block sets the next state by XORing in a constant. Track the state values to rebuild the real edges.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Log the state at the dispatcher with a gdb breakpoint script, drop the junk states that never run, and read the linear check.

</details>

