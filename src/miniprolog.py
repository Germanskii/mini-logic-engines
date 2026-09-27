# -*- coding: utf-8 -*-
"""
MiniProlog — логическое программирование / исчисление предикатов:
- термы: Const, Var, Func
- предикаты/атомы: p(t1,...,tn)
- клаузы: факт (head.) и правило (head :- body1, body2.)
- вывод: SLD-резолюция (backward chaining) + унификация + подстановки
- трассировка шагов вывода
"""

import sys
import re
import itertools
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set, Iterable

# 1) Булева алгебра (из ПР1): !, *, +, ->, truth/equiv/laws

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

def tokenize_bool(s: str) -> List[Tok]:
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

@dataclass(frozen=True)
class Node: ...

@dataclass(frozen=True)
class VarB(Node):
    name: str

@dataclass(frozen=True)
class NotB(Node):
    x: Node

@dataclass(frozen=True)
class BinB(Node):
    op: str  # AND/OR/IMP
    a: Node
    b: Node

class ParserB:
    # ! * + ->
    def __init__(self, toks: List[Tok]):
        self.toks = toks
        self.i = 0

    def peek(self) -> Optional[Tok]:
        return self.toks[self.i] if self.i < len(self.toks) else None

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

    def parse_imp(self) -> Node:
        left = self.parse_or()
        t = self.peek()
        if t and t.typ == "ARROW":
            self.eat("ARROW")
            right = self.parse_imp()
            return BinB("IMP", left, right)
        return left

    def parse_or(self) -> Node:
        node = self.parse_and()
        while True:
            t = self.peek()
            if t and t.typ == "OR":
                self.eat("OR")
                node = BinB("OR", node, self.parse_and())
            else:
                break
        return node

    def parse_and(self) -> Node:
        node = self.parse_not()
        while True:
            t = self.peek()
            if t and t.typ == "AND":
                self.eat("AND")
                node = BinB("AND", node, self.parse_not())
            else:
                break
        return node

    def parse_not(self) -> Node:
        t = self.peek()
        if t and t.typ == "NOT":
            self.eat("NOT")
            return NotB(self.parse_not())
        return self.parse_atom()

    def parse_atom(self) -> Node:
        t = self.peek()
        if not t:
            raise ValueError("Синтаксическая ошибка: неожиданный конец ввода")
        if t.typ == "ID":
            self.eat("ID")
            return VarB(t.val)
        if t.typ == "LP":
            self.eat("LP")
            node = self.parse_imp()
            self.eat("RP")
            return node
        raise ValueError(f"Синтаксическая ошибка: неожиданный токен {t.val!r}")

def parse_bool(expr_text: str) -> Node:
    return ParserB(tokenize_bool(expr_text)).parse()

def collect_vars_bool(node: Node, out: Set[str]) -> None:
    if isinstance(node, VarB):
        out.add(node.name)
    elif isinstance(node, NotB):
        collect_vars_bool(node.x, out)
    elif isinstance(node, BinB):
        collect_vars_bool(node.a, out); collect_vars_bool(node.b, out)

def eval_bool(node: Node, env: Dict[str, bool]) -> bool:
    if isinstance(node, VarB):
        return bool(env.get(node.name, False))
    if isinstance(node, NotB):
        return not eval_bool(node.x, env)
    if isinstance(node, BinB):
        if node.op == "AND":
            return eval_bool(node.a, env) and eval_bool(node.b, env)
        if node.op == "OR":
            return eval_bool(node.a, env) or eval_bool(node.b, env)
        if node.op == "IMP":
            return (not eval_bool(node.a, env)) or eval_bool(node.b, env)
    raise TypeError("Неизвестный узел AST")

def truth_table(expr_text: str):
    ast = parse_bool(expr_text)
    vs: Set[str] = set()
    collect_vars_bool(ast, vs)
    vars_ = sorted(vs)
    rows = []
    for bits in itertools.product([False, True], repeat=len(vars_)):
        env = dict(zip(vars_, bits))
        rows.append((env, eval_bool(ast, env)))
    return vars_, rows

def is_tautology(expr_text: str) -> bool:
    _, rows = truth_table(expr_text)
    return all(out for _, out in rows)

def is_satisfiable(expr_text: str) -> bool:
    _, rows = truth_table(expr_text)
    return any(out for _, out in rows)

def cmd_truth(expr: str):
    vars_, rows = truth_table(expr)
    if not vars_:
        out = rows[0][1]
        print(f"F\n-\n{1 if out else 0}")
        return
    print(" | ".join(vars_) + " | F")
    print("-" * (4 * len(vars_) + 3))
    for env, out in rows:
        line = " | ".join("1" if env[v] else "0" for v in vars_) + " | " + ("1" if out else "0")
        print(line)

