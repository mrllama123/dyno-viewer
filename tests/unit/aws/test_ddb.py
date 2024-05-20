from decimal import Decimal

import pytest


@pytest.mark.parametrize(
    "exp",
    [
        {"cond": "==", "value": "test#123", "dynoExp": "="},
        {"cond": ">", "value": "213432"},
        {"cond": "<", "value": "12213"},
        {"cond": "<=", "value": "1221132"},
        {"cond": ">=", "value": "324432"},
        {"cond": "between", "value": (123, 678)},
        {"cond": "begins_with", "value": "test#123"},
    ],
)
def test_convert_filter_exp_key_cond(exp):
    from dyno_viewer.aws.ddb import convert_filter_exp_key_cond

    result = convert_filter_exp_key_cond(exp["cond"], "sk", exp["value"])
    assert result.expression_operator.lower() == exp.get("dynoExp", exp["cond"]).lower()


@pytest.mark.parametrize(
    "exp",
    [
        {"cond": "==", "value": "test#123", "dynoExp": "="},
        {"cond": "!=", "value": "test#123", "dynoExp": "<>"},
        {"cond": ">", "value": "213432"},
        {"cond": "<", "value": "12213"},
        {"cond": "<=", "value": "1221132"},
        {"cond": ">=", "value": "324432"},
        {"cond": "between", "value": (123, 678)},
        {"cond": "begins_with", "value": "test#123"},
        {"cond": "in", "value": ["test1", "test2"]},
    ],
)
def test_convert_filter_exp_attr_cond(exp):
    from dyno_viewer.aws.ddb import convert_filter_exp_attr_cond

    result = convert_filter_exp_attr_cond(exp["cond"], "sk", exp["value"])
    assert result.expression_operator.lower() == exp.get("dynoExp", exp["cond"]).lower()


@pytest.mark.parametrize(
    "attr_value",
    [
        {"args": {"value": "1234", "type": "number"}, "resultType": Decimal},
        {"args": {"value": "['test', 'test2']", "type": "list"}, "resultType": list},
        {"args": {"value": '{"test": 123}', "type": "map"}, "resultType": dict},
        {"args": {"value": '("test", 123)', "type": "set"}, "resultType": set},
        {"args": {"value": "test1234", "type": "string"}, "resultType": str},
    ],
)
def test_convert_filter_exp_value(attr_value):
    from dyno_viewer.aws.ddb import convert_filter_exp_value

    result = convert_filter_exp_value(**attr_value["args"])
    assert isinstance(result, attr_value["resultType"])
