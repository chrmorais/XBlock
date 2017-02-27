"""
Test Scorable block.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

from unittest import TestCase

from mock import Mock

from xblock import scorable


class StubScorableBlock(scorable.ScorableXBlockMixin):
    """
    A very simple scorable block that needs no backing
    """
    location = 'Here'

    _allows_rescore = True

    def __init__(self, initial):
        self.result = initial
        self.runtime = Mock()

    def allows_rescore(self):
        return self._allows_rescore

    def get_score(self):
        return self.result

    def set_score(self, score):
        self.result = score

    def calculate_score(self):
        return scorable.Score(earned=1.6, total=2.0)


class ScorableXBlockTestCase(TestCase):
    def test_rescore(self):
        block = StubScorableBlock(scorable.Score(earned=0.0, total=1.0))
        block.rescore(only_if_higher=False)
        self.assertEqual(
            block.get_score(),
            scorable.Score(earned=1.6, total=2.0)
        )

    def test_not_yet_scored(self):
        block = StubScorableBlock(None)
        with self.assertRaises(ValueError):
            block.rescore(only_if_higher=False)

    def test_disallow_rescore(self):
        block = StubScorableBlock(scorable.Score(earned=0.0, total=1.0))
        block._allows_rescore = False
        with self.assertRaises(TypeError):
            block.rescore(only_if_higher=False)

    def test_rescore_if_higher_with_higher(self):
        block = StubScorableBlock(scorable.Score(earned=0.0, total=1.0))
        block.rescore(only_if_higher=True)
        self.assertEqual(
            block.get_score(),
            scorable.Score(earned=1.6, total=2.0)
        )

    def test_rescore_if_higher_with_lower(self):
        block = StubScorableBlock(scorable.Score(earned=2.0, total=2.0))
        block.rescore(only_if_higher=True)
        self.assertEqual(
            block.get_score(),
            scorable.Score(earned=2.0, total=2.0)
        )