def cmd_equiv(arg: str):
    parts = [p.strip() for p in arg.split(",")]
    if len(parts) != 2:
        raise ValueError("equiv(e1, e2) ожидает два выражения через запятую")
    e1, e2 = parts
    vars1, _ = truth_table(e1)
    vars2, _ = truth_table(e2)
    vars_all = sorted(set(vars1) | set(vars2))

    ok = True
    for bits in itertools.product([False, True], repeat=len(vars_all)):
        env = dict(zip(vars_all, bits))
        if eval_bool(parse_bool(e1), env) != eval_bool(parse_bool(e2), env):
            ok = False
            break
    print("Эквивалентны: " + ("ДА" if ok else "НЕТ"))

def cmd_laws():
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
        vars_all = sorted(set(v for v,_ in []) | set())  # заглушка, ниже реальный сбор
        vs = set(); collect_vars_bool(parse_bool(e1), vs); collect_vars_bool(parse_bool(e2), vs)
        vars_all = sorted(vs)

        ok = True
        for bits in itertools.product([False, True], repeat=len(vars_all)):
            env = dict(zip(vars_all, bits))
            if eval_bool(parse_bool(e1), env) != eval_bool(parse_bool(e2), env):
                ok = False
                break
        print(f"  {name:20s}: {'OK' if ok else 'FAIL'}   ({e1} ≡ {e2})")

def cmd_sat(expr: str):
    print("Выполнима: " + ("ДА" if is_satisfiable(expr) else "НЕТ"))

def cmd_valid(expr: str):
    print("Тавтология: " + ("ДА" if is_tautology(expr) else "НЕТ"))


# 2) Исчисление предикатов: термы, атомы, клаузы, унификация

# Термы
@dataclass(frozen=True)
class Term: ...

@dataclass(frozen=True)
class Var(Term):
    name: str  # начинаем с заглавной буквы или '_' (как в Prolog)

@dataclass(frozen=True)
class Const(Term):
    name: str  # обычная константа/атом (нижний регистр)

@dataclass(frozen=True)
class Func(Term):
    name: str
    args: Tuple[Term, ...]

@dataclass(frozen=True)
class Atom:
    pred: str
    args: Tuple[Term, ...]

@dataclass
class Clause:
    cid: int
    head: Atom
    body: Tuple[Atom, ...]   # пусто = факт
    text: str

# Лексер/парсер для предикатов

P_TOKEN = re.compile(r"""
    (?P<SKIP>\s+)
  | (?P<COLON_DASH>:-)
  | (?P<LP>\()
  | (?P<RP>\))
  | (?P<COMMA>,)
  | (?P<DOT>\.)
  | (?P<ID>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<MISMATCH>.)
""", re.VERBOSE)

@dataclass(frozen=True)
class PTok:
    typ: str
    val: str

def p_tokenize(s: str) -> List[PTok]:
    out: List[PTok] = []
    for m in P_TOKEN.finditer(s):
        typ = m.lastgroup
        val = m.group()
        if typ == "SKIP":
            continue
        if typ == "MISMATCH":
            raise ValueError(f"Лексическая ошибка (предикаты): {val!r}")
        out.append(PTok(typ, val))
    return out

class PParser:
    def __init__(self, toks: List[PTok]):
        self.toks = toks
        self.i = 0

    def peek(self) -> Optional[PTok]:
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self, typ: str) -> PTok:
        t = self.peek()
        if not t or t.typ != typ:
            got = t.typ if t else "EOF"
            raise ValueError(f"Синтаксическая ошибка (предикаты): ожидалось {typ}, получено {got}")
        self.i += 1
        return t

    def parse_term(self) -> Term:
        t = self.peek()
        if not t or t.typ != "ID":
            raise ValueError("Ожидался терм")
        name = self.eat("ID").val
        # переменная: начинается с заглавной или '_'
        if name[0].isupper() or name[0] == "_":
            return Var(name)

        # функция/структура?
        if self.peek() and self.peek().typ == "LP":
            self.eat("LP")
            args: List[Term] = []
            if self.peek() and self.peek().typ != "RP":
                args.append(self.parse_term())
                while self.peek() and self.peek().typ == "COMMA":
                    self.eat("COMMA")
                    args.append(self.parse_term())
            self.eat("RP")
            return Func(name, tuple(args))

        return Const(name)

    def parse_atom(self) -> Atom:
        t = self.peek()
        if not t or t.typ != "ID":
            raise ValueError("Ожидался предикат")
        pred = self.eat("ID").val

        if not (self.peek() and self.peek().typ == "LP"):
            return Atom(pred, tuple())

        self.eat("LP")
        args: List[Term] = []
        if self.peek() and self.peek().typ != "RP":
            args.append(self.parse_term())
            while self.peek() and self.peek().typ == "COMMA":
                self.eat("COMMA")
                args.append(self.parse_term())
        self.eat("RP")
        return Atom(pred, tuple(args))

    def parse_clause(self) -> Tuple[Atom, Tuple[Atom, ...]]:
        head = self.parse_atom()
        if self.peek() and self.peek().typ == "COLON_DASH":
            self.eat("COLON_DASH")
            body: List[Atom] = []
            body.append(self.parse_atom())
            while self.peek() and self.peek().typ == "COMMA":
                self.eat("COMMA")
                body.append(self.parse_atom())
            return head, tuple(body)
        return head, tuple()

