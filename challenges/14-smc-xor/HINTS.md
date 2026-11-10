# 14-smc-xor: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

The function that checks your input disassembles as garbage.

</details>

<details><summary>Level 2: Direction</summary>

Look for an `mprotect` call followed by a loop that writes into `.text`.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Break after the decrypt loop and dump the function, or XOR the bytes yourself with the key in the loop.

</details>

