#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""arc-dwarf CLI: A2L & ELF 交互式查询工具 (物理地址提取 + DWARF 结构体展开)"""

from __future__ import annotations

import argparse
import sys

from .a2l_parser import A2lParser
from .dwarf_explorer import DwarfTypeExplorer
from .type_dumper import DumpOptions, TypeTreeDumper
from .textout import TextEmitter


def interactive_shell(a2l_path: str, elf_path: str) -> None:
    print("=" * 60)
    print("自动化标定工具链 - 交互式分析终端")
    print("=" * 60)

    # 1. 解析 A2L 文件，获取所有变量和类型
    print(f"\n[1/2] 正在解析 A2L 文件: {a2l_path} ...")
    try:
        a2l = A2lParser(a2l_path)
        a2l_vars = a2l.get_variables()
        a2l_dict = {v["name"]: v for v in a2l_vars}
        print(f"      成功提取 {len(a2l_vars)} 个测量/标定变量定义。")
    except Exception as e:
        print(f"      解析 A2L 失败: {e}")
        return

    # 2. 预加载 ELF 与 DWARF
    print(f"[2/2] 正在加载 ELF 符号表与 DWARF 树: {elf_path} ...")
    try:
        ex = DwarfTypeExplorer(elf_path)
        ex.open()
        dumper = TypeTreeDumper(ex)
        dumper_opts = DumpOptions(max_depth=5, recursive=True)
        print("      ELF 文件加载完成。")
    except Exception as e:
        print(f"      解析 ELF 失败: {e}")
        return

    print("\n" + "=" * 60)
    print("提示：在提示符处输入 'q' 或 'exit' 退出程序。")
    print("      输入 'list' 可以查看 A2L 中所有的变量名。")
    print("=" * 60)

    # 3. 开启交互式循环
    try:
        while True:
            print("\n" + "-" * 50)

            try:
                var_name = input("请输入待测变量名 (e.g. gRspCfg): ").strip()
            except EOFError:
                break

            if var_name.lower() in ("q", "exit", "quit"):
                break

            if var_name.lower() == "list":
                print(f"\n   [A2L] 当前存在的所有变量列表 ({len(a2l_vars)} 个):")
                for v in a2l_vars[:50]:
                    print(f"      - {v['name']:<25} ({v['type']})")
                if len(a2l_vars) > 50:
                    print("      ... (篇幅省略)")
                continue

            if not var_name:
                continue

            # 查找 A2L 信息
            var_info = a2l_dict.get(var_name)
            recommended_type = ""
            if var_info:
                recommended_type = var_info["type"]
                print(f"   [A2L] 找到声明 -> Block: {var_info['block']}, A2L 绑定类型: {recommended_type}")
            else:
                print(f"   [A2L] 未在 A2L 文件中找到变量 '{var_name}'")

            # 获取实际物理地址
            addr_info = ex.get_variable_info(var_name)
            if addr_info:
                addr, size = addr_info
                print(f"   [ELF] 物理真实地址 = 0x{addr:08X} (占用大小: {size} Bytes)")
            else:
                print("   [ELF] 未在目标 ELF 的符号表中找到该全局变量！")

            # 输入指定的结构体类型并展开
            prompt_str = (
                f"请输入要展开的数据类型名 [回车默认: {recommended_type}]: "
                if recommended_type
                else "请输入要展开的数据类型名: "
            )
            try:
                target_type = input(prompt_str).strip()
            except EOFError:
                break

            if target_type.lower() in ("q", "exit", "quit"):
                break

            if not target_type and recommended_type:
                target_type = recommended_type

            if not target_type:
                print("   未输入有效的数据类型，跳过结构体展开。")
                continue

            print(f"   [DWARF] 正在查询并递归展开结构体树: {target_type} ...\n")
            try:
                emitter = TextEmitter(stream=sys.stdout)
                dumper.dump(target_type, options=dumper_opts, emitter=emitter)
            except RuntimeError as e:
                print(f"   查询失败：{e}")
            except Exception as e:
                print(f"   解析 DWARF 类型时发生错误: {e}")

    except KeyboardInterrupt:
        pass
    finally:
        print("\n\n接收到退出指令，正在清理系统资源...")
        ex.close()
        print("退出成功。")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A2L & ELF 交互式查询工具 (物理地址提取 + DWARF 结构体展开)",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("a2l", help="A2L 文件路径 (例如: Langcang_bpm_solution.a2l)")
    parser.add_argument("elf", help="包含 DWARF 调试信息的 ELF 文件路径 (例如: CPD_BPM_App_Core1.elf)")

    args = parser.parse_args()
    interactive_shell(args.a2l, args.elf)


if __name__ == "__main__":
    main()
