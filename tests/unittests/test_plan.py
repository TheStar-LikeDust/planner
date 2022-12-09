import unittest

from planner import create_plan, Plan


class test_planTestCase(unittest.TestCase):

    def test_plan(self):
        """Plan class have own actions."""

        class PlanA(Plan):
            pass

        class PlanB(Plan):
            pass

        assert id(PlanA.actions) != id(PlanB.actions)

        class PlanAA(PlanA):
            pass

        assert id(PlanAA.actions) != id(PlanA.actions)

    def test_create_plan(self):
        """creat_plan() function"""
        with self.subTest('create plan class'):
            plan = create_plan()

            isinstance(plan, Plan)
            issubclass(plan, Plan)

        with self.subTest('create plan with name'):
            plan_name = 'plan_name'
            plan = create_plan(plan_name)

            assert plan.__name__ == plan_name

    def test_create_plan_with_actions(self):
        """create_plan with actions"""
        plan = create_plan(actions=[
            lambda: 1,
        ])

        assert plan.execute() == 1

        with self.subTest('multi level'):
            level_2_plan = create_plan(
                actions=[
                    lambda: None,
                    plan,

                ])

            assert level_2_plan.execute() == 1


if __name__ == '__main__':
    unittest.main()
