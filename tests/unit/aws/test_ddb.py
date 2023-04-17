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
    from dyna_cli.aws.ddb import convert_filter_exp_key_cond

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
    from dyna_cli.aws.ddb import convert_filter_exp_attr_cond

    result = convert_filter_exp_attr_cond(exp["cond"], "sk", exp["value"])
    assert result.expression_operator.lower() == exp.get("dynoExp", exp["cond"]).lower()
