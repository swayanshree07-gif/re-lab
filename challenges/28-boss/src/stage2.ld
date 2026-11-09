SECTIONS {
  . = 0;
  .text : { *(.text.entry) *(.text*) *(.rodata*) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) *(.data*) *(.bss*) }
}
