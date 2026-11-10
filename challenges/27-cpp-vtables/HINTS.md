# 27-cpp-vtables: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

Indirect `call *0x10(%rax)`: which function is that?

</details>

<details><summary>Level 2: Direction</summary>

`nm -C` lists the vtables. A factory picks a class per stage from a params table.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Read the params table, work out which `transform` each stage uses, and invert them one by one.

</details>

