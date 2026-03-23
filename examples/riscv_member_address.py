"""
arc_dwarf 示例 - RISC-V ELF 结构体成员地址解析

演示如何使用 arch_info() 确认架构，再通过 get_member_address()
计算 RISC-V 目标上嵌套结构体成员的运行时物理地址。

arc_dwarf 通过 pyelftools 原生支持 RISC-V (RV32/RV64)，
无需额外配置：pointer_size 会自动从 ELF class 推导
（RV32 → 4 字节，RV64 → 8 字节）。

编译示例（需 RISC-V 工具链）：
  riscv64-unknown-elf-gcc -g -o firmware.elf main.c
"""

import sys
from pathlib import Path

# 支持未安装时从项目根目录直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from arc_dwarf import DwarfTypeExplorer

ELF_FILE = "firmware.elf"   # 替换为实际 RISC-V ELF 路径
VAR_NAME = "gConfig"         # 替换为实际全局变量名
TYPE_NAME = "Config_t"       # 替换为实际类型名
MEMBER_PATH = "param.value"  # 替换为实际成员路径，空字符串表示整个结构体


def main():
    with DwarfTypeExplorer(ELF_FILE) as ex:
        # 确认架构信息
        info = ex.arch_info()
        print(f"架构:         {info['machine']}")
        print(f"位宽:         {info['bits']} bit")
        print(f"字节序:       {info['endian']}")
        print(f"指针大小:     {info['pointer_size']} bytes")
        print()

        result = ex.get_member_address(
            var_name=VAR_NAME,
            member_path=MEMBER_PATH,
            type_name=TYPE_NAME,
        )

        print(f"变量名:       {result.var_name}")
        print(f"成员路径:     {result.member_path}")
        print(f"基地址:       0x{result.base_address:08X}")
        print(f"成员偏移:     0x{result.member_offset:04X} ({result.member_offset} bytes)")
        print(f"物理地址:     0x{result.address:08X}")
        print(f"成员类型:     {result.type_str}")
        print(f"成员大小:     {result.sizeof} bytes")


if __name__ == "__main__":
    main()
