# -*- coding: utf-8 -*-

import sys
import itertools
import re
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set

#лексер булевой логики
TOKEN_SPEC = [
    ("SKIP",   r"[ \t\r\n]+"),
    ("ARROW",  r"->"),
    ("NOT",    r"!"),
    ("AND",    r"\*"),
    ("OR",     r"\+"),
    ("LP",     r"\("),
    ("RP",     r"\)"),
    ("ID",     r"[A-Za-z_][A-Za-z0-9_]*"),
    ("MISMATCH", r"."),
]
TOKEN_RE = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

@dataclass(frozen=True)
class Tok:
    typ: str
    val: str

def tokenize(s: str) -> List[Tok]:
    toks: List[Tok] = []
    for m in TOKEN_RE.finditer(s):
        typ = m.lastgroup
        val = m.group()
        if typ == "SKIP":
            continue
        if typ == "MISMATCH":
            raise ValueError(f"Лексическая ошибка: неожиданный символ {val!r}")
        toks.append(Tok(typ, val))
    return toks

# AST
@dataclass(frozen=True)
class Node: ...

@dataclass(frozen=True)
class Var(Node):
    name: str

@dataclass(frozen=True)
class Not(Node):
    x: Node

@dataclass(frozen=True)
class Bin(Node):
    op: str  # 'AND','OR','IMP'
    a: Node
    b: Node

class Parser:
    # приоритеты: !, *, +, ->
    def __init__(self, toks: List[Tok]):
        self.toks = toks
        self.i = 0

    #посмотреть текущий токен
    def peek(self) -> Optional[Tok]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    #проверка на ожидаемый тип
    def eat(self, typ: str) -> Tok:
        t = self.peek()
        if not t or t.typ != typ:
            got = t.typ if t else "EOF"
            raise ValueError(f"Синтаксическая ошибка: ожидалось {typ}, получено {got}")
        self.i += 1
        return t

    def parse(self) -> Node:
        node = self.parse_imp()
        if self.peek() is not None:
            raise ValueError(f"Синтаксическая ошибка: лишний токен {self.peek().val!r}")
        return node

    #импликация
    def parse_imp(self) -> Node:
        left = self.parse_or()
        t = self.peek()
        if t and t.typ == "ARROW":
            self.eat("ARROW")
            right = self.parse_imp()
            return Bin("IMP", left, right)
        return left

    #дизъюнкция
    def parse_or(self) -> Node:
        node = self.parse_and()
        while True:
            t = self.peek()
            if t and t.typ == "OR":
                self.eat("OR")
                node = Bin("OR", node, self.parse_and())
            else:
                break
        return node

    #конъюнкция
    def parse_and(self) -> Node:
        node = self.parse_not()
        while True:
            t = self.peek()
            if t and t.typ == "AND":
                self.eat("AND")
                node = Bin("AND", node, self.parse_not())
            else:
                break
        return node

    #отрицание
    def parse_not(self) -> Node:
        t = self.peek()
        if t and t.typ == "NOT":
            self.eat("NOT")
            return Not(self.parse_not())
        return self.parse_atom()

    def parse_atom(self) -> Node:
        t = self.peek()
        if not t:
            raise ValueError("Синтаксическая ошибка: неожиданный конец ввода")
        if t.typ == "ID":
            self.eat("ID")
            return Var(t.val)
        if t.typ == "LP":
            self.eat("LP")
            node = self.parse_imp()
            self.eat("RP")
            return node
        raise ValueError(f"Синтаксическая ошибка: неожиданный токен {t.val!r}")

#выражение Вход - формула (текст) Выход - дерево
def parse_expr(expr_text: str) -> Node:
    toks = tokenize(expr_text)
    return Parser(toks).parse()

#Сбор переменных
def collect_vars(node: Node, out: Set[str]) -> None:
    if isinstance(node, Var):
        out.add(node.name)
    elif isinstance(node, Not):
        collect_vars(node.x, out)
    elif isinstance(node, Bin):
        collect_vars(node.a, out); collect_vars(node.b, out)

#Вычисление формулы
def eval_node(node: Node, env: Dict[str, bool]) -> bool:
    if isinstance(node, Var):
        return bool(env.get(node.name, False))
    if isinstance(node, Not):
        return not eval_node(node.x, env)
    if isinstance(node, Bin):
        if node.op == "AND":
            return eval_node(node.a, env) and eval_node(node.b, env)
        if node.op == "OR":
            return eval_node(node.a, env) or eval_node(node.b, env)
        # -> = ! +
        if node.op == "IMP":
            return (not eval_node(node.a, env)) or eval_node(node.b, env)
    raise TypeError("Неизвестный тип узла AST")

