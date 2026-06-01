#!/usr/bin/env python3
# Sand Interpreter, pre-bundled with Notation and notateOS.
#
# Sand is a simple scripting language designed to be easy to use,
# learn, and extend. It can also be used for frameworks, applications,
# and app bundles on notateOS.
#
# Written by *mostly by Kankavee Tarnprasant,
# Lead Developer of notateOS and Founder of Astrais Corporations.
#
# Licensed under the MIT License.
# Copyright (c) 2026 Astrais Corporations.

from io import StringIO
from contextlib import redirect_stdout # kankavee is too lazy to remove these so nah

import ast
import inspect
import os
import sys

# states
variables = {}
functions = {}


class ReturnException(Exception):
    """Custom exception used to go back when return() is used"""
    def __init__(self, value):
        self.value = value


def split_arguments(argstr):
    if not argstr:
        return []

    args = []
    current = []

    inside_quotes = False
    quote_char = None

    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    for char in argstr:
        # Handle strings
        if char in ('"', "'"):
            if not inside_quotes:
                inside_quotes = True
                quote_char = char
            elif quote_char == char:
                inside_quotes = False
                quote_char = None

            current.append(char)
            continue

        if not inside_quotes:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1

            elif char == "[":
                bracket_depth += 1
            elif char == "]":
                bracket_depth -= 1

            elif char == "{":
                brace_depth += 1
            elif char == "}":
                brace_depth -= 1

            elif (
                char == ","
                and paren_depth == 0
                and bracket_depth == 0
                and brace_depth == 0
            ):
                value = "".join(current).strip()
                if value:
                    args.append(value)
                current = []
                continue

        current.append(char)

    value = "".join(current).strip()
    if value:
        args.append(value)

    return args


def evaluate_argument(arg):
    arg = arg.strip()
    if not arg:
        return None

    if arg.startswith('"') and arg.endswith('"'):
        return arg[1:-1]

    if arg in variables:
        return variables[arg]

    # Function call syntax: name(...)
    if "(" in arg and arg.endswith(")"):
        cmd, argstr = arg.split("(", 1)
        return execute_command(cmd.strip(), argstr[:-1])

    try:
        return ast.literal_eval(arg)
    except (ValueError, SyntaxError):
        print(f"NameError: name '{arg}' was not found in scope.")
        return None


def register_python_function(name, func):
    """Makes Python Libraries able to register functions too"""
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    functions[name] = (param_names, func)


def execute_command(cmd, argstr):
    """Executes a command"""
    cmd = cmd.strip()
    args = split_arguments(argstr)

    # Check if it's a registered user function or Python-interop function
    if cmd in functions:
        param_names, body_or_callable = functions[cmd]
        evaluated_args = [evaluate_argument(arg) for arg in args]

        # Scenario A: The function was registered by a Python library module
        if callable(body_or_callable):
            try:
                result = body_or_callable(*evaluated_args[: len(param_names)])
                if result is not None:
                    variables["_"] = result
                return result
            except Exception as e:
                print(f"PyError: Runtime error in Python function '{cmd}': {e}")
            return None

        # Scenario B: The function is a native Sand script block structure
        previous_vars = variables.copy()

        for i, param in enumerate(param_names):
            if i < len(evaluated_args):
                variables[param] = evaluated_args[i]
            else:
                variables[param] = None

        return_value = None
        try:
            run_source(body_or_callable)
        except ReturnException as e:
            return_value = e.value

        for key in list(variables.keys()):
            if key in previous_vars:
                variables[key] = previous_vars[key]
            else:
                del variables[key]

        if return_value is not None:
            variables["_"] = return_value
        return return_value

    # Native Commands
    if cmd == "printf":
        out = [str(evaluate_argument(arg)) for arg in args]
        print(*out)

    elif cmd == "return":
        val = evaluate_argument(args[0]) if args else None
        raise ReturnException(val)

    elif cmd == "input":
        if len(args) == 1:
            varname = args[0].strip('"')
            variables[varname] = input()
        else:
            print("IOError (Input): input() expects exactly 1 argument (variable name)")

    elif cmd == "getlib":
        if not args:
            print("SyntaxError, FileNotFoundError: getlib() expects a library path")
            return

        libname = args[0].strip('"')
        search_paths = [libname, f"/usr/lib/sand/Libraries/{libname}"]
        file_found = False

        for path in search_paths:
            if os.path.exists(path):
                file_found = True
                try:
                    if path.endswith(".py"):
                        with open(path, "r", encoding="utf-8") as f:
                            python_code = f.read()

                        current_globals = sys.modules[__name__].__dict__
                        current_globals[
                            "register_function"
                        ] = register_python_function
                        current_globals["sand_variables"] = variables
                        current_globals["sand_functions"] = functions

                        exec(python_code, current_globals)
                    else:
                        with open(path, "r", encoding="utf-8") as f:
                            run_source(f.read())
                    break
                except Exception as e:
                    print(f"PyError: error while executing library at {path}: {e}")
                    return

        if not file_found:
            print(f"LibraryError, FileNotFoundError: File '{libname}' not found'")
    
    else:
        print(f"SyntaxError: command {cmd} not found")
    return None


