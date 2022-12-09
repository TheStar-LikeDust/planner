import unittest

from planner import Plan, create_plan


class Ins():

    def call(self, **kwargs):
        return kwargs.get('action_mapper')


ins = Ins()


class test_plan_parameterTestCase(unittest.TestCase):

    def test_action_mapper(self):
        """获取action_mapper"""

        class NormalPlan(Plan):
            actions = [
                lambda **kwargs: None,
                ins.call
            ]

        action_mapper = NormalPlan.execute()

        assert isinstance(action_mapper, dict)
        assert action_mapper.get('Ins')
        assert action_mapper.get('Ins') is ins

        normal_plan = create_plan(actions=[ins.call])

        action_mapper = normal_plan.execute()

        assert isinstance(action_mapper, dict)
        assert action_mapper.get('Ins')
        assert action_mapper.get('Ins') is ins

    def test_multi_level_plan(self):
        """多层"""
        level_1 = create_plan('level_1')
        level_2 = create_plan('level_2')

        level_1.register(lambda: None)
        level_1.register(ins.call)

        level_2.register(level_1)

        assert level_1.execute()
        action_mapper = level_2.execute()

        assert isinstance(action_mapper, dict)
        assert action_mapper.get('Ins')
        assert action_mapper.get('Ins') is ins


if __name__ == '__main__':
    unittest.main()
