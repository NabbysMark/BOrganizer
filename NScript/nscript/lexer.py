NUMBER = 'NUMBER'
FLOAT = 'FLOAT'
DOUBLE = 'DOUBLE'
PLUS = 'PLUS'
MINUS = 'MINUS'
MULTIPLY = 'MULTIPLY'
DIVIDE = 'DIVIDE'
LPAREN = 'LPAREN'
RPAREN = 'RPAREN'
EOF = 'EOF'
FELLA = 'FELLA'
STRING = 'STRING'
YE = 'YE'
BOOM = 'BOOM'
ID = 'ID'
WHAT = 'WHAT'
WE = 'WE'
POW = 'POW'
IS = 'IS'
ISNOT = 'ISNOT'
UNDER = 'UNDER'
OVER = 'OVER'
ANOTHER = 'ANOTHER'
ANOTHER_ONE = 'ANOTHER_ONE'
AT = 'AT'
POPPIN = 'POPPIN'
RING = 'RING'
FEED = 'FEED'
RETURN = 'RETURN'
TRUE = 'TRUE'
FALSE = 'FALSE'
LBRACKET = 'LBRACKET'
RBRACKET = 'RBRACKET'
LBRACE = 'LBRACE'
RBRACE = 'RBRACE'
COLON = 'COLON'
SPIN = 'SPIN'
ASSIGN = 'ASSIGN'
HASH = 'HASH'
TALLBOY = 'TALLBOY'
ALSO = 'ALSO'
MAYBE = 'MAYBE'
NOT = 'NOT'
GIVE = 'GIVE'
ME = 'ME'
BUT = 'BUT'
ONLY = 'ONLY'
LEARNING = 'LEARNING'
HUNGRY = 'HUNGRY'
FOR = 'FOR'
CONVERTED = 'CONVERTED'
WAITING = 'WAITING'
BUILD = 'BUILD'
DOT = 'DOT'
LIBRARY = 'LIBRARY'
KILL = 'KILL'
SELF = 'SELF'
EXTENDING = 'EXTENDING'
WITH = 'WITH'
SUPERMAN = 'SUPERMAN'
INTERP_STRING = 'INTERP_STRING'
AS = 'AS'
IN = 'IN'

class Token:
    def __init__(self, type_, value, line=None, pos=None):
        self.type = type_
        self.value = value
        self.line = line
        self.pos = pos

    def __repr__(self):
        return f'Token({self.type}, {repr(self.value)}, line={self.line}, pos={self.pos})'

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        result = ''
        decimal_seen = False
        after_decimal = ''
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if decimal_seen:
                    break
                decimal_seen = True
                result += self.current_char
                self.advance()
                continue
            if decimal_seen:
                after_decimal += self.current_char
            result += self.current_char
            self.advance()
        if not decimal_seen:
            return Token(NUMBER, int(result), self.line, self.col)
        elif len(after_decimal) == 1:
            return Token(FLOAT, float(result), self.line, self.col)
        else:
            return Token(DOUBLE, float(result), self.line, self.col)

    def string(self):
        result = ''
        self.advance()
        while self.current_char is not None and self.current_char != '"':
            result += self.current_char
            self.advance()
        if self.current_char != '"':
            raise Exception("Unterminated string literal")
        self.advance()
        return Token(STRING, result, self.line, self.col)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            if self.current_char.isdigit():
                return self.number()
            if self.current_char == '+':
                self.advance()
                return Token(PLUS, '+', self.line, self.col)
            if self.current_char == '-':
                self.advance()
                return Token(MINUS, '-', self.line, self.col)
            if self.current_char == '*':
                self.advance()
                return Token(MULTIPLY, '*', self.line, self.col)
            if self.current_char == '/':
                next_pos = self.pos + 1
                if next_pos < len(self.text) and self.text[next_pos] == '/':
                    self.advance()
                    self.advance()
                    while self.current_char is not None and self.current_char != '\n':
                        self.advance()
                    continue
                else:
                    self.advance()
                    return Token(DIVIDE, '/', self.line, self.col)
            if self.current_char == '(':
                self.advance()
                return Token(LPAREN, '(', self.line, self.col)
            if self.current_char == ')':
                self.advance()
                return Token(RPAREN, ')', self.line, self.col)
            if self.current_char == '"':
                return self.string()
            if self.text[self.pos:].startswith("FELLA"):
                end = self.pos + 5
                if end == len(self.text) or not self.text[end].isalnum():
                    self.pos += 5
                    self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                    return Token(FELLA, "FELLA", self.line, self.col)
            if self.current_char == '[':
                self.advance()
                return Token(LBRACKET, '[', self.line, self.col)
            if self.current_char == ']':
                self.advance()
                return Token(RBRACKET, ']', self.line, self.col)
            if self.current_char == '{':
                self.advance()
                return Token(LBRACE, '{', self.line, self.col)
            if self.current_char == '}':
                self.advance()
                return Token(RBRACE, '}', self.line, self.col)
            if self.current_char == ':':
                self.advance()
                return Token(COLON, ':', self.line, self.col)
            if self.current_char == '#':
                self.advance()
                return Token(HASH, '#', self.line, self.col)
            if self.current_char == '.':
                self.advance()
                return Token(DOT, '.', self.line, self.col)
            if self.current_char.isalpha():
                ident = self._id()
                if ident == "IN":
                    return Token(IN, ident, self.line, self.col)
                elif ident == "EXTENDING":
                    return Token(EXTENDING, ident, self.line, self.col)
                elif ident == "WITH":
                    return Token(WITH, ident, self.line, self.col)
                elif ident == "SUPERMAN":
                    return Token(SUPERMAN, ident, self.line, self.col)
                elif ident == "KILL":
                    return Token(KILL, ident, self.line, self.col)
                elif ident == "SELF":
                    return Token(SELF, ident, self.line, self.col)
                elif ident == "GIVE":
                    return Token(GIVE, ident, self.line, self.col)
                elif ident == "ME":
                    return Token(ME, ident, self.line, self.col)
                elif ident == "BUT":
                    return Token(BUT, ident, self.line, self.col)
                elif ident == "ONLY":
                    return Token(ONLY, ident, self.line, self.col)
                elif ident == "NOT":
                    return Token(NOT, ident, self.line, self.col)
                elif ident == "ALSO":
                    return Token(ALSO, ident, self.line, self.col)
                elif ident == "MAYBE":
                    return Token(MAYBE, ident, self.line, self.col)
                elif ident == "TALL":
                    save_pos = self.pos
                    self.skip_whitespace()
                    lookahead = self.text[self.pos:self.pos+3]
                    if lookahead == "BOY":
                        self.pos += 3
                        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                        return Token(TALLBOY, "TALL BOY", self.line, self.col)
                    else:
                        self.pos = save_pos
                        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                elif ident == "SPIN":
                    return Token(SPIN, ident, self.line, self.col)
                elif ident == "IS":
                    return Token(IS, ident, self.line, self.col)
                elif ident == "true":
                    return Token(TRUE, True, self.line, self.col)
                elif ident == "false":
                    return Token(FALSE, False, self.line, self.col)
                elif ident == "YE":
                    return Token('YE', ident, self.line, self.col)
                elif ident == "BOOM":
                    return Token('BOOM', ident, self.line, self.col)
                elif ident == "WHAT":
                    return Token('WHAT', ident, self.line, self.col)
                elif ident == "WE":
                    return Token('WE', ident, self.line, self.col)
                elif ident == "POPPIN":
                    return Token(POPPIN, ident, self.line, self.col)
                elif ident == "POW":
                    return Token('POW', ident, self.line, self.col)
                elif ident == "RING":
                    return Token(RING, ident, self.line, self.col)
                elif ident == "FEED":
                    return Token(FEED, ident, self.line, self.col)
                elif ident == "return":
                    return Token(RETURN, ident, self.line, self.col)
                elif ident == "UNDER":
                    return Token('UNDER', ident, self.line, self.col)
                elif ident == "OVER":
                    return Token('OVER', ident, self.line, self.col)
                elif ident == "ANOTHER":
                    save_pos = self.pos
                    save_char = self.current_char
                    self.skip_whitespace()
                    lookahead = self.text[self.pos:self.pos+3]
                    if lookahead == "ONE":
                        self.pos += 3
                        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                        return Token('ANOTHER_ONE', "ANOTHER ONE", self.line, self.col)
                    else:
                        self.pos = save_pos
                        self.current_char = save_char
                        return Token('ANOTHER', ident, self.line, self.col)
                elif ident == "IS":
                    save_pos = self.pos
                    self.skip_whitespace()
                    lookahead = self.text[self.pos:self.pos+3]
                    if lookahead == "NOT":
                        self.pos += 3
                        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                        return Token(ISNOT, "IS NOT", self.line, self.col)
                    else:
                        self.pos = save_pos
                        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None
                        return Token('IS', ident, self.line, self.col)
                elif ident == "ISNOT":
                    return Token(ISNOT, "IS NOT", self.line, self.col)
                elif ident == "LEARNING":
                    return Token(LEARNING, ident, self.line, self.col)
                elif ident == "BUILD":
                    return Token(BUILD, ident, self.line, self.col)
                elif ident == "HUNGRY":
                    return Token(HUNGRY, ident, self.line, self.col)
                elif ident == "FOR":
                    return Token(FOR, ident, self.line, self.col)
                elif ident == "CONVERTED":
                    return Token(CONVERTED, ident, self.line, self.col)
                elif ident == "WAITING":
                    return Token(WAITING, ident, self.line, self.col)
                elif ident == "CONVERTSTRING":
                    return Token('CONVERTSTRING', ident, self.line, self.col)
                elif ident == "CONVERTNUMBER":
                    return Token('CONVERTNUMBER', ident, self.line, self.col)
                elif ident == "TYPEOF":
                    return Token('TYPEOF', ident, self.line, self.col)
                elif ident == "NOM":
                    return Token('NOM', ident, self.line, self.col)
                elif ident == "INPUT":
                    return Token('INPUT', ident, self.line, self.col)
                elif ident == "None":
                    return Token('NONE', ident, self.line, self.col)
                elif ident == "LIBRARY":
                    return Token(LIBRARY, ident, self.line, self.col)
                else:
                    return Token('ID', ident, self.line, self.col)
            if self.current_char == '@':
                self.advance()
                return Token(AT, '@', self.line, self.col)
            if self.current_char == ',':
                self.advance()
                return Token(',', ',', self.line, self.col)
            if self.current_char == '`':
                result = ''
                self.advance()
                while self.current_char is not None and self.current_char != '`':
                    result += self.current_char
                    self.advance()
                if self.current_char != '`':
                    raise Exception("Unterminated interpolated string")
                self.advance()
                return Token(INTERP_STRING, result, self.line, self.col)
            raise Exception(f'Invalid character: {self.current_char}')
        return Token('EOF', None, self.line, self.col)

    def _id(self):
        """Handle identifiers and keywords."""
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        return result