def parse_predicate_clause(text: str) -> Tuple[Atom, Tuple[Atom, ...]]:
    # уберём завершающую точку, если есть
    s = text.strip()
    if s.endswith("."):
        s = s[:-1].strip()
    pp = PParser(p_tokenize(s))
    head, body = pp.parse_clause()
    if pp.peek() is not None:
        raise ValueError(f"Лишние токены в конце: {pp.peek().val!r}")
    return head, body

def parse_query_atoms(text: str) -> Tuple[Atom, ...]:
    # запрос допускаем как список атомов через запятую: a(...), b(...)
    s = text.strip()
    if s.endswith("."):
        s = s[:-1].strip()
    toks = p_tokenize(s)
    pp = PParser(toks)
    atoms: List[Atom] = []
    atoms.append(pp.parse_atom())
    while pp.peek() and pp.peek().typ == "COMMA":
        pp.eat("COMMA")
        atoms.append(pp.parse_atom())
    if pp.peek() is not None:
        raise ValueError(f"Лишние токены в запросе: {pp.peek().val!r}")
    return tuple(atoms)

# Унификация / подстановка

Subst = Dict[str, Term]  # Var.name -> Term

def deref(t: Term, s: Subst) -> Term:
    # найти конечное значение переменной
    while isinstance(t, Var) and t.name in s:
        t = s[t.name]
    return t

def occurs(v: str, t: Term, s: Subst) -> bool:
    t = deref(t, s)
    if isinstance(t, Var):
        return t.name == v
    if isinstance(t, Func):
        return any(occurs(v, a, s) for a in t.args)
    return False

def unify(t1: Term, t2: Term, s: Subst) -> Optional[Subst]:
    t1 = deref(t1, s)
    t2 = deref(t2, s)

    if t1 == t2:
        return s

    if isinstance(t1, Var):
        # occurs-check можно оставить (без него иногда проще, но риск циклов)
        if occurs(t1.name, t2, s):
            return None
        s2 = dict(s); s2[t1.name] = t2
        return s2

    if isinstance(t2, Var):
        if occurs(t2.name, t1, s):
            return None
        s2 = dict(s); s2[t2.name] = t1
        return s2

    if isinstance(t1, Const) and isinstance(t2, Const):
        return s if t1.name == t2.name else None

    if isinstance(t1, Func) and isinstance(t2, Func):
        if t1.name != t2.name or len(t1.args) != len(t2.args):
            return None
        s2 = dict(s)
        for a, b in zip(t1.args, t2.args):
            s2 = unify(a, b, s2)
            if s2 is None:
                return None
        return s2

    return None

def unify_atom(a: Atom, b: Atom, s: Subst) -> Optional[Subst]:
    if a.pred != b.pred or len(a.args) != len(b.args):
        return None
    s2 = dict(s)
    for x, y in zip(a.args, b.args):
        s2 = unify(x, y, s2)
        if s2 is None:
            return None
    return s2

def apply_subst_term(t: Term, s: Subst) -> Term:
    t = deref(t, s)
    if isinstance(t, Var):
        return t
    if isinstance(t, Const):
        return t
    if isinstance(t, Func):
        return Func(t.name, tuple(apply_subst_term(a, s) for a in t.args))
    return t

def apply_subst_atom(a: Atom, s: Subst) -> Atom:
    return Atom(a.pred, tuple(apply_subst_term(t, s) for t in a.args))

def vars_in_atom(a: Atom) -> Set[str]:
    out: Set[str] = set()
    def walk(t: Term):
        t = deref(t, {})
        if isinstance(t, Var):
            out.add(t.name)
        elif isinstance(t, Func):
            for x in t.args:
                walk(x)
    for arg in a.args:
        walk(arg)
    return out