#таблица истинности
def truth_table(expr_text: str) -> Tuple[List[str], List[Tuple[Dict[str, bool], bool]]]:
    ast = parse_expr(expr_text)
    vs: Set[str] = set()
    collect_vars(ast, vs)
    vars_ = sorted(vs)
    rows = []
    for bits in itertools.product([False, True], repeat=len(vars_)):
        env = dict(zip(vars_, bits))
        rows.append((env, eval_node(ast, env)))
    return vars_, rows

def is_tautology(expr_text: str) -> bool:
    _, rows = truth_table(expr_text)
    return all(out for _, out in rows)

def is_satisfiable(expr_text: str) -> bool:
    _, rows = truth_table(expr_text)
    return any(out for _, out in rows)

#База знаний (Хорн)
@dataclass
class HornRule:
    rid: int
    original_text: str
    antecedents: List[str]      # условия слева (and)
    consequent: str             # один вывод

    def cond_text(self) -> str:
        return "*".join(self.antecedents) if self.antecedents else ""

class MiniLogicKB:
    def __init__(self):
        self.facts: Set[str] = set() #A
        self.rules: List[HornRule] = [] #Ak
        self._next_rid = 1

    #очистить все правила и факты
    def clear(self):
        self.facts.clear()
        self.rules.clear()
        self._next_rid = 1

    # добавить факты
    def alp(self, arg: str):
        arg = arg.strip()
        if arg.startswith("[") and arg.endswith("]"):
            inner = arg[1:-1].strip()
            if not inner:
                return
            items = [x.strip() for x in inner.split(",")]
            for it in items:
                if it:
                    self._add_fact(it)
        else:
            self._add_fact(arg)

    def _add_fact(self, name: str):
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"Некорректное имя факта: {name}")
        self.facts.add(name)

    #добавить аксиому
    def axi(self, expr_text: str):
        """
        Разрешается форму:
          a*b -> c+d+e
        Интерпретация как сокращение:
          (a*b -> c), (a*b -> d), (a*b -> e)
        """
        expr_text = expr_text.strip()
        # Требуем импликацию на верхнем уровне
        ast = parse_expr(expr_text)
        if not (isinstance(ast, Bin) and ast.op == "IMP"):
            raise ValueError("axi(...) ожидает импликацию вида X -> Y")

        ants = self._extract_conj_atoms(ast.a)
        cons = self._extract_disj_atoms(ast.b)

        rid = self._next_rid
        self._next_rid += 1

        for c in cons:
            self.rules.append(HornRule(rid=rid, original_text=expr_text, antecedents=ants, consequent=c))

    def _extract_conj_atoms(self, node: Node) -> List[str]:
        # Разрешаем только конъюнкцию атомов (Var)
        atoms: List[str] = []
        def walk(n: Node):
            if isinstance(n, Var):
                atoms.append(n.name)
                return
            if isinstance(n, Bin) and n.op == "AND":
                walk(n.a); walk(n.b); return
            raise ValueError("В левой части правила допустимы только атомы, соединённые * (И)")
        walk(node)
        # Удалим дубли, сохранив порядок
        seen = set()
        out = []
        for a in atoms:
            if a not in seen:
                seen.add(a); out.append(a)
        return out

    def _extract_disj_atoms(self, node: Node) -> List[str]:
        # Разрешаем только дизъюнкцию атомов (Var)
        atoms: List[str] = []
        def walk(n: Node):
            if isinstance(n, Var):
                atoms.append(n.name); return
            if isinstance(n, Bin) and n.op == "OR":
                walk(n.a); walk(n.b); return
            raise ValueError("В правой части правила допустимы только атомы, соединённые + (ИЛИ)")
        walk(node)
        # Удалим дубли, сохранив порядок
        seen = set()
        out = []
        for a in atoms:
            if a not in seen:
                seen.add(a); out.append(a)
        return out

    def list_alp(self):
        print("A = { " + ", ".join(sorted(self.facts)) + " }")

    def list_axi(self):
        if not self.rules:
            print("(правил нет)")
            return
        for r in self.rules:
            left = "*".join(r.antecedents)
            print(f"   axi#{r.rid}: {r.original_text}  ::  {left} -> {r.consequent}")

    #вывод (правило P)
    def theorem(self, goal_text: str) -> bool:
        goal_text = goal_text.strip()
        goal_atoms = self._parse_goal_conj(goal_text)

        #все что уже известно как истинное
        derived: Set[str] = set(self.facts)
        derived_order: List[str] = []
        why: Dict[str, Tuple[Optional[HornRule], List[str]]] = {}

        for f in sorted(self.facts):
            derived_order.append(f)
            why[f] = (None, [])

        #прямой вывод
        changed = True
        while changed:
            changed = False
            for rule in self.rules:
                if rule.consequent in derived:
                    continue
                if all(a in derived for a in rule.antecedents):
                    derived.add(rule.consequent)
                    derived_order.append(rule.consequent)
                    why[rule.consequent] = (rule, list(rule.antecedents))
                    changed = True
        #доказано если все переменные есть в derived
        ok = all(g in derived for g in goal_atoms)
        self._print_trace(goal_atoms, ok, derived_order, why)
        return ok

    def _parse_goal_conj(self, text: str) -> List[str]:
        # goal: "a*b*c" (только конъюнкция атомов)
        text = text.strip()
        if not text:
            raise ValueError("Пустая цель theorem(...)")
        parts = [p.strip() for p in text.split("*")]
        if not parts or any(not p for p in parts):
            raise ValueError("Цель theorem(...) должна быть конъюнкцией атомов через *")
        for p in parts:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", p):
                raise ValueError(f"Некорректный атом в цели: {p}")
        # уникализируем, сохраняя порядок
        seen=set(); out=[]
        for p in parts:
            if p not in seen:
                seen.add(p); out.append(p)
        return out

    # Упрощённая сигнатура
    def _print_trace(self, goal_atoms, ok, derived, why):
        print("\n=== Трассировка вывода ===")
        print("Факты (A): " + (", ".join(sorted(self.facts)) if self.facts else "(нет)"))
        print("Правила (Ak):")
        if not self.rules:
            print("  (нет)")
        else:
            for r in self.rules:
                left = "*".join(r.antecedents)
                print(f"  axi#{r.rid}: {r.original_text}: {left} -> {r.consequent}")

        print("Выведено:")
        for x in derived:
            rule, conds = why.get(x, (None, []))
            if rule is None:
                print(f"  {x}  (дано)")
            else:
                cond_text = " & ".join(conds) if conds else ""
                print(f"  {x}  (из axi#{rule.rid}: {rule.original_text} при {cond_text})")

        print("Цель: " + " * ".join(goal_atoms))
        print("Результат: " + ("ИСТИНА" if ok else "ЛОЖЬ"))
        print("==========================\n")

