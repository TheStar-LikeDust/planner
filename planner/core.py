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
from types import FunctionType, MethodType
from typing import Callable, Any, Union, Type, Dict, List, Tuple

from planner.error import PlanException

DEFAULT_DELAY = 0.2


def get_origin(action) -> Tuple[str, object]:
    if isinstance(action, PlanMeta):
        return action.__name__, action
    # 函数
    elif isinstance(action, FunctionType):
        return action.__name__, action

    # 实例方法
    elif isinstance(action, MethodType):

        self = action.__self__

        # 类方法
        if isinstance(self, type):
            return self.__name__, self
        # 实例方法
        else:
            return self.__class__.__name__, self

    else:
        return str(action), action


class PlanMeta(type):
    def __init__(cls, name, bases, attrs: dict, actions=None):
        super().__init__(name, bases, attrs)

    def __new__(mcs, name, bases, attrs: dict, actions=None):
        cls = type.__new__(mcs, name, bases, attrs)
        cls._thread_action_result_mapper = {}

        cls.actions = [_ for _ in (actions if actions is not None else cls.actions)]

        return cls


class Plan(object, metaclass=PlanMeta):
    """不能实例化后使用"""
    actions: List[Union[FunctionType, Type[Plan]]] = []
    """已注册的原始信息 """

    is_output: bool = False
    """打印结果"""

    delay: Union[float, int] = DEFAULT_DELAY
    """执行间隔"""

    _thread_action_result_mapper: Dict[int, Dict[str, Any]] = {}
    """线程与action结果字典的字典"""

    @classmethod
    def get_results(cls) -> Dict[str, Any]:
        """多线程: 根据当前线程id自动切换不同的结果队列"""
        _id = threading.get_ident()
        if _id not in cls._thread_action_result_mapper:
            cls._thread_action_result_mapper[_id] = {}
        return cls._thread_action_result_mapper[_id]

    @classmethod
    def register(cls, target_callable: Union[FunctionType, MethodType, Type[Plan]]):
        """注册一个函数或者Plan到此Plan"""
        cls.actions.append(target_callable)

        # if isinstance(target_callable, FunctionType):
        #     cls.actions.append(target_callable)
        # elif isinstance(target_callable, PlanMeta):
        #     cls.actions.append(target_callable)

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
            pe.add_plan_exception(cls, pe)
            raise pe from None

        except Exception as e:
            plan_exception = PlanException(e, cls)
            plan_exception.add_origin_exception(cls, e)

            raise plan_exception from None

        return res

    @classmethod
    def execute_single_actions(cls, action: Callable, last_result, execute_parameter: dict) -> Any:
        """运行单个的一个函数 可以根据函数参数动态调整"""

        action_name, origin = get_origin(action)

        if cls.is_output:
            s = time.time()

            cls.output(f'- Start action: {action_name} --> {action}')
            if doc := action.__doc__:
                cls.output(f'- Doc: {doc}')

        # 如果是Plan类 转换为其execute方法
        if isinstance(action, PlanMeta) or isinstance(action, Plan):
            execute_target = action.execute
        else:
            execute_target = action

        # 动态检查参数
        sig = signature(execute_target)
        positional = [_ for _ in sig.parameters.values() if _.kind == Parameter.POSITIONAL_OR_KEYWORD]
        var_positional = [_ for _ in sig.parameters.values() if _.kind == Parameter.VAR_POSITIONAL]
        var_keyword = [_ for _ in sig.parameters.values() if _.kind == Parameter.VAR_KEYWORD]

        # case: 没有参数
        if not sig.parameters:
            action_result = execute_target()

            cls.get_results()[action_name] = action_result

        # case: 有且只有一个给定的参数
        elif not var_positional and not var_keyword and len(positional) == 1:
            action_result = execute_target(last_result)
            cls.get_results()[action_name] = action_result

        # case: 不定参数
        elif var_keyword:
            # 如果是当前Plan第一个action 则试图从执行参数中获取result
            # *result可以向下渗透
            if last_result is None:
                last_result = execute_parameter.get('result')

            action_result = execute_target(**{
                **execute_parameter,
                'result': last_result,
                'result_mapper': {
                    **execute_parameter.get('result_mapper', {}),
                    **cls.get_results()
                },
                'action_mapper': {
                    **{_[0]: _[1] for _ in [get_origin(_) for _ in cls.actions]},
                    **execute_parameter.get('action_mapper', {}),
                },
            })
            cls.get_results()[action_name] = action_result

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

            return action_result.get('result')

        return action_result

    @classmethod
    def output(cls, output_content):
        """默认输出"""
        if not getLogger(cls.__name__).handlers:
            print(output_content)
        else:
            getLogger(cls.__name__).info(output_content)


def create_plan(name: str = None, actions: list = None, is_output: bool = False, delay: float = DEFAULT_DELAY,
                **kwargs) -> Type[Plan]:
    """创建"""
    name = name if name is not None else f'Plan{uuid.uuid4().node}'
    actions = actions if actions is not None else list()

    # TODO: refactor here.
    return PlanMeta(name, (Plan,), {'is_output': is_output, 'delay': delay, **kwargs}, actions)
