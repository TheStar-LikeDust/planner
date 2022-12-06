import unittest
from unittest.mock import MagicMock

from planner import Plan, create_plan

return_value = {1: '1', '2': 2}


def return_action():
    return return_value


def check_value_action(the_arg_name_is_xxx):
    assert the_arg_name_is_xxx == return_value


def empty_action():
    pass


def execute_parameter_checker(**kwargs):
    assert kwargs['ident']
    assert kwargs['info']


def check_result(**kwargs):
    assert kwargs['result']
    return kwargs['result']


class test_plan_pipelineTestCase(unittest.TestCase):

    def test_pass_value(self):
        """pass result between actions"""
        plan = create_plan()

        plan.register(return_action)
        plan.register(check_value_action)

        plan.execute()

    def test_receive_execute_parameter(self):
        """receive execute_parameter from Plan"""
        execute_parameter = {
            'ident': 10,
            'info': 'info_message'
        }

        plan = create_plan()

        with self.subTest('checker'):
            plan.register(execute_parameter_checker)

            plan.execute(**execute_parameter)

        with self.subTest('inner plan with checker'):
            inner_plan = create_plan()
            inner_plan.register(execute_parameter_checker)

            plan.register(inner_plan)
            plan.execute(**execute_parameter)

    def test_pass_result_between_var_keyword(self):
        """pass result"""

        with self.subTest('return_and_check'):
            plan = create_plan('return_and_check')

            plan.register(return_action)
            plan.register(check_result)

            assert plan.execute() == return_value

        with self.subTest('result from plan'):
            plan = create_plan('result from plan')

            plan.register(empty_action)
            plan.register(create_plan(actions=[return_action, check_result]))
            plan.register(check_result)

            plan.execute()

        with self.subTest('result to plan'):
            plan = create_plan('result to plan')

            plan.register(return_action)
            plan.register(create_plan(actions=[check_result]))
            plan.register(check_result)

            plan.execute()


if __name__ == '__main__':
    unittest.main()
