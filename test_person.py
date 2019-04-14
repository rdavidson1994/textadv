from unittest import TestCase


class TestPerson(TestCase):
    def test_learn_spell(self):
        from spells import Sleep
        from world import ActorTest
        env = ActorTest()
        env.actor.learn_spell(Sleep)
        assert Sleep in env.actor.spells_known