import os
import sys
import shutil
from typing import Any
from nscript.lexer import Lexer
from nscript.parser import Parser
from nscript.parser import AttributeAccess, Var
from nscript.ast import Var

class Interpreter:
    def __init__(self):
        self.env = {}  # type: dict[str, Any]
        self.functions = {}
        self.classes = {}
        self.libraries = {}

        self._ensure_libs_in_appdata()

    def _ensure_libs_in_appdata(self):
        local_libs_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "nscript_libs")
        if not os.path.exists(local_libs_dir):
            os.makedirs(local_libs_dir, exist_ok=True)
            defaultlibs_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "defaultlibs"))
            if os.path.exists(defaultlibs_dir):
                for fname in os.listdir(defaultlibs_dir):
                    src = os.path.join(defaultlibs_dir, fname)
                    dst = os.path.join(local_libs_dir, fname)
                    if os.path.isfile(src):
                        shutil.copyfile(src, dst)

    def interpret(self, node):
        return self.visit(node)

    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def visit_SliceNode(self, node):
        # Convert 1-based indices to 0-based for start/end if they are ints
        def to_zero_based(val):
            if val is None:
                return None
            v = self.visit(val) if hasattr(val, '__class__') and not isinstance(val, int) else val
            return v - 1 if isinstance(v, int) else v
        start = to_zero_based(node.start)
        end = self.visit(node.end) if node.end is not None and hasattr(node.end, '__class__') and not isinstance(node.end, int) else node.end
        if isinstance(end, int):
            end = end
        step = self.visit(node.step) if node.step is not None and hasattr(node.step, '__class__') and not isinstance(node.step, int) else node.step
        return slice(start, end, step)

    def generic_visit(self, node):
        raise Exception(f'No visit_{type(node).__name__} method')

    def visit_Num(self, node):
        return node.value

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = getattr(node.op, "value", None)
        if op == '+':
            return left + right
        elif op == '-':
            return left - right
        elif op == '*':
            return left * right
        elif op == '/':
            return left / right
        else:
            raise Exception(f"Unknown operator: {op}")

    def visit_Print(self, node):
        value = self.visit(node.value)
        if hasattr(value, "interpolated") and getattr(value, "interpolated", False):
            value = self.visit_Str(value)
        elif hasattr(node.value, "interpolated") and getattr(node.value, "interpolated", False):
            value = self.visit_Str(node.value)
        print(value)
        return None

    def visit_Program(self, node):
        for stmt in node.statements:
            if hasattr(stmt, "token") and getattr(stmt.token, "type", None) == "KILL":
                print("Script terminated by KILL SELF.")
                sys.exit(1)
            if getattr(stmt, "is_kill_self", False):
                print("Script terminated by KILL SELF.")
                sys.exit(1)
            self.visit(stmt)
        return None

    def visit_ClassDef(self, node):
        self.classes[node.name] = node
        return None

    def visit_ClassInstance(self, node):
        class_def = self.classes.get(node.class_name)
        if not class_def:
            raise Exception(f"Class '{node.class_name}' not defined")
        instance = {'__class__': class_def, '__fields__': {}}
        if getattr(class_def, "base_class", None):
            base = self.classes.get(class_def.base_class)
            if base:
                for k, v in base.methods.items():
                    if k not in class_def.methods:
                        class_def.methods[k] = v
        if 'constructor' in class_def.methods:
            ctor = class_def.methods['constructor']
            local_env = {'ts': instance}
            for pname, arg in zip(ctor.params[1:], node.args):
                local_env[pname] = self.visit(arg)
            old_env = self.env
            self.env = local_env
            for stmt in ctor.body:
                self.visit(stmt)
            self.env = old_env
        return instance

    def visit_SuperCall(self, node):
        ts = self.env.get('ts')
        if not ts:
            raise Exception("SUPERMAN can only be called inside a class method")
        class_def = ts.get('__class__')
        base_class_name = getattr(class_def, "base_class", None)
        if not base_class_name:
            raise Exception("No base class to call SUPERMAN on")
        base_class = self.classes.get(base_class_name)
        if not base_class or 'constructor' not in base_class.methods:
            raise Exception(f"Base class '{base_class_name}' has no constructor")
        ctor = base_class.methods['constructor']
        local_env = {'ts': ts}
        for pname, arg in zip(ctor.params[1:], node.args):
            local_env[pname] = self.visit(arg)
        old_env = self.env
        self.env = local_env
        for stmt in ctor.body:
            self.visit(stmt)
        self.env = old_env

    def visit_AttributeAccess(self, node):
        obj = self.visit(node.obj)
        attr = node.attr
        if hasattr(obj, "__nscript_pythonlib__"):
            if hasattr(obj, attr):
                return getattr(obj, attr)
            raise Exception(f"Library '{obj.__nscript_pythonlib__}' has no attribute '{attr}'")
        if isinstance(obj, dict) and attr in obj.get('__fields__', {}):
            return obj['__fields__'][attr]
        class_def = obj.get('__class__') if isinstance(obj, dict) else None
        if class_def and attr in class_def.methods:
            def bound_method(*args):
                method = class_def.methods[attr]
                local_env = {'ts': obj}
                for pname, arg in zip(method.params[1:], args):
                    local_env[pname] = arg
                old_env = self.env
                self.env = local_env
                result = None
                try:
                    for stmt in method.body:
                        result = self.visit(stmt)
                except ReturnException as ret:
                    self.env = old_env
                    return ret.value
                self.env = old_env
                return result
            return bound_method
        raise Exception(f"Attribute '{attr}' not found")

    def visit_VarAssign(self, node):
        value = self.visit(node.value) if node.value is not None else None
        if isinstance(node.name, AttributeAccess):
            obj = self.visit(node.name.obj)
            attr = node.name.attr
            obj['__fields__'][attr] = value
            return value
        else:
            self.env[node.name] = value
            return value

    def visit_FuncCall(self, node):
        if isinstance(node.name, AttributeAccess):
            method = self.visit(node.name)
            args = [self._to_python_value(self.visit(arg)) for arg in node.args]
            if callable(method):
                return method(*args)
            raise Exception("Attribute is not callable")
        func_obj = None
        if hasattr(node.name, "name"):
            if node.name.name in self.env:
                func_obj = self.env[node.name.name]
            elif node.name.name in self.functions:
                func_obj = self.functions[node.name.name]
        elif isinstance(node.name, str) and node.name in self.functions:
            func_obj = self.functions[node.name]
        if func_obj:
            if hasattr(func_obj, "params") and hasattr(func_obj, "body"):
                old_env = self.env.copy()
                local_env = old_env.copy()
                for param, arg in zip(func_obj.params, node.args):
                    local_env[param] = self.visit(arg)
                self.env = local_env
                result = None
                try:
                    for stmt in func_obj.body:
                        result = self.visit(stmt)
                except ReturnException as ret:
                    self.env = old_env
                    return ret.value
                self.env = old_env
                return result
            if callable(func_obj):
                args = [self._to_python_value(self.visit(arg)) for arg in node.args]
                return func_obj(*args)
            raise Exception(f"Variable '{getattr(node.name, 'name', node.name)}' is not callable")
        raise Exception(f"Function '{getattr(node.name, 'name', node.name)}' not defined")

    def visit_Return(self, node):
        value = self.visit(node.value)
        raise ReturnException(value)

    def visit_FeedOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        return str(left) + str(right)

    def visit_Bool(self, node):
        return node.value

    def visit_ListLiteral(self, node):
        return [self.visit(element) for element in node.elements]

    def visit_DictLiteral(self, node):
        return {self.visit(k): self.visit(v) for k, v in node.pairs}

    def visit_Subscript(self, node):
        value = self.visit(node.value)
        index = self.visit(node.index)
        if isinstance(index, slice):
            if isinstance(value, (str, list)):
                return value[index]
            else:
                raise Exception("Slicing only supported on strings and lists")
        if not isinstance(index, int):
            raise Exception("Indices must be integers")
        idx = index - 1
        if isinstance(value, dict):
            keys = list(value.keys())
            if not (0 <= idx < len(keys)):
                raise Exception(f"Index {index} out of range for dictionary")
            key = keys[idx]
            return value[key]
        elif isinstance(value, list):
            if not (0 <= idx < len(value)):
                raise Exception(f"Index {index} out of range for list")
            return value[idx]
        elif isinstance(value, str):
            if not (0 <= idx < len(value)):
                raise Exception(f"Index {index} out of range for string")
            return value[idx]
        else:
            raise Exception(f"Cannot subscript value of type {type(value).__name__}")

    def visit_Len(self, node):
        value = self.visit(node.value)
        if isinstance(value, (list, dict)):
            return len(value)
        else:
            raise Exception(f"Cannot get length of type {type(value).__name__}")

    def visit_TallBoy(self, node):
        value = self.visit(node.value)
        if isinstance(value, str):
            return len(value)
        else:
            raise Exception(f"TALL BOY only works on strings, got {type(value).__name__}")

    def visit_ForLoop(self, node):
        start = self.visit(node.start)
        end = self.visit(node.end)
        result = None
        for i in range(int(start), int(end) + 1):
            self.env[node.var] = i
            for stmt in node.body:
                result = self.visit(stmt)
        return result

    def visit_LogicalOp(self, node):
        if node.op == 'NOT':
            return not bool(self.visit(node.left))
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op == 'ALSO':
            return bool(left) and bool(right)
        elif node.op == 'MAYBE':
            return bool(left) or bool(right)
        else:
            raise Exception(f"Unknown logical operator: {node.op}")

    def visit_Import(self, node):
        if node.module_path.startswith("LIBRARY "):
            libname = node.module_path[len("LIBRARY "):].strip('"').strip("'")
            if libname in self.libraries:
                return
            local_libs_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "nscript_libs")
            lib_dir = os.path.join(local_libs_dir, libname)
            lib_main = os.path.join(lib_dir, "main.py")
            lib_main = os.path.normpath(lib_main)
            if not os.path.exists(lib_main):
                raise Exception(f"Library '{libname}' not found at {lib_main}")
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"nscript_libs.{libname}.main", lib_main)
            if spec is None or spec.loader is None:
                raise Exception(f"Could not load library '{libname}' from {lib_main}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            setattr(mod, "__nscript_pythonlib__", libname)
            self.libraries[libname] = mod
            self.env[libname] = mod
            return
        module_env, module_funcs, module_classes = self._load_module_env(node.module_path)
        for k, v in module_env.items():
            self.env[f"{os.path.basename(node.module_path).replace('.n','')}__{k}"] = v
        for k, v in module_funcs.items():
            self.functions[f"{os.path.basename(node.module_path).replace('.n','')}__{k}"] = v
        for k, v in module_classes.items():
            self.classes[f"{os.path.basename(node.module_path).replace('.n','')}__{k}"] = v

    def visit_ImportOnly(self, node):
        module_env, module_funcs, module_classes = self._load_module_env(node.module_path)
        if node.name in module_env:
            self.env[node.name] = module_env[node.name]
        elif node.name in module_funcs:
            self.functions[node.name] = module_funcs[node.name]
        elif node.name in module_classes:
            self.classes[node.name] = module_classes[node.name]
        else:
            raise Exception(f"'{node.name}' not found in module '{node.module_path}'")

    def visit_ImportAs(self, node):
        if node.is_library:
            libname = node.module_path[len("LIBRARY "):].strip('"').strip("'")
            local_libs_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "nscript_libs")
            lib_dir = os.path.join(local_libs_dir, libname)
            lib_main = os.path.join(lib_dir, "main.py")
            lib_main = os.path.normpath(lib_main)
            if not os.path.exists(lib_main):
                raise Exception(f"Library '{libname}' not found at {lib_main}")
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"nscript_libs.{libname}.main", lib_main)
            if spec is None or spec.loader is None:
                raise Exception(f"Could not load library '{libname}' from {lib_main}")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            setattr(mod, "__nscript_pythonlib__", libname)
            alias = node.as_name if node.as_name else libname
            if node.only_name:
                if not hasattr(mod, node.only_name):
                    raise Exception(f"Library '{libname}' has no attribute '{node.only_name}'")
                self.env[alias] = getattr(mod, node.only_name)
            else:
                self.libraries[alias] = mod
                self.env[alias] = mod
            return
        module_env, module_funcs, module_classes = self._load_module_env(node.module_path)
        alias = node.as_name if node.as_name else os.path.basename(node.module_path).replace('.n','')
        class ModuleObj:
            pass
        mod_obj = ModuleObj()
        for k, v in {**module_env, **module_funcs, **module_classes}.items():
            setattr(mod_obj, k, v)
        if node.only_name:
            if node.only_name in module_env:
                self.env[alias] = module_env[node.only_name]
            elif node.only_name in module_funcs:
                self.env[alias] = module_funcs[node.only_name]
            elif node.only_name in module_classes:
                self.env[alias] = module_classes[node.only_name]
            else:
                raise Exception(f"'{node.only_name}' not found in module '{node.module_path}'")
        else:
            self.env[alias] = mod_obj

    def _load_module_env(self, module_path):
        import sys, os
        from nscript.lexer import Lexer
        from nscript.parser import Parser
        if not module_path.endswith('.n'):
            module_path += '.n'
        main_file = sys.argv[1] if len(sys.argv) > 1 else __file__
        base_dir = os.path.dirname(os.path.abspath(main_file))
        abs_module_path = os.path.join(base_dir, module_path)
        abs_module_path = os.path.normpath(abs_module_path)
        if not os.path.exists(abs_module_path):
            raise Exception(f"Module file '{abs_module_path}' not found")
        with open(abs_module_path, 'r', encoding='utf-8') as f:
            source = f.read()
        lexer = Lexer(source)
        parser = Parser(lexer)
        tree = parser.parse()
        module_interpreter = Interpreter()
        module_interpreter.env = {}
        module_interpreter.functions = {}
        module_interpreter.classes = {}
        module_interpreter.interpret(tree)
        return dict(module_interpreter.env), dict(module_interpreter.functions), dict(module_interpreter.classes)

    def visit_Str(self, node):
        value = getattr(node, "value", None)
        if getattr(node, "interpolated", False):
            import re
            def interpolate(match):
                expr_code = match.group(1)
                expr_lexer = Lexer(expr_code)
                expr_parser = Parser(expr_lexer)
                expr_ast = expr_parser.expr()
                return str(self.visit(expr_ast))
            return re.sub(r"\$\{([^}]+)\}", interpolate, str(value) if value is not None else "")
        return value

    def visit_Var(self, node):
        if node.name in self.env:
            return self.env[node.name]
        elif node.name in self.functions:
            return self.functions[node.name]
        else:
            raise Exception(f"Variable '{node.name}' not defined")

    def visit_WhileLoop(self, node):
        result = None
        while self.visit(node.condition):
            for stmt in node.body:
                result = self.visit(stmt)
        return result

    def visit_ToString(self, node):
        value = self.visit(node.expr)
        return str(value)

    def visit_ToNumber(self, node):
        value = self.visit(node.expr)
        try:
            return int(value)
        except (ValueError, TypeError):
            try:
                return float(value)
            except (ValueError, TypeError):
                raise Exception(f"Cannot convert {value!r} to number")

    def visit_TypeOf(self, node):
        value = self.visit(node.expr)
        if isinstance(value, bool):
            return "bool"
        elif isinstance(value, int) or isinstance(value, float):
            return "number"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "list"
        elif isinstance(value, dict):
            return "dictionary"
        elif value is None:
            return "none"
        else:
            return type(value).__name__

    def visit_Nom(self, node):
        path = self.visit(node.path_expr)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise Exception(f"NOM error: {e}")

    def visit_If(self, node):
        for condition, body in node.branches:
            if condition is None or self.visit(condition):
                result = None
                for stmt in body:
                    result = self.visit(stmt)
                return result
        return None

    def visit_Compare(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if node.op == 'IS':
            return left == right
        elif node.op == 'IS_NOT':
            return left != right
        elif node.op == 'IS_UNDER':
            return left < right
        elif node.op == 'IS_OVER':
            return left > right
        else:
            raise Exception(f"Unknown comparison operator: {node.op}")

    def visit_FuncDef(self, node):
        self.functions[node.name] = node
        return None

    def visit_Input(self, node):
        prompt = self.visit(node.prompt_expr)
        return input(str(prompt))

    def visit_Gurt(self, node):
        expr_str = self.visit(node.expr)
        try:
            allowed = "0123456789+-*/(). "
            if not all(c in allowed for c in str(expr_str)):
                raise Exception("GURT only allows basic math expressions.")
            return eval(str(expr_str), {"__builtins__": None}, {})
        except Exception as e:
            raise Exception(f"GURT error: {e}")

    def visit_ForEachLoop(self, node):
        collection = self.visit(node.collection)
        result = None
        if isinstance(collection, dict):
            items = list(collection.items())
            for idx, (k, v) in enumerate(items):
                self.env[node.index_var] = k
                self.env[node.value_var] = v
                for stmt in node.body:
                    result = self.visit(stmt)
        elif isinstance(collection, list):
            for idx, v in enumerate(collection):
                self.env[node.index_var] = idx + 1
                self.env[node.value_var] = v
                for stmt in node.body:
                    result = self.visit(stmt)
        else:
            raise Exception("Can only SPIN over lists or dictionaries")
        return result

    def _to_python_value(self, value):
        if isinstance(value, dict):
            return {self._to_python_value(k): self._to_python_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._to_python_value(v) for v in value]
        return value

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value
