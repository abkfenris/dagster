import datetime
import re
from typing import Any, Dict

import kubernetes
from dateutil.parser import parse
from kubernetes.client import ApiClient

from dagster import check
from dagster.utils import frozendict


def _get_k8s_class(classname):
    if classname in ApiClient.NATIVE_TYPES_MAPPING:
        return ApiClient.NATIVE_TYPES_MAPPING[classname]
    else:
        return getattr(kubernetes.client.models, classname)


def _k8s_parse_value(data, classname, attr_name):
    if classname.startswith("list["):
        sub_kls = re.match(r"list\[(.*)\]", classname).group(1)
        return [
            _k8s_parse_value(data[index], sub_kls, f"{attr_name}[{index}]")
            for index in range(len(data))
        ]

    if classname.startswith("dict("):
        sub_kls = re.match(r"dict\(([^,]*), (.*)\)", classname).group(2)
        return {k: _k8s_parse_value(v, sub_kls, f"{attr_name}[{k}]") for k, v in data.items()}

    klass = _get_k8s_class(classname)

    if klass in ApiClient.PRIMITIVE_TYPES:
        return klass(data)
    elif klass == object:
        return data
    elif klass == datetime.date:
        return parse(data).date()
    elif klass == datetime.datetime:
        return parse(data)
    else:
        if not isinstance(data, (frozendict, dict)):
            raise Exception(
                f"Attribute {attr_name} of type {klass.__name__} must be a dict, received {data} instead"
            )

        return k8s_model_from_dict(klass, data)


def _k8s_snake_case_value(val, attr_type, attr_name):
    if attr_type.startswith("list["):
        sub_kls = re.match(r"list\[(.*)\]", attr_type).group(1)
        return [
            _k8s_snake_case_value(val[index], sub_kls, f"{attr_name}[{index}]")
            for index in range(len(val))
        ]
    elif attr_type.startswith("dict("):
        sub_kls = re.match(r"dict\(([^,]*), (.*)\)", attr_type).group(2)
        return {k: _k8s_snake_case_value(v, sub_kls, f"{attr_name}[{k}]") for k, v in val.items()}
    else:
        klass = _get_k8s_class(attr_type)
        if klass in ApiClient.PRIMITIVE_TYPES or klass in (
            object,
            datetime.date,
            datetime.datetime,
        ):
            return val
        else:
            if not isinstance(val, (frozendict, dict)):
                raise Exception(
                    f"Attribute {attr_name} of type {klass.__name__} must be a dict, received {val} instead"
                )
            return k8s_snake_case_dict(klass, val)


def k8s_snake_case_dict(model_class, model_dict: Dict[str, Any]):
    snake_case_to_camel_case = model_class.attribute_map
    camel_case_to_snake_case = dict((v, k) for k, v in snake_case_to_camel_case.items())

    snake_case_dict = {}
    for key, val in model_dict.items():
        snake_case_key = camel_case_to_snake_case[key] if key in camel_case_to_snake_case else key

        if snake_case_key != key and snake_case_key in model_dict:
            raise Exception(
                f"Model class {model_class.__name__} cannot contain both {key} and {snake_case_key} keys"
            )

        snake_case_dict[snake_case_key] = val

    invalid_keys = set(snake_case_dict).difference(snake_case_to_camel_case)

    if len(invalid_keys):
        raise Exception(f"Unexpected keys in model class {model_class.__name__}: {invalid_keys}")

    final_dict = {}
    for key, val in snake_case_dict.items():
        attr_type = model_class.openapi_types[key]
        final_dict[key] = _k8s_snake_case_value(val, attr_type, key)

    return final_dict


# Heavily inspired by kubernetes.client.ApiClient.__deserialize_model, with more validation
# that the keys and values match the expected format. Accepts atribute names in snake_case.
def k8s_model_from_dict(model_class, model_dict: Dict[str, Any]):
    check.dict_param(model_dict, "model_dict")

    expected_keys = set(model_class.attribute_map.keys())
    invalid_keys = set(model_dict).difference(expected_keys)

    if len(invalid_keys):
        raise Exception(f"Unexpected keys in model class {model_class.__name__}: {invalid_keys}")

    kwargs = {}
    for attr, attr_type in model_class.openapi_types.items():
        # e.g. config_map => configMap
        if attr in model_dict:
            value = model_dict[attr]
            kwargs[attr] = _k8s_parse_value(value, attr_type, attr)

    return model_class(**kwargs)
