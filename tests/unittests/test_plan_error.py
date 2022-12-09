import unittest

from planner import create_plan


def empty():
    pass


def normal_error():
    {}[1]


class TestPlanErrorTestCase(unittest.TestCase):

    def test_level_1_error(self):
        plan = create_plan()

        plan.register(lambda: None)
        plan.register(normal_error)
        plan.register(lambda: None)

        with self.assertRaises(Exception) as e:
            plan.execute()

        print(e.exception)

    def test_level_2_error(self):
        inner_plan = create_plan('inner_plan')

        inner_plan.register(lambda: None)
        inner_plan.register(normal_error)
        inner_plan.register(lambda: None)

        plan = create_plan('plan')

        plan.register(create_plan('inner_normal', actions=[lambda: None]))
        plan.register(inner_plan)
        plan.register(lambda: None)

        with self.assertRaises(Exception) as e:
            plan.execute()

        print(e.exception)

    def test_level_3_error(self):
        level_3_plan = create_plan('level_3_plan')

        level_3_plan.register(lambda: None)
        level_3_plan.register(normal_error)
        level_3_plan.register(empty)

        level_2_plan = create_plan('level_2_plan')

        level_2_plan.register(empty)
        level_2_plan.register(level_3_plan)
        level_2_plan.register(lambda: None)

        level_1_plan = create_plan('level_1_plan')

        level_1_plan.register(lambda: None)
        level_1_plan.register(level_2_plan)
        level_1_plan.register(lambda: None)

        with self.assertRaises(Exception) as e:
            level_1_plan.execute()

        print(e.exception)


if __name__ == '__main__':
    unittest.main()