#  Стандартизация переменных (снятие кванторов)

def rename_term(t: Term, mapping: Dict[str, str]) -> Term:
    if isinstance(t, Var):
        return Var(mapping.get(t.name, t.name))
    if isinstance(t, Const):
        return t
    if isinstance(t, Func):
        return Func(t.name, tuple(rename_term(a, mapping) for a in t.args))
    return t

def rename_atom(a: Atom, mapping: Dict[str, str]) -> Atom:
    return Atom(a.pred, tuple(rename_term(t, mapping) for t in a.args))

def standardize_apart(cl: Clause, fresh_id: int) -> Clause:
    # переименуем все переменные в клаузе: X -> X__fresh_id
    all_vars: Set[str] = set()
    all_vars |= vars_in_atom(cl.head)
    for b in cl.body:
        all_vars |= vars_in_atom(b)
    mapping = {v: f"{v}__{fresh_id}" for v in all_vars}
    head2 = rename_atom(cl.head, mapping)
    body2 = tuple(rename_atom(b, mapping) for b in cl.body)
    return Clause(cid=cl.cid, head=head2, body=body2, text=cl.text)

#  База знаний + SLD-резолюция

class MiniPrologKB:
    def __init__(self):
        self.clauses: List[Clause] = []
        self._next_cid = 1
        self._fresh = 1

    def clear(self):
        self.clauses.clear()
        self._next_cid = 1
        self._fresh = 1

    def add_fact(self, atom_text: str):
        head, body = parse_predicate_clause(atom_text)
        if body:
            raise ValueError("fact(...) ожидает факт без ':-'")
        self.clauses.append(Clause(self._next_cid, head, tuple(), atom_text.strip()))
        self._next_cid += 1

    def add_rule(self, rule_text: str):
        head, body = parse_predicate_clause(rule_text)
        if not body:
            raise ValueError("rule(...) ожидает 'head :- body1, body2'")
        self.clauses.append(Clause(self._next_cid, head, body, rule_text.strip()))
        self._next_cid += 1

    def axi(self, text: str):
        # поддержим: head :- body...   ИЛИ   body -> head (с '*' как конъюнкция)
        s = text.strip()
        if ":-" in s:
            return self.add_rule(s)
        if "->" in s:
            left, right = [x.strip() for x in s.split("->", 1)]
            head = right
            body_atoms = [x.strip() for x in re.split(r"[\*,]", left) if x.strip()]
            body = ", ".join(body_atoms)
            return self.add_rule(f"{head} :- {body}.")
        raise ValueError("axi(...) ожидает 'head :- body' или 'body -> head'")

    def alp(self, text: str):
        # факты (можно несколько как в [a,b] — но для предикатов проще по одному)
        return self.add_fact(text)

    def list_all(self):
        if not self.clauses:
            print("(KB пуста)")
            return
        for c in self.clauses:
            if c.body:
                print(f"cl#{c.cid}: {pretty_atom(c.head)} :- {', '.join(pretty_atom(b) for b in c.body)}.")
            else:
                print(f"cl#{c.cid}: {pretty_atom(c.head)}.")

    def solve(self, query_text: str, trace: bool = True, max_solutions: int = 10, max_depth: int = 100):
        if max_depth < 1 or max_solutions < 1: raise ValueError('Лимиты должны быть положительными')
        self.max_depth = max_depth
        self.depth_exceeded = False
        goals0 = parse_query_atoms(query_text)
        query_vars = set().union(*(vars_in_atom(g) for g in goals0))

        if trace:
            print("=== SLD-вывод (трассировка) ===")
            print("Запрос:", ", ".join(pretty_atom(g) for g in goals0))

        sols = []
        for sol in self._prove(list(goals0), {}, trace=trace, depth=0):
            sols.append(sol)
            if len(sols) >= max_solutions:
                break

        if self.depth_exceeded:
            print('Достигнут лимит глубины: поиск неполон.')
        # печать результата
        if not sols:
            print('Результат: НЕИЗВЕСТНО (лимит поиска)' if self.depth_exceeded else 'Результат: ЛОЖЬ (решений нет)')
            return []

        # если запрос без переменных (ground), то достаточно одного решения
        if not query_vars:
            print("Результат: ИСТИНА")
            return sols

        print(f"Результат: ИСТИНА (найдено решений: {len(sols)})")
        for i, s in enumerate(sols, 1):
            # покажем только переменные исходного запроса
            items = []
            for v in sorted(query_vars):
                tv = apply_subst_term(Var(v), s)
                items.append(f"{v} = {pretty_term(tv)}")
            print(f"  Solution #{i}: " + ", ".join(items))

        return sols

    def _prove(self, goals: List[Atom], subst: Subst, trace: bool, depth: int) -> Iterable[Subst]:
        if not goals:
            yield subst
            return

        if depth >= getattr(self, 'max_depth', 100):
            self.depth_exceeded = True
            return
        # выбираем первую цель
        goal = apply_subst_atom(goals[0], subst)
        rest = goals[1:]

        if trace:
            print("  " * depth + f"- Цель: {pretty_atom(goal)}")

        for cl in self.clauses:
            # standardize apart
            cl2 = standardize_apart(cl, self._fresh)
            self._fresh += 1

            # пробуем унифицировать head с goal
            s2 = unify_atom(cl2.head, goal, subst)
            if s2 is None:
                continue

            # новые цели: body + rest
            new_goals = [apply_subst_atom(b, s2) for b in cl2.body] + [apply_subst_atom(r, s2) for r in rest]

            if trace:
                print("  " * depth + f"  Применяем cl#{cl.cid}: {cl.text.strip()}")
                # покажем изменившиеся подстановки (грубо)
                show = []
                for k in sorted(s2.keys()):
                    show.append(f"{k}={pretty_term(apply_subst_term(Var(k), s2))}")
                print("  " * depth + f"  Подстановка: {{ " + ", ".join(show) + " }}")
                if new_goals:
                    print("  " * depth + "  Новые цели: " + ", ".join(pretty_atom(g) for g in new_goals))
                else:
                    print("  " * depth + "  Новые цели: (пусто)")

            yield from self._prove(new_goals, s2, trace=trace, depth=depth+1)

def pretty_term(t: Term) -> str:
    if isinstance(t, Var):
        return t.name
    if isinstance(t, Const):
        return t.name
    if isinstance(t, Func):
        return f"{t.name}(" + ", ".join(pretty_term(a) for a in t.args) + ")"
    return str(t)

def pretty_atom(a: Atom) -> str:
    if not a.args:
        return a.pred
    return f"{a.pred}(" + ", ".join(pretty_term(t) for t in a.args) + ")"

# 3) CLI / команды сценария

HELP_TEXT = """MiniProlog — справка (ПР#2: исчисление предикатов)

Команды KB:
  clear
  fact(p(a,b))
  rule(h(X) :- b1(X), b2(X)).

  list_kb                  показать все клаузы (факты и правила)
  goal(q(X)).              выполнить запрос (SLD-вывод), вывести трассировку

Булева алгебра (как в ПР#1):
  truth(expr)
  equiv(e1, e2)
  laws
  sat(expr)
  valid(expr)

Замечания:
- Переменные: начинаются с заглавной буквы (X, User) или '_'
- Константы: с маленькой (u1, passport, ticket)
- Предикаты: p(...), can_board(...), has(...)
"""

def parse_command(line: str) -> Tuple[str, str]:
    line = line.strip().removesuffix('.').strip()
    m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(\((.*)\))?$", line)
    if not m:
        raise ValueError("Не распознан ввод. Введите help() для справки.")
    name = m.group(1)
    has_parens = m.group(2) is not None
    arg = (m.group(3) or "").strip()
    if not has_parens:
        arg = ""
    return name, arg

def run_script(path: str):
    kb = MiniPrologKB()

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue

            print(f">> {line}")
            try:
                name, arg = parse_command(line)

                if name in ("quit", "exit"):
                    return
                if name == "help":
                    print(HELP_TEXT); continue
                if name == "clear":
                    kb.clear(); print("Очищено."); continue

                # KB-команды
                if name == "fact":
                    kb.add_fact(arg); continue
                if name == "rule":
                    kb.add_rule(arg); continue
                if name == "axi":
                    kb.axi(arg); continue
                if name == "alp":
                    kb.alp(arg); continue
                if name == "list_kb":
                    kb.list_all(); continue
                if name == "goal":
                    kb.solve(arg, trace=True); continue

                # Булева алгебра
                if name == "truth":
                    cmd_truth(arg); continue
                if name == "equiv":
                    cmd_equiv(arg); continue
                if name == "laws":
                    cmd_laws(); continue
                if name == "sat":
                    cmd_sat(arg); continue
                if name == "valid":
                    cmd_valid(arg); continue

                raise ValueError(f"Неизвестная функция: {name}")

            except Exception as e:
                print(f"Ошибка: {e}")

def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("Использование: python miniprolog.py <script.txt>")
        return 2
    run_script(argv[1])
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
