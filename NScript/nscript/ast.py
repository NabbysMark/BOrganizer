class AST:
    pass

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = op
        self.op = op
        self.right = right

class Print(AST):
    def __init__(self, value):
        self.value = value

class VarAssign(AST):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class Var(AST):
    def __init__(self, name):
        self.name = name

class Str(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Compare(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class If(AST):
    def __init__(self, branches):
        self.branches = branches

class Program(AST):
    def __init__(self, statements):
        self.statements = statements

class FuncDef(AST):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FuncCall(AST):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class Return(AST):
    def __init__(self, value):
        self.value = value

class FeedOp(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Bool(AST):
    def __init__(self, value):
        self.value = value

class ListLiteral(AST):
    def __init__(self, elements):
        self.elements = elements

class DictLiteral(AST):
    def __init__(self, pairs):
        self.pairs = pairs

class Subscript(AST):
    def __init__(self, value, index):
        self.value = value
        self.index = index

class ForLoop(AST):
    def __init__(self, var, start, end, body):
        self.var = var
        self.start = start
        self.end = end
        self.body = body

class ForEachLoop(AST):
    def __init__(self, index_var, value_var, collection, body):
        self.index_var = index_var
        self.value_var = value_var
        self.collection = collection
        self.body = body

class Len(AST):
    def __init__(self, value):
        self.value = value

class TallBoy(AST):
    def __init__(self, value):
        self.value = value

class LogicalOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Import(AST):
    def __init__(self, module_path):
        self.module_path = module_path

class ImportOnly(AST):
    def __init__(self, module_path, name):
        self.module_path = module_path
        self.name = name

class ClassDef(AST):
    def __init__(self, name, methods, base_class=None):
        self.name = name
        self.methods = methods
        self.base_class = base_class

class SuperCall(AST):
    def __init__(self, args):
        self.args = args

class ClassInstance(AST):
    def __init__(self, class_name, args):
        self.class_name = class_name
        self.args = args

class AttributeAccess(AST):
    def __init__(self, obj, attr):
        self.obj = obj
        self.attr = attr

class WhileLoop(AST):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class ToString(AST):
    def __init__(self, expr):
        self.expr = expr

class ToNumber(AST):
    def __init__(self, expr):
        self.expr = expr

class TypeOf:
    def __init__(self, expr):
        self.expr = expr

class Nom:
    def __init__(self, path_expr):
        self.path_expr = path_expr

class Input:
    def __init__(self, prompt_expr):
        self.prompt_expr = prompt_expr

class Gurt:
    def __init__(self, expr):
        self.expr = expr

class SliceNode(AST):
    def __init__(self, start, end, step):
        self.start = start
        self.end = end
        self.step = step