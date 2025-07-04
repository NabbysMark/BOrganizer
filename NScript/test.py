import sys
from nscript.lexer import Lexer
from nscript.parser import Parser
from nscript.interpreter import Interpreter

def main():
    if len(sys.argv) < 2:
        print("Usage: python test.py <script.n>")
        return
    with open(sys.argv[1], "r", encoding="utf-8") as f:
        source = f.read()
    lexer = Lexer(source)
    parser = Parser(lexer)
    tree = parser.parse()
    interpreter = Interpreter()
    interpreter.interpret(tree)

if __name__ == "__main__":
    main()
