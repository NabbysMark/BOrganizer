import sys
import os
import webbrowser
from nscript.lexer import Lexer
from nscript.parser import Parser
from nscript.interpreter import Interpreter

VERSION = "1.1.0"

def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-v", "--version"):
        print(f"NScript version {VERSION}")
        return
    if len(sys.argv) == 2 and sys.argv[1] in ("--docs", "-d"):
        docs_path = os.path.join(os.path.dirname(__file__), "docs.html")
        if os.path.exists(docs_path):
            webbrowser.open(f"file://{os.path.abspath(docs_path)}")
            print("Opened documentation in your default browser.")
        else:
            print("Documentation file 'docs.html' not found.")
        return
    if len(sys.argv) == 2 and sys.argv[1].lower().endswith('.n'):
        filename = sys.argv[1]
        with open(filename, "r", encoding="utf-8") as f:
            code = f.read()
        lexer = Lexer(code)
        parser = Parser(lexer)
        tree = parser.parse()
        interpreter = Interpreter()
        interpreter.interpret(tree)
    else:
        print("NScript Interactive Console (type 'exit' to quit)")
        interpreter = Interpreter()
        while True:
            try:
                line = input(">>> ")
                if line.strip().lower() == "exit":
                    break
                lexer = Lexer(line)
                parser = Parser(lexer)
                tree = parser.parse()
                interpreter.interpret(tree)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()