#Команды
HELP_TEXT = """MiniLogic — справка.

Синтаксис выражений:
  Переменные: a, b, x1, Has_Passport
  Операции:  ! (НЕ), * (И), + (ИЛИ), -> (ИМПЛИКАЦИЯ), скобки ( )

База знаний:
  alp(name)                — добавить факт (элемент алфавита A)
  alp([a, b, c])           — добавить сразу несколько фактов
  axi(expr)                — добавить аксиому(ы) в виде Хорновых правил
                             Пример: axi(a*e -> b+c+d)  ⇒ (a*e→b), (a*e→c), (a*e→d)
  list_alp()               — показать все факты
  list_axi()               — показать все правила
  clear()                  — очистить базу знаний

Вывод (P):
  theorem(goal)            — проверить выводимость конъюнкции атомов
                             Пример: theorem(b*c)

Булева алгебра и таблицы истинности:
  truth(expr)              — вывести таблицу истинности
  equiv(e1, e2)            — проверить логическую эквивалентность
  laws()                   — проверить набор классических тождеств
  sat(expr)                — выполнима ли формула (есть ли строка, где она истинна)
  valid(expr)              — тавтология ли формула (истинна ли на всех строках)

Прочее:
  help()                   — эта справка
  quit / exit              — выход
"""

#вывод таблицы истинности
def cmd_truth(expr: str):
    vars_, rows = truth_table(expr)
    if not vars_:
        # константа
        out = rows[0][1]
        print(f"F\n-\n{1 if out else 0}")
        return
    print(" | ".join(vars_) + " | F")
    print("-" * (4 * len(vars_) + 3))
    for env, out in rows:
        line = " | ".join("1" if env[v] else "0" for v in vars_) + " | " + ("1" if out else "0")
        print(line)

