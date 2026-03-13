#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
arc_dwarf 示例 - 交互式标定工具

用法:
    python interactive_tool.py <A2L文件路径> <ELF文件路径>

示例:
    python interactive_tool.py Langcang_bpm_solution.a2l CPD_BPM_App_Core1.elf
"""

from arc_dwarf.cli import main

if __name__ == "__main__":
    main()
