"""
arc_dwarf 示例 - 获取结构体成员物理地址

演示如何使用 get_member_address() 沿点分路径计算
嵌套结构体成员的运行时物理地址。
"""

import sys
from pathlib import Path

# 支持未安装时从项目根目录直接运行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from arc_dwarf import DwarfTypeExplorer

ELF_FILE = "CPD_BPM_App_Core1.elf"
VAR_NAME = "gRadioCfg"
TYPE_NAME = "Radio_Params_t"
MEMBER_PATH = ""


def main():
    with DwarfTypeExplorer(ELF_FILE) as ex:
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
