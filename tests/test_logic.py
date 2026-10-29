import contextlib
import io
import unittest
from src import minilogic as ml, miniprolog as mp

class LogicTest(unittest.TestCase):
    def test_anonymous_variables_are_independent(self):
        kb = mp.MiniPrologKB()
        kb.add_fact('pair(alice,bob).')
        kb.add_rule('any_pair :- pair(_,_).')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(len(kb.solve('pair(_,_)', trace=False)), 1)
            self.assertEqual(kb.solve('pair(_Same,_Same)', trace=False), [])
            self.assertEqual(len(kb.solve('any_pair', trace=False)), 1)

    def test_anonymous_bindings_are_not_reported(self):
        kb = mp.MiniPrologKB()
        kb.add_fact('pair(alice,bob).')
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            solutions = kb.solve('pair(_,Who)', trace=False)
        self.assertEqual(mp.apply_subst_term(mp.Var('Who'), solutions[0]), mp.Const('bob'))
        self.assertIn('Who = bob', capture.getvalue())
        self.assertNotIn('$anonymous', capture.getvalue())

    def test_boolean_laws(self):
        self.assertTrue(ml.is_tautology('a+!a'))
        self.assertFalse(ml.is_satisfiable('a*!a'))
    def test_occurs_check(self):
        self.assertIsNone(mp.unify(mp.Var('X'),mp.Func('f',(mp.Var('X'),)),{}))
    def test_substitution(self):
        kb=mp.MiniPrologKB()
        kb.add_fact('parent(alice,bob).');kb.add_fact('parent(bob,carol).')
        kb.add_rule('grandparent(X,Z) :- parent(X,Y), parent(Y,Z).')
        with contextlib.redirect_stdout(io.StringIO()): sols=kb.solve('grandparent(alice,Z)',trace=False)
        self.assertEqual(mp.pretty_term(mp.apply_subst_term(mp.Var('Z'),sols[0])),'carol')
    def test_depth_exhaustion_is_unknown(self):
        kb=mp.MiniPrologKB();kb.add_rule('loop(X) :- loop(X).')
        capture=io.StringIO()
        with contextlib.redirect_stdout(capture): sols=kb.solve('loop(a)',trace=False,max_depth=5)
        self.assertEqual(sols,[])
        self.assertIn('НЕИЗВЕСТНО',capture.getvalue())
