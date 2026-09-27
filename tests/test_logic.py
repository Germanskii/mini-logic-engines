import contextlib
import io
import unittest
from src import minilogic as ml, miniprolog as mp

class LogicTest(unittest.TestCase):
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
