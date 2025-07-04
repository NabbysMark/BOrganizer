from nscript.lexer import (
    Lexer, NUMBER, FLOAT, DOUBLE, PLUS, MINUS, MULTIPLY, DIVIDE, LPAREN, RPAREN, EOF, FELLA, STRING, AT, POPPIN, RING, FEED, RETURN, TRUE, FALSE, LBRACKET, RBRACKET, LBRACE, RBRACE, COLON, SPIN, ASSIGN, HASH, TALLBOY, ALSO, MAYBE, ISNOT, NOT, GIVE, ME, BUT, ONLY, LEARNING, BUILD, DOT,
    HUNGRY, FOR, CONVERTED, WAITING, INTERP_STRING, LIBRARY, KILL, SELF, EXTENDING, WITH, SUPERMAN, AS
)
from nscript.ast import Num, BinOp, Print, VarAssign, Var, Str, If, Compare, Program, FuncDef, FuncCall, Return, FeedOp, Bool, ListLiteral, DictLiteral, Subscript, ForLoop, Len, TallBoy, LogicalOp, Import, ImportOnly, ClassDef, ClassInstance, AttributeAccess, WhileLoop
from nscript.ast import ToString, ToNumber, TypeOf, Nom, Input, Gurt

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def _make_slice(self, start, end, step):
        # Convert 1-based to 0-based for start/end if int, else None
        s = start - 1 if isinstance(start, int) else None
        e = end if end is not None and isinstance(end, int) else None
        st = step if step is not None and isinstance(step, int) else None
        return slice(s, e, st)

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise Exception(f'Unexpected token: {self.current_token}, expected {token_type} at line {getattr(self.current_token, "line", "?")}, pos {getattr(self.current_token, "pos", "?")}')

    def factor(self):
        token = self.current_token
        if token.type == HASH:
            self.eat(HASH)
            value = self.factor()
            return Len(value)
        elif token.type == TALLBOY:
            self.eat(TALLBOY)
            value = self.factor()
            return TallBoy(value)
        elif token.type in (NUMBER, FLOAT, DOUBLE):
            self.eat(token.type)
            return Num(token)
        elif token.type == INTERP_STRING:
            value = token.value
            self.eat(INTERP_STRING)
            s = Str(token)
            s.value = value
            setattr(s, 'interpolated', True)
            return s
        elif token.type == STRING:
            self.eat(STRING)
            return Str(token)
        elif getattr(token, "value", None) and isinstance(token.value, str) and token.value.startswith("`") and token.value.endswith("`"):
            raw = token.value[1:-1]
            self.eat(STRING)
            return Str(type('InterpolatedString', (), {'value': raw, 'interpolated': True})())
        elif token.type == TRUE:
            self.eat(TRUE)
            return Bool(True)
        elif token.type == FALSE:
            self.eat(FALSE)
            return Bool(False)
        elif token.type == BUILD:
            self.eat(BUILD)
            if self.current_token.type != 'ID':
                raise Exception("Expected class name after BUILD")
            class_name = self.current_token.value
            self.eat('ID')
            self.eat(LPAREN)
            args = []
            if self.current_token.type != RPAREN:
                args.append(self.expr())
                while self.current_token.type == ',':
                    self.eat(',')
                    args.append(self.expr())
            self.eat(RPAREN)
            return ClassInstance(class_name, args)
        elif token.type == 'ID':
            varname = token.value
            self.eat('ID')
            node = Var(varname)
            while True:
                if self.current_token.type == DOT:
                    self.eat(DOT)
                    if self.current_token.type != 'ID':
                        raise Exception(f"Expected attribute name after '.' at line {getattr(self.current_token, 'line', '?')}, pos {getattr(self.current_token, 'pos', '?')}")
                    attr = self.current_token.value
                    self.eat('ID')
                    node = AttributeAccess(node, attr)
                    if self.current_token.type == LPAREN:
                        self.eat(LPAREN)
                        args = []
                        if self.current_token.type != RPAREN:
                            args.append(self.expr())
                            while self.current_token.type == ',':
                                self.eat(',')
                                args.append(self.expr())
                        self.eat(RPAREN)
                        node = FuncCall(node, args)
                elif self.current_token.type == LPAREN:
                    self.eat(LPAREN)
                    args = []
                    if self.current_token.type != RPAREN:
                        args.append(self.expr())
                        while self.current_token.type == ',':
                            self.eat(',')
                            args.append(self.expr())
                    self.eat(RPAREN)
                    node = FuncCall(node, args)
                elif self.current_token.type == LBRACKET:
                    self.eat(LBRACKET)
                    # Support full Python-like slicing: [start:end:step]
                    start = self.expr() if self.current_token.type != COLON and self.current_token.type != RBRACKET else None
                    if self.current_token.type == COLON:
                        self.eat(COLON)
                        end = self.expr() if self.current_token.type != COLON and self.current_token.type != RBRACKET else None
                        if self.current_token.type == COLON:
                            self.eat(COLON)
                            step = self.expr() if self.current_token.type != RBRACKET else None
                        else:
                            step = None
                        self.eat(RBRACKET)
                        # Do not convert to 0-based here, let interpreter handle it
                        node = Subscript(node, SliceNode(start, end, step))
                    else:
                        self.eat(RBRACKET)
                        node = Subscript(node, start)
                else:
                    break
            return node
        elif token.type == LBRACKET:
            return self.list_literal()
        elif token.type == LBRACE:
            return self.dict_literal()
        elif token.type == LPAREN:
            self.eat(LPAREN)
            node = self.expr()
            self.eat(RPAREN)
            return node
        elif token.type == HUNGRY:
            self.eat(HUNGRY)
            if self.current_token.type != FOR:
                raise Exception("Expected FOR after HUNGRY")
            self.eat(FOR)
            if self.current_token.type == CONVERTED:
                self.eat(CONVERTED)
                if self.current_token.type == 'STRING':
                    self.eat('STRING')
                    expr = self.expr()
                    return ToString(expr)
                elif self.current_token.type == 'NUMBER':
                    self.eat('NUMBER')
                    expr = self.expr()
                    return ToNumber(expr)
                else:
                    raise Exception(f"Expected STRING or NUMBER after CONVERTED, got {self.current_token}")
            else:
                raise Exception("Expected CONVERTED after FOR")
        elif token.type == 'CONVERTSTRING':
            self.eat('CONVERTSTRING')
            expr = self.expr()
            return ToString(expr)
        elif token.type == 'CONVERTNUMBER':
            self.eat('CONVERTNUMBER')
            expr = self.expr()
            return ToNumber(expr)
        elif token.type == 'TYPEOF':
            self.eat('TYPEOF')
            expr = self.expr()
            return TypeOf(expr)
        elif token.type == 'NOM':
            self.eat('NOM')
            path_expr = self.expr()
            return Nom(path_expr)
        elif token.type == 'INPUT':
            self.eat('INPUT')
            prompt_expr = self.expr()
            return Input(prompt_expr)
        elif token.type == 'NONE':
            self.eat('NONE')
            return None
        elif token.type == 'GURT':
            self.eat('GURT')
            expr = self.expr()
            return Gurt(expr)
        elif token.type == 'SUPERMAN':
            self.eat('SUPERMAN')
            args = []
            if self.current_token.type == 'LPAREN':
                self.eat('LPAREN')
                if self.current_token.type != 'RPAREN':
                    args.append(self.expr())
                    while self.current_token.type == ',':
                        self.eat(',')
                        args.append(self.expr())
                self.eat('RPAREN')
            return SuperCall(args)
        elif token.type == STRING:
            value = token.value
            self.eat(STRING)
            import re
            def interpolate(match):
                expr_code = match.group(1)
                expr_lexer = Lexer(expr_code)
                expr_parser = Parser(expr_lexer)
                expr_ast = expr_parser.expr()
                return '{' + expr_code + '}'
            if '{' in value and '}' in value:
                return Str(type('InterpolatedString', (), {'value': value, 'interpolated': True})())
            return Str(token)
        if token.type == FEED:
            self.eat(FEED)
            return self.factor()
        else:
            raise Exception(f"Invalid syntax in factor at line {getattr(token, 'line', '?')}, pos {getattr(token, 'pos', '?')}, token: {token}")

    def list_literal(self):
        elements = []
        self.eat('LBRACKET')
        if self.current_token.type != 'RBRACKET':
            elements.append(self.expr())
            while self.current_token.type == ',':
                self.eat(',')
                elements.append(self.expr())
        self.eat('RBRACKET')
        return ListLiteral(elements)

    def dict_literal(self):
        pairs = []
        self.eat(LBRACE)
        if self.current_token.type != RBRACE:
            key = self.expr()
            self.eat(COLON)
            value = self.expr()
            pairs.append((key, value))
            while self.current_token.type == ',':
                self.eat(',')
                key = self.expr()
                self.eat(COLON)
                value = self.expr()
                pairs.append((key, value))
        self.eat(RBRACE)
        return DictLiteral(pairs)

    def feed_expr(self):
        node = self.expr()
        while self.current_token.type == FEED:
            self.eat(FEED)
            right = self.expr()
            node = FeedOp(node, right)
        return node

    def term(self):
        node = self.factor()
        while self.current_token.type in (MULTIPLY, DIVIDE):
            token = self.current_token
            if token.type == MULTIPLY:
                self.eat(MULTIPLY)
            else:
                self.eat(DIVIDE)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token.type in (PLUS, MINUS):
            token = self.current_token
            if token.type == PLUS:
                self.eat(PLUS)
            else:
                self.eat(MINUS)
            node = BinOp(left=node, op=token, right=self.term())
        while self.current_token.type == FEED:
            self.eat(FEED)
            right = self.term()
            node = FeedOp(node, right)
        return node

    def statement(self):
        if self.current_token.type == LEARNING:
            return self.class_def()
        elif self.current_token.type == GIVE:
            return self.import_statement()
        elif self.current_token.type == 'AT':
            return self.block_statement()
        elif self.current_token.type == FELLA:
            self.eat(FELLA)
            value = self.feed_expr()
            return Print(value)
        elif self.current_token.type == 'YE':
            return self.var_statement()
        elif self.current_token.type == 'WHAT':
            return self.if_statement()
        elif self.current_token.type == POPPIN:
            return self.func_def()
        elif self.current_token.type == RETURN:
            self.eat(RETURN)
            value = self.feed_expr()
            return Return(value)
        elif self.current_token.type == RING:
            raise Exception("The 'RING' keyword is no longer supported. Use standard function call syntax.")
        elif self.current_token.type == SPIN:
            return self.for_loop()
        elif self.current_token.type == 'WAITING':
            return self.while_loop()
        elif self.current_token.type == 'ID':
            node = self.factor()
            if isinstance(node, AttributeAccess) and self.current_token.type == 'BOOM':
                self.eat('BOOM')
                value = self.expr()
                return VarAssign(node, value)
            elif isinstance(node, Var) and self.current_token.type == 'BOOM':
                self.eat('BOOM')
                value = self.expr()
                return VarAssign(node.name, value)
            return node
        elif self.current_token.type == 'KILL':
            self.eat('KILL')
            if self.current_token.type == 'SELF':
                self.eat('SELF')
                return KillSelf()
            else:
                raise Exception("Expected SELF after KILL")
        elif self.current_token.type == 'EXTENDING':
            return self.extending_class_def()
        else:
            return self.feed_expr()

    def while_loop(self):
        self.eat('WAITING')
        if self.current_token.type == 'LPAREN':
            self.eat('LPAREN')
            condition = self.condition_expr()
            if self.current_token.type == 'RPAREN':
                self.eat('RPAREN')
        else:
            condition = self.condition_expr()
        while self.current_token.type not in ('WE', 'EOF'):
            self.current_token = self.lexer.get_next_token()
        self.eat('WE')
        body = self.block()
        return WhileLoop(condition, body)

    def for_loop(self):
        self.eat(SPIN)
        if self.current_token.type != 'BOOM':
            raise Exception("Expected 'BOOM' before loop variable name")
        self.eat('BOOM')
        if self.current_token.type == 'ID':
            var1 = self.current_token.value
            self.eat('ID')
            if self.current_token.type == ',':
                self.eat(',')
                if self.current_token.type != 'ID':
                    raise Exception("Expected value variable name after ','")
                var2 = self.current_token.value
                self.eat('ID')
                if self.current_token.type != 'IN':
                    raise Exception("Expected 'IN' after index, value")
                self.eat('IN')
                collection = self.expr()
                self.eat('WE')
                body = self.block()
                return ForEachLoop(var1, var2, collection, body)
            elif self.current_token.type == 'IS':
                self.eat('IS')
                start = self.expr()
                if self.current_token.type != ',':
                    raise Exception("Expected ',' after loop start value")
                self.eat(',')
                end = self.expr()
                self.eat('WE')
                body = self.block()
                return ForLoop(var1, start, end, body)
            else:
                raise Exception("Expected ',' or 'IS' after loop variable name")
        else:
            raise Exception("Expected loop variable name after BOOM")
        return ForLoop(var, start, end, body)

    def block_statement(self):
        self.eat('AT')
        statements = []
        while self.current_token.type != 'AT' and self.current_token.type != 'EOF':
            stmt = self.statement()
            if stmt is not None:
                statements.append(stmt)
        self.eat('AT')
        return Program(statements)

    def if_statement(self):
        branches = []
        self.eat('WHAT')
        self.eat('LPAREN')
        condition = self.condition_expr()
        self.eat('RPAREN')
        self.eat('WE')
        body = self.block()
        branches.append((condition, body))
        while self.current_token.type in ('ANOTHER', 'ANOTHER_ONE'):
            if self.current_token.type == 'ANOTHER_ONE':
                self.eat('ANOTHER_ONE')
                self.eat('LPAREN')
                condition = self.condition_expr()
                self.eat('RPAREN')
                self.eat('WE')
                body = self.block()
                branches.append((condition, body))
            elif self.current_token.type == 'ANOTHER':
                self.eat('ANOTHER')
                self.eat('WE')
                body = self.block()
                branches.append((None, body))
        return If(branches)

    def condition_expr(self):
        if self.current_token.type == 'NOT':
            self.eat('NOT')
            node = self.condition_expr()
            return LogicalOp(node, 'NOT', None)
        left = self.expr()
        if self.current_token.type == 'IS':
            self.eat('IS')
            if self.current_token.type == 'NOT':
                self.eat('NOT')
                right = self.expr()
                node = Compare(left, 'IS_NOT', right)
            elif self.current_token.type == 'UNDER':
                self.eat('UNDER')
                right = self.expr()
                node = Compare(left, 'IS_UNDER', right)
            elif self.current_token.type == 'OVER':
                self.eat('OVER')
                right = self.expr()
                node = Compare(left, 'IS_OVER', right)
            else:
                right = self.expr()
                node = Compare(left, 'IS', right)
        elif self.current_token.type == 'ISNOT':
            self.eat('ISNOT')
            right = self.expr()
            node = Compare(left, 'IS_NOT', right)
        else:
            node = left
        while self.current_token.type in ('ALSO', 'MAYBE'):
            op = self.current_token.type
            self.eat(op)
            right = self.condition_expr()
            node = LogicalOp(node, op, right)
        return node
    
    def block(self):
        statements = []
        while self.current_token.type not in ('POW', 'ANOTHER', 'ANOTHER_ONE', 'EOF'):
            stmt = self.statement()
            if stmt is not None:
                statements.append(stmt)
        self.eat('POW')
        return statements

    def var_statement(self):
        self.eat('YE')
        if self.current_token.type != 'ID':
            raise Exception("Expected variable name after YE")
        varname = self.current_token.value
        self.eat('ID')
        if self.current_token.type == 'BOOM':
            self.eat('BOOM')
            value = self.expr()
            return VarAssign(varname, value)
        else:
            return VarAssign(varname, None)

    def func_def(self):
        self.eat(POPPIN)
        if self.current_token.type != 'ID':
            raise Exception("Expected function name after POPPIN")
        name = self.current_token.value
        self.eat('ID')
        self.eat(LPAREN)
        params = []
        if self.current_token.type == 'ID':
            params.append(self.current_token.value)
            self.eat('ID')
            while self.current_token.type == ',':
                self.eat(',')
                params.append(self.current_token.value)
                self.eat('ID')
        self.eat(RPAREN)
        body = self.block()
        return FuncDef(name, params, body)

    def func_call(self):
        raise Exception("The 'RING' keyword is no longer supported. Use standard function call syntax.")

    def import_statement(self):
        self.eat(GIVE)
        as_name = None
        only_name = None
        is_library = False
        if self.current_token.type == LIBRARY:
            is_library = True
            self.eat(LIBRARY)
            if self.current_token.type != STRING:
                raise Exception('Expected library name string after GIVE LIBRARY')
            libname = self.current_token.value
            self.eat(STRING)
            module_path = f'LIBRARY {libname}'
        else:
            self.eat(ME)
            if self.current_token.type != STRING:
                raise Exception('Expected module path string after GIVE ME')
            module_path = self.current_token.value
            self.eat(STRING)
        if self.current_token.type == 'AS':
            self.eat('AS')
            if self.current_token.type != 'ID':
                raise Exception('Expected name after AS')
            as_name = self.current_token.value
            self.eat('ID')
        if self.current_token.type == BUT:
            self.eat(BUT)
            self.eat(ONLY)
            if self.current_token.type != 'ID':
                raise Exception('Expected variable or function name after BUT ONLY')
            only_name = self.current_token.value
            self.eat('ID')
        if as_name or only_name:
            return ImportAs(module_path, as_name, only_name, is_library)
        elif is_library:
            return Import(module_path)
        else:
            return Import(module_path)

    def extending_class_def(self):
        self.eat('EXTENDING')
        if self.current_token.type != 'ID':
            raise Exception("Expected base class name after EXTENDING")
        base_class = self.current_token.value
        self.eat('ID')
        if self.current_token.type != 'WITH':
            raise Exception("Expected WITH after EXTENDING <BaseClass>")
        self.eat('WITH')
        if self.current_token.type != 'ID':
            raise Exception("Expected subclass name after WITH")
        class_name = self.current_token.value
        self.eat('ID')
        self.eat('WE')
        methods = {}
        while self.current_token.type == POPPIN:
            method = self.func_def()
            methods[method.name] = method
        self.eat('POW')
        return ClassDef(class_name, methods, base_class=base_class)

    def class_def(self):
        self.eat(LEARNING)
        if self.current_token.type != 'ID':
            raise Exception("Expected class name after LEARNING")
        class_name = self.current_token.value
        self.eat('ID')
        self.eat('WE')
        methods = {}
        while self.current_token.type == POPPIN:
            method = self.func_def()
            methods[method.name] = method
        self.eat('POW')
        return ClassDef(class_name, methods)

    def parse(self):
        statements = []
        while self.current_token.type != 'EOF':
            stmt = self.statement()
            if stmt is not None:
                statements.append(stmt)
        return Program(statements)

class KillSelf:
    is_kill_self = True

class SuperCall:
    def __init__(self, args):
        self.args = args

class ImportAs:
    def __init__(self, module_path, as_name, only_name=None, is_library=False):
        self.module_path = module_path
        self.as_name = as_name
        self.only_name = only_name
        self.is_library = is_library

class ForEachLoop:
    def __init__(self, index_var, value_var, collection, body):
        self.index_var = index_var
        self.value_var = value_var
        self.collection = collection
        self.body = body

class SliceNode:
    def __init__(self, start, end, step):
        self.start = start
        self.end = end
        self.step = step