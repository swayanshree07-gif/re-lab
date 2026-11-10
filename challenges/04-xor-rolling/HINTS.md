# 04-xor-rolling: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

The key is longer than one byte this time. Look at the loop index arithmetic.

</details>

<details><summary>Level 2: Direction</summary>

The index is reduced modulo a small number, and there's an add that depends on the previous byte.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Undo it in reverse order: subtract the chained add first, then XOR with key[i % len].

</details>