def parse_and_run(chunk):
    """Processes an isolated command token/block chunk."""
    chunk = chunk.strip()
    if not chunk or chunk.startswith("#"):
        return

    # Modern Assignment Syntax: x = value OR setvar x value
    if "=" in chunk and not chunk.replace(" ", "").startswith("func"):
        parts = chunk.split("=", 1)
        name = parts[0].strip()
        
        if name.isidentifier():
            raw_value = parts[1].strip()
            variables[name] = evaluate_argument(raw_value)
            return

    if chunk.startswith("setvar "):
        parts = chunk.split(None, 2)
        if len(parts) < 3:
            print("SyntaxError: setvar expects a variable name and a value expression.")
            return
        name = parts[1]
        raw_value = parts[2]
        if name.isidentifier():
            variables[name] = evaluate_argument(raw_value)
        else:
            print(f"SyntaxError: '{name}' is not a valid variable name.")
        return

    if "{" in chunk and chunk.replace(" ", "").endswith("}"):
        header, body = chunk.split("{", 1)
        header = header.strip()
        body = body[:-1].strip()

        if header.startswith("func "):
            func_declaration = header[5:].strip()
            if "(" in func_declaration and func_declaration.endswith(")"):
                f_name, f_args_str = func_declaration.split("(", 1)
                f_name = f_name.strip()
                f_args_str = f_args_str[:-1]
                f_params = [p.strip() for p in f_args_str.split(",") if p.strip()]
                functions[f_name] = (f_params, body)
            else:
                functions[func_declaration] = ([], body)
            return

        if " " in header:
            cmd, remaining = header.split(None, 1)
            execute_command(cmd, f"{remaining} {body}")
        else:
            execute_command(header, body)

    elif "(" in chunk and chunk.endswith(")"):
        cmd, argstr = chunk.split("(", 1)
        execute_command(cmd, argstr[:-1])

    else:
        parts = chunk.split(None, 1)
        if not parts:
            return
        cmd = parts[0]
        argstr = parts[1] if len(parts) > 1 else ""
        execute_command(cmd, argstr)


def run_source(source):
    """Breaks down source text into standalone statements or complete brace blocks."""
    buffer = []
    brace_count = 0

    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if brace_count == 0:
                continue

        buffer.append(line)
        brace_count += stripped.count("{")
        brace_count -= stripped.count("}")

        if brace_count == 0 and buffer:
            combined = "\n".join(buffer)
            parse_and_run(combined)
            buffer = []

    if brace_count != 0:
        print("SyntaxError: Unbalanced curly braces detected.")


def repl():
    """Launches the interactive shell."""
    print("Sand Interpreter")
    print("Type Ctrl+C or Ctrl+D to exit.")

    buffer = []
    brace_count = 0

    while True:
        try:
            prompt = "sand > " if brace_count == 0 else "  > "
            line = input(prompt)

            stripped = line.strip()
            buffer.append(line)
            brace_count += stripped.count("{")
            brace_count -= stripped.count("}")

            if brace_count == 0 and buffer:
                try:
                    run_source("\n".join(buffer))
                except ReturnException:
                    print("SyntaxError: return statement outside of function.")
                buffer = []

        except (KeyboardInterrupt, EOFError):
            print("\nKeyboardInterrupt / EOF: Exiting shell.")
            sys.exit(0)


# Engine Entry Point Execution
if len(sys.argv) > 1:
    filename = sys.argv[1]
    try:
        with open(filename, "r", encoding="utf-8") as f:
            run_source(f.read())
    except ReturnException:
        print("SyntaxError: return statement outside of function.")
    except FileNotFoundError:
        print(f"FileNotFoundError: Script file '{filename}' not found.")
    except PermissionError:
        print(f"PermissionError: Permission denied accessing '{filename}'.")
else:
    repl()
    
# to the other developers reading this:
# A voice is calling to me, to set me free!

# …but first I need to charge my phone,
# My battery’s at three percent alone!
# The rain is pouring, Wi-Fi’s gone,
# And somehow you still carry on!

# Test of my faith!
# Why are you still posting this?
# Test of my faith!
# The group chat’s now an abyss!

# The rain keeps falling, line by line,
# The message count is ninety-nine!
# I beg the heavens from above:
# PLEASE SEND SOMETHING ELSE, MY HUMBLE LITTLE DEVS!
# - kankavee
