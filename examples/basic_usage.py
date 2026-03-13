"""
arc_dwarf 示例 - 基础用法

演示如何使用 DwarfTypeExplorer 进行 ELF/DWARF 类型解析，
以及使用 A2lParser 解析 A2L 标定文件。
"""

from arc_dwarf import A2lParser, DwarfTypeExplorer, TypeTreeDumper, DumpOptions

# ---- 示例 1: DWARF 类型树展开 ----

with DwarfTypeExplorer("CPD_BPM_App_Core1.elf") as ex:
    dumper = TypeTreeDumper(ex)
    out = dumper.dump("Rsp_Params_t", options=DumpOptions(max_depth=6, recursive=True))
    text = out.text()          # 一整个字符串
    lines = out.lines()        # list[str]
    # print(text)


# ---- 示例 2: 获取变量物理地址 ----

with DwarfTypeExplorer("CPD_BPM_App_Core1.elf") as ex:
    var_info = ex.get_variable_info("gRspCfg")
    if var_info is None:
        print(f"错误：在符号表中未找到变量 gRspCfg")
    else:
        addr, size = var_info
        print(f"找到变量 gRspCfg:")
        print(f"   起始地址 : 0x{addr:08X}")
        print(f"   符号大小 : {size} bytes\n")


# ---- 示例 3: A2L 变量解析 ----

def sync_a2l_var(a2l_path: str):
    print(f"[{a2l_path}] 开始解析 A2L 变量...")

    a2l = A2lParser(a2l_path)
    a2l_vars = a2l.get_variables()
    print(f"在 A2L 中找到 {len(a2l_vars)} 个变量定义。\n")
    print(a2l_vars)


if __name__ == "__main__":
    A2L_FILE = "Langcang_bpm_solution.a2l"
    sync_a2l_var(A2L_FILE)
