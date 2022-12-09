import unittest

from planner import Plan, create_plan

return_values = ['1', 2, (3,)]


class test_plan_executeTestCase(unittest.TestCase):

    def test_execute_empty(self):
        plan = Plan()
        plan.execute()

    def test_execute_with_functions(self):
        """execute plan and return the last action result"""

        class FunctionPlan(Plan):
            pass

        @FunctionPlan.register
        def registered_function():
            return return_values

        assert FunctionPlan.execute() == return_values

        FunctionPlan.register(lambda: None)

        assert FunctionPlan.execute() == None

    def test_execute_with_plan(self):
        """execute plan and return the last action result"""

        OuterPlan = create_plan('OuterPlan')
        InnerPlan = create_plan('InnerPlan')

        InnerPlan.register(lambda: return_values)

        OuterPlan.register(InnerPlan)

        assert OuterPlan.execute() == return_values

    @unittest.skip
    def test_execute_and_output(self):
        """output"""

        class OutPutPlan(Plan):
            actions = [
                lambda: None,
                lambda x: x,
            ]

            is_output = True

        OutPutPlan.execute()


if __name__ == '__main__':
    unittest.main()
