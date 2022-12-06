# -*- coding: utf-8 -*-
"""core package

#. 可以打印运行信息。包括docs、花费时间、运行结果
#. 可以暂存运行结果。用于查询结果
#. 可以动态检测函数参数
#. 可以包装错误 并且逐级抛出

"""
from __future__ import annotations

import threading
import time
import uuid
from functools import reduce
from inspect import signature, Parameter
from logging import getLogger
from types import FunctionType
from typing import Callable, Any, Union, Type

from planner.error import PlanException

DEFAULT_DELAY = 0.2


class PlanMeta(type):
    def __init__(self, name, bases, attrs: dict, actions=None):
        super().__init__(name, bases, attrs)

    def __new__(mcs, name, bases, attrs: dict, actions=None):
        actions = actions if actions is not None else attrs.get('actions', [])
        attrs['actions'] = [_.execute if isinstance(_, PlanMeta) and issubclass(_, Plan) else _ for _ in
                            actions]
        attrs['_result'] = []
        return type.__new__(mcs, name, bases, attrs)


class Plan(object, metaclass=PlanMeta):
    """不能实例化后使用"""
    actions = []
    """已注册的原始信息 """

    is_output: bool = False
    """打印结果"""

    delay: Union[float, int] = DEFAULT_DELAY
    """执行间隔"""

    _thread_results_mapper = {}
    """线程id结果字典"""

    @classmethod
    def get_results(cls) -> list:
        """多线程自动切换不同的结果队列"""
        _id = threading.get_ident()
        if _id not in cls._thread_results_mapper:
            cls._thread_results_mapper[_id] = []
        return cls._thread_results_mapper[_id]

    @classmethod
    def register(cls, target_callable: Union[Callable, Plan]):
        """注册一个函数或者Plan到此Plan"""
        if isinstance(target_callable, FunctionType):
            cls.actions.append(target_callable)
        elif isinstance(target_callable, PlanMeta):
            cls.actions.append(target_callable.execute)

    @classmethod
    def execute(cls, **execute_parameter):
        """运行此计划"""

        cls.get_results().clear()

        try:
            res = reduce(
                lambda last_result, action: cls.execute_single_actions(action, last_result, execute_parameter),
                cls.actions,
                None
            )

        except PlanException as pe:
            pe.add_exception(cls, pe)
            raise pe from None

        except Exception as e:
            plan_exception = PlanException()
            plan_exception.add_exception(cls, e)

            raise plan_exception from None

        return res

    @classmethod
    def execute_single_actions(cls, action: Callable, last_result, execute_parameter: dict) -> Any:
        """运行单个的一个函数 可以根据函数参数动态调整"""

        # 动态检查参数
        sig = signature(action)
        positional = [_ for _ in sig.parameters.values() if _.kind == Parameter.POSITIONAL_OR_KEYWORD]
        var_positional = [_ for _ in sig.parameters.values() if _.kind == Parameter.VAR_POSITIONAL]
        var_keyword = [_ for _ in sig.parameters.values() if _.kind == Parameter.VAR_KEYWORD]

        if cls.is_output:
            s = time.time()

            if hasattr(action, '__self__') and isinstance(action.__self__, PlanMeta) and issubclass(action.__self__,
                                                                                                    Plan):
                target = action.__self__
            else:
                target = action
            cls.output(f'- Start action: {target.__name__} --> {target}')
            if doc := target.__doc__:
                cls.output(f'- Doc: {doc}')

        # case: 没有参数
        if not sig.parameters:
            action_result = action()
            cls.get_results().append(action_result)

        # case: 有且只有一个给定的参数
        elif not var_positional and not var_keyword and len(positional) == 1:
            action_result = action(last_result)
            cls.get_results().append(action_result)

        # case: 不定参数
        elif var_keyword:
            if last_result is None:
                last_result = execute_parameter.get('result')

            action_result = action(**{**execute_parameter, 'result': last_result, 'results': cls.get_results()})
            cls.get_results().append(action_result)

        else:
            assert False, 'parameter error.'

        if cls.is_output:
            e = time.time()
            cls.output(f'- Done.')
            time.sleep(cls.delay)

            cls.output(f'- Time cost: {round(e - s, 3)} second.')
            cls.output(f'- action result:{action_result}')
            cls.output('-' * 80)
            time.sleep(cls.delay)

        # TODO: special sentinel return value.
        if type(action_result) is dict and 'pass' in action_result:
            execute_parameter.update(action_result)

        return action_result

    @classmethod
    def output(cls, output_content):
        """默认输出"""
        if not getLogger(cls.__name__).handlers:
            print(output_content)
        else:
            getLogger(cls.__name__).info(output_content)


def create_plan(name: str = None, actions: list = None, is_output: bool = False, delay: float = DEFAULT_DELAY) -> Type[
    Plan]:
    """创建"""
    name = name if name is not None else f'Plan{uuid.uuid4().node}'
    actions = actions if actions is not None else list()

    # TODO: refactor here.
    return PlanMeta(name, (Plan,), {'is_output': is_output, 'delay': delay}, actions)
