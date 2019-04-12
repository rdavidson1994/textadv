from unittest import TestCase


class TestPerson(TestCase):
    def test_learn_spell(self):
        from spells import StunWave
        from world import ActorTest
        env = ActorTest()
        env.actor.learn_spell(StunWave)
        assert StunWave in env.actor.spells_known