#проверка эквивалентности
def cmd_equiv(arg: str):
    parts = [p.strip() for p in arg.split(",")]
    if len(parts) != 2:
        raise ValueError("equiv(e1, e2) ожидает два выражения через запятую")
    e1, e2 = parts
    vars1, rows1 = truth_table(e1)
    vars2, rows2 = truth_table(e2)
    vars_all = sorted(set(vars1) | set(vars2))

    def eval_on(expr: str, env: Dict[str, bool]) -> bool:
        return eval_node(parse_expr(expr), env)

    ok = True
    for bits in itertools.product([False, True], repeat=len(vars_all)):
        env = dict(zip(vars_all, bits))
        if eval_on(e1, env) != eval_on(e2, env):
            ok = False
            break
    print("Эквивалентны: " + ("ДА" if ok else "НЕТ"))

#проверка тождеств
def cmd_laws():
    # набор классических тождеств
    laws = [
        ("коммутативность_and", "a*b", "b*a"),
        ("коммутативность_or",  "a+b", "b+a"),
        ("дистрибутивность1",   "a*(b+c)", "a*b + a*c"),
        ("дистрибутивность2",   "a+b*c", "(a+b)*(a+c)"),
        ("идемпотентность_and", "a*a", "a"),
        ("идемпотентность_or",  "a+a", "a"),
        ("де_морган1",          "!(a*b)", "!a + !b"),
        ("де_морган2",          "!(a+b)", "!a * !b"),
        ("импликация",          "a->b", "!a + b"),
    ]
    print("Проверка тождеств булевой алгебры:")
    for name, e1, e2 in laws:
        # быстро: проверка эквивалентности
        vars_all = sorted(set(collect(e1)) | set(collect(e2)))
        ok = True
        for bits in itertools.product([False, True], repeat=len(vars_all)):
            env = dict(zip(vars_all, bits))
            if eval_node(parse_expr(e1), env) != eval_node(parse_expr(e2), env):
                ok = False
                break
        print(f"  {name:20s}: {'OK' if ok else 'FAIL'}   ({e1} ≡ {e2})")

def collect(expr: str) -> Set[str]:
    ast = parse_expr(expr)
    s: Set[str] = set()
    collect_vars(ast, s)
    return s

#выполнимость
def cmd_sat(expr: str):
    print("Выполнима: " + ("ДА" if is_satisfiable(expr) else "НЕТ"))

#тавтолгогия
def cmd_valid(expr: str):
    print("Тавтология: " + ("ДА" if is_tautology(expr) else "НЕТ"))

#разбирает строку на имя команды и аргумент
def parse_command(line: str) -> Tuple[str, str]:
    """
    Поддержка:
      name
      name()
      name(arg)
    """
    line = line.strip()
    # name(...) ?
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(\((.*)\))?$", line)
    if not m:
        raise ValueError("Не распознан ввод. Введите help() для справки.")
    name = m.group(1)
    has_parens = m.group(2) is not None
    arg = (m.group(3) or "").strip()
    # если без скобок, arg пуст
    if not has_parens:
        arg = ""
    return name, arg

def run_script(path: str):
    kb = MiniLogicKB()

    def help_():
        print(HELP_TEXT)

    # диспетчер
    def dispatch(name: str, arg: str):
        if name in ("quit", "exit"):
            raise SystemExit

        if name == "help":
            help_(); return
        if name == "clear":
            kb.clear(); print("Очищено."); return
        if name == "alp":
            kb.alp(arg); return
        if name == "axi":
            kb.axi(arg); return
        if name == "list_alp":
            kb.list_alp(); return
        if name == "list_axi":
            kb.list_axi(); return
        if name == "theorem":
            kb.theorem(arg); return
        if name == "truth":
            cmd_truth(arg); return
        if name == "equiv":
            cmd_equiv(arg); return
        if name == "laws":
            cmd_laws(); return
        if name == "sat":
            cmd_sat(arg); return
        if name == "valid":
            cmd_valid(arg); return

        raise ValueError(f"Неизвестная функция: {name}")

    # чтение файла
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            # убираем комментарии
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue
            print(f">> {line}")
            try:
                name, arg = parse_command(line)
                # разрешаем формы без аргументов без скобок: help / list_alp / list_axi / laws / clear
                if name in {"help", "list_alp", "list_axi", "laws", "clear"} and arg == "" and "(" not in line:
                    dispatch(name, "")
                else:
                    dispatch(name, arg)
            except SystemExit:
                return
            except Exception as e:
                print(f"Ошибка: {e}")

def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("Использование: python minilogic.py <script.txt>")
        return 2
    run_script(argv[1])
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
