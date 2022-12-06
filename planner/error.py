# -*- coding: utf-8 -*-
"""error - 异常处理包

#. 可以定位行号
#. 可以追溯异常错误

"""
from __future__ import annotations

import linecache
from typing import List, Tuple, Iterable

line_mask = (-2, -1, 0, 1, 2)

horizon_line = '-' * 80 + '\n'

error_line_mark = ' --> '
normal_line_mark = ' ' * len(error_line_mark)


def get_error_line(origin_exception: Exception):
    # reduce -> lambda in reduce -> execute_single_actions -> target function
    tb = origin_exception.__traceback__.tb_next.tb_next.tb_next
    target_line = tb.tb_frame.f_lineno - 1

    error_file_content = linecache.getlines(tb.tb_frame.f_code.co_filename)
    error_lines = [f'Package <{tb.tb_frame.f_globals["__name__"]}> File <{tb.tb_frame.f_code.co_filename}>\n']

    # target line = lineno + mask
    for line_index in map(lambda x: x + target_line, line_mask):
        if 0 <= line_index < len(error_file_content):
            # error_lines.append(error_file_content[line_index])
            error_lines.append(
                f'Line {str(line_index).rjust(3)} {"->" if line_index == target_line else " |"}{error_file_content[line_index]}')

    # format str
    return ''.join(error_lines)


class PlanException(Exception):

    def __init__(self, error_lines=5):
        self.error_lines: int = error_lines
        self.plan_trace: List[Tuple[Exception, object, List[str]]] = []

    def add_exception(self, plan, exception: Exception):
        """添加异常"""

        # reduce -> lambda in reduce -> execute_single_actions -> target function
        tb = exception.__traceback__.tb_next.tb_next.tb_next

        current_plan_actions = []
        for index, action in enumerate(plan.actions):
            action_name = f'{action.__self__.__name__}' if hasattr(action, "__self__") and isinstance(action.__self__,
                                                                                                      plan.__class__) and action.__name__ == 'execute' else action.__name__
            current_plan_actions.append(
                f'{error_line_mark if action.__name__ == tb.tb_frame.f_code.co_name else normal_line_mark} [{index + 1}] {action_name}')

        self.plan_trace.insert(0, (exception, plan, current_plan_actions,))

    def get_plan_trace(self, level=0) -> Iterable[str]:
        """获取Plan的路径"""
        if len(self.plan_trace) > level:
            _, plan, action_lines = self.plan_trace[level]

            level_0_syntax = ' |' if level else ''
            syntax_content = ' ' * (level * 4)
            target_syntax_content = ' ---' * level

            if not level:
                yield f'Plan <{plan.__name__}> execute:'

            for action_line in action_lines:
                if action_line.startswith(error_line_mark):
                    yield f'|{target_syntax_content}{level_0_syntax}{action_line}'

                    yield from self.get_plan_trace(level + 1)
                else:
                    yield f'|{syntax_content}{level_0_syntax}{action_line}'

    def __str__(self):
        origin_error = self.plan_trace[-1][0]

        error_content = get_error_line(origin_error)

        error_hand = f'Raise [{origin_error.__class__.__name__}]. Message:{str(origin_error)}\n'

        plan_content = '\n'.join(list(self.get_plan_trace()))

        return f'{error_hand}{horizon_line}{plan_content}\n{horizon_line}{error_content}'
