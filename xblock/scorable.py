"""
Scorable.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from collections import namedtuple
import six


Score = namedtuple('Score', ['earned', 'total'])


class ScorableXBlockMixin(object):
    """
    Mixin to handle functionality related to scoring.

    Provides the following public methods:

        ScorableXBlockMixin.rescore(self, only_if_higher)
            Calculate a new score and save it to the block.
            `only_if_higher

        ScorableXBlockMixin.allows_rescore(self) -> bool
            Returns True if the block can be rescored.

    Subclasses must define the following:

        ScorableXBlockMixin.get_score(self)
            Return the currently saved score.  Must not calculate a new score.

        ScorableXBlockMixin.set_score(self, score)
            Set the score on the block to the specified value

        ScorableXBlockMixin.calculate_score(self, score)
            Calculate a new score based on the state of the block.  Must not
            update any values on the block.
    """

    def rescore(self, only_if_higher):
        """
        Calculate a new score and save it to the block.  If only_if_higher is
        True and the score didn't improve, keep the existing score.

        Returns True if the score was changed.
        Returns False if the score was not changed.
        Raises a TypeError if the block cannot be scored.
        Raises a ValueError if the user has not yet completed the problem.
        """

        _ = self.runtime.service(self, 'i18n').ugettext
        if not self.allows_rescore():
            self._publish_scoring_event('rescore_failure', {'failure': 'unsupported'})
            raise TypeError(_('Problem does not support rescoring'))

        original_score = self.get_score()
        if original_score is None:
            self._publish_scoring_event('rescore_failure', {'failure': 'unanswered'})
            raise ValueError(_('Problem must be answered before it can be rescored.'))

        try:
            new_score = self.calculate_score()
        except Exception:  # pylint: disable=broad-except
            self._publish_scoring_event('rescore_failure', {'failure': 'calculation error'})
            return False

        if not only_if_higher or new_score > original_score:
            self.set_score(new_score)
            self._publish_grade(only_if_higher)
            self._publish_scoring_event(
                'rescore_result',
                {
                    'result': 'score updated',
                    'original_score': original_score._asdict(),  # pylint: disable=protected-access
                    'new_score': new_score._asdict(),  # pylint: disable=protected-access
                }
            )
            return True
        else:
            self._publish_scoring_event(
                'rescore_result',
                {
                    'result': 'score not changed',
                    'original_score': original_score._asdict(),  # pylint: disable=protected-access
                    'new_score': new_score._asdict(),  # pylint: disable=protected-access
                }
            )
            return False

    def _publish_grade(self, only_if_higher=None):
        """
        Publish a grade to the runtime.
        """
        score = self.get_score()
        grade_dict = {
            'value': score.earned,
            'max_value': score.total,
        }
        if only_if_higher is not None:
            grade_dict['only_if_higher'] = only_if_higher
        self.runtime.publish('grade', grade_dict)

    def _publish_scoring_event(self, name, data):
        """
        Publish an event related to scoring.
        """
        logged = {}  # Ensure we don't mutate our arguments
        logged.update(data)
        logged.update(self._base_event_info())
        self.runtime.publish(name, logged)

    def _base_event_info(self):
        """
        Return a dictionary containing information that belongs on any logged
        events.
        """
        return {
            'usage_key': six.text_type(self.location)
        }

    def allows_rescore(self):
        """
        Boolean value: Can this problem be rescored.
        """
        return True

    def get_score(self):
        """
        Return a score already persisted on the XBlock.

        Returns:
            Score(earned=float, total=float)_
        """
        raise NotImplementedError

    def set_score(self, score):
        """
        Persist a score to the XBlock.  The score is a named tuple with a
        score attribute and a total, reflecting the earned score, and the
        maximum the student could have earned.

        Arguments:
            score: Score(earned=float, total=float)

        Returns:
            None
        """
        raise NotImplementedError

    def calculate_score(self):
        """
        Calculate a new score based on the state of the problem.
        This method should should not modify the state of the
        XBlock.

        Returns:
            Score(earned=float, total=float)
        """
