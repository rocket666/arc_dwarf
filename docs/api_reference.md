# API 参考

## `DwarfTypeExplorer`

ELF/DWARF 解析引擎，支持上下文管理器协议。

### 构造函数

```python
DwarfTypeExplorer(elf_path: str)
```

### 方法

- `open()` — 打开 ELF 文件并索引 DWARF 类型信息
- `close()` — 关闭文件句柄
- `find_type_die(type_name: str)` — 根据类型名查找 DWARF DIE
- `parse_struct_or_union_members(die)` — 解析结构体/联合体成员列表
- `type_byte_size(die)` — 计算类型字节大小
- `type_display_name(die)` — 获取类型可读名称
- `get_variable_info(var_name: str)` — 从符号表查找变量地址和大小，返回 `(address, size)` 元组

---

## `A2lParser`

A2L (ASAP2) 标定文件解析器。

### 构造函数

```python
A2lParser(filepath: str)
```

### 方法

- `get_variables()` — 提取所有 MEASUREMENT/CHARACTERISTIC/INSTANCE/TYPEDEF_STRUCTURE 变量
- `get_variable_type(var_name: str)` — 根据变量名快速查询数据类型

---

## `TypeTreeDumper`

类型树可视化工具。

### 构造函数

```python
TypeTreeDumper(explorer: DwarfTypeExplorer)
```

### 方法

- `dump(type_name, *, options=None, emitter=None)` — 渲染类型树为文本表格
- `build(type_name, *, options=None)` — 构建 JSON 可序列化的类型树字典

---

## `DumpOptions`

类型树展开配置。

```python
@dataclass
class DumpOptions:
    max_depth: int = 20
    recursive: bool = True
    show_notes: bool = True
    expand_type_names: Optional[Set[str]] = None
    expand_member_names: Optional[Set[str]] = None
    case_insensitive_filters: bool = False
```
