# -*- coding: utf-8 -*-
"""error - 异常处理包

#. 可以定位行号
#. 可以追溯异常错误

"""
from __future__ import annotations

import linecache
from types import FunctionType, MethodType
from typing import List, Tuple, Iterable

line_mask = (-2, -1, 0, 1, 2)

horizon_line = '-' * 80 + '\n'

error_line_mark = ' --> '
normal_line_mark = ' ' * len(error_line_mark)


def get_action_name(action):
    """获取一个函数/方法信息"""
    # FIXME: import and other type
    from planner.core import PlanMeta

    if isinstance(action, PlanMeta):
        return f'(Plan) {action.__name__}'
    # 函数
    elif isinstance(action, FunctionType):
        return f'(Function) {action.__name__}'
    # 实例方法
    elif isinstance(action, MethodType):
        self = action.__self__
        # 类方法
        if isinstance(self, type):
            return f'(Class method) {self.__name__}'
        # 实例方法
        else:
            return f'(Object) {self.__class__.__name__}'
    else:
        return f'(Other) {str(action)}'


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

    def __init__(self, origin_exception: Exception, origin_plan, error_lines=5):
        self.origin_exception = origin_exception
        self.origin_plan = origin_plan
        self.error_lines: int = error_lines
        # FIXME: Plan typing
        self.trace: List[List[Tuple[bool, str]]] = []
        super().__init__()

    def add_origin_exception(self, plan, e):
        """添加原始异常类"""
        # reduce -> lambda in reduce -> execute_single_actions
        failed_tb = e.__traceback__.tb_next.tb_next.tb_next
        current_trace = []

        for index, action in enumerate(plan.actions):
            action_name = get_action_name(action)

            if hasattr(action, "__code__") and action.__code__.co_code == failed_tb.tb_frame.f_code.co_code:
                current_trace.append((True, f'{error_line_mark} [{index + 1}] {action_name}'))
            else:
                current_trace.append((False, f'{normal_line_mark} [{index + 1}] {action_name}'))

        self.trace.insert(0, current_trace)

    def add_plan_exception(self, plan, e):
        """plan异常

        如果为Plan异常，则action必定为Plan类。
        """

        execute_tb = e.__traceback__.tb_next.tb_next

        current_trace = []

        for index, action in enumerate(plan.actions):
            action_name = get_action_name(action)

            # 如果是执行的plan类
            if action is execute_tb.tb_frame.f_locals['action']:
                current_trace.append((True, f'{error_line_mark} [{index + 1}] {action_name}'))
            else:
                current_trace.append((False, f'{normal_line_mark} [{index + 1}] {action_name}'))

        self.trace.insert(0, current_trace)

    def get_plan_trace(self, level=0) -> Iterable[str]:
        """获取Plan的路径"""
        if len(self.trace) > level:
            action_lines = self.trace[level]

            level_0_syntax = ' |' if level else ''
            syntax_content = ' ' * (level * 4)
            target_syntax_content = ' ---' * level

            # if not level:
            #     yield f'Plan <{plan.__name__}> execute:'
            for error_flag, action_line in action_lines:
                if error_flag:
                    yield f'|{target_syntax_content}{level_0_syntax}{action_line}'

                    yield from self.get_plan_trace(level + 1)
                else:
                    yield f'|{syntax_content}{level_0_syntax}{action_line}'

    def __str__(self):
        origin_error = self.origin_exception
        plan = self.origin_plan

        error_content = get_error_line(origin_error)

        plan_hand = f'Plan [{plan.__name__}]:\n'
        error_hand = f'Raise [{origin_error.__class__.__name__}]. Message:{str(origin_error)}\n'

        plan_content = '\n'.join(list(self.get_plan_trace()))

        return f'{horizon_line}{error_hand}{horizon_line}{plan_hand}{horizon_line}{plan_content}\n{horizon_line}{error_content}'
