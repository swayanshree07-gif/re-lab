# 21-packed: hints

Open one level at a time. Level 3 is close to a spoiler.

<details><summary>Level 1: Nudge</summary>

Very little code, a large high-entropy blob, and an `mmap`.

</details>

<details><summary>Level 2: Direction</summary>

Two steps: an XOR keystream from an LCG, then LZ-style decompression into an executable page.

</details>

<details><summary>Level 3: Near-spoiler</summary>

Break where it jumps into the mmap page and dump it, or write a static unpacker. Then the inner check is easy.

</details>

