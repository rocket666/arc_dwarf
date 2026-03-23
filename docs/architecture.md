# 架构设计

## 概览

`arc_dwarf` 是一个面向嵌入式汽车电子领域的工具库，用于将 ELF 二进制文件中的 DWARF 调试信息与 A2L 标定配置文件进行关联分析。

## 模块关系

```
A2lParser ──────────┐
                    ├──▶ CLI (交互式工具)
DwarfTypeExplorer ──┤
       │            │
       ▼            │
  TypeTreeDumper ───┘
       │
       ▼
  TextEmitter (输出格式化)
```

## 核心模块

### `dwarf_explorer` — DWARF 解析引擎

负责打开 ELF 文件、索引 DWARF 调试信息、解析类型定义和成员偏移。
使用 `pyelftools` 作为底层解析库。

### `a2l_parser` — A2L 文件解析

基于正则表达式提取 ASAP2 标定文件中的变量定义，支持 MEASUREMENT、CHARACTERISTIC、INSTANCE、TYPEDEF_STRUCTURE 四种块类型。

### `type_dumper` — 类型可视化

将 DWARF 类型信息渲染为对齐的文本表格或 JSON 树结构，支持递归展开、深度限制和选择性过滤。

### `model` — 数据模型

定义 `Member` 数据类，表示结构体/联合体的成员信息。

### `textout` — 文本输出

`TextEmitter` 类提供带缩进支持的文本累积器，可流式输出到文件或内存缓冲。

### `formatting` — 格式化工具

提供十六进制和字节数的格式化辅助函数。

## 支持的目标架构

底层解析依赖 `pyelftools`，凡是 `pyelftools` 支持的 ELF 架构均可直接使用，无需额外配置。已验证或明确支持的架构包括：

| 架构 | ELF `e_machine` | 位宽 | 备注 |
|---|---|---|---|
| ARC (DesignWare) | `EM_ARC` | 32 | 原始目标平台 |
| ARM / Thumb | `EM_ARM` | 32 | 含 Cortex-M 系列 |
| AArch64 | `EM_AARCH64` | 64 | |
| RISC-V | `EM_RISCV` | 32 / 64 | RV32 / RV64 均支持 |
| x86 | `EM_386` | 32 | |
| x86-64 | `EM_X86_64` | 64 | |
| MIPS | `EM_MIPS` | 32 / 64 | |

`pointer_size` 由 ELF class 自动推导（32-bit ELF → 4 字节，64-bit ELF → 8 字节）。
可通过 `DwarfTypeExplorer.arch_info()` 在运行时确认目标架构信息。
