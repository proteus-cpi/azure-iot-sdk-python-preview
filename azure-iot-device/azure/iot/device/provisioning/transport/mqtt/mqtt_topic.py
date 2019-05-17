# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import logging
from datetime import date
import six.moves.urllib as urllib

logger = logging.getLogger(__name__)


def _get_topic_base():
    """
    return the string that creates the beginning of all topics for DPS
    """
    return "$dps/registrations/"


def get_topic_for_subscribe():
    """
    return the topic string used to subscribe for receiving future responses from DPS
    """
    return _get_topic_base() + "res/#"


def get_topic_for_register(rid):
    """
    return the topic string used to publish telemetry
    """
    return (_get_topic_base() + "PUT/iotdps-register/?$rid={rid}").format(rid=rid)


def get_topic_for_query(rid, operation_id):
    """
    :return: The topic for cloud to device messages.It is of the format
    "devices/<deviceid>/messages/devicebound/#"
    """
    return (_get_topic_base() + "GET/iotdps-get-operationstatus/?$rid={}&operationId={}").format(
        rid=rid, operation_id=operation_id
    )


def get_topic_for_response():
    """
    return the topic string used to publish telemetry
    """
    return _get_topic_base() + "res/"


def is_query_topic(topic):
    if "GET/iotdps-get-operationstatus" in topic:
        return True
    return False


# def get_input_topic_for_subscribe(device_id, module_id):
#     """
#     :return: The topic for input messages. It is of the format
#     "devices/<deviceId>/modules/<moduleId>/inputs/#"
#     """
#     return _get_topic_base(device_id, module_id) + "/inputs/#"
#
#
# def get_method_topic_for_publish(request_id, status):
#     """
#     :return: The topic for publishing method responses. It is of the format
#     "$iothub/methods/res/<status>/?$rid=<requestId>
#     """
#     return "$iothub/methods/res/{status}/?$rid={rid}".format(
#         status=urllib.parse.quote_plus(status), rid=urllib.parse.quote_plus(request_id)
#     )
#
#
# def get_method_topic_for_subscribe():
#     """
#     :return: The topic for ALL incoming methods. It is of the format
#     "$iothub/methods/POST/#"
#     """
#     return "$iothub/methods/POST/#"
#
#


def is_dps_response_topic(topic):
    """
    Topics for responses from DPS are of the following format:
    $dps/registrations/res/<statuscode>/?$<key1>=<value1>&<key2>=<value2>&<key3>=<value3>
    :param topic: The topic string
    """
    if get_topic_for_response() in topic:
        return True
    return False


#
#
# def is_input_topic(topic):
#     """
#     Topics for inputs are of the following format:
#     devices/<deviceId>/modules/<moduleId>/inputs/<inputName>
#     :param topic: The topic string
#     """
#     if "/inputs/" in topic:
#         return True
#     return False


# def get_input_name_from_topic(topic):
#     """
#     Extract the input channel from the topic name
#     Topics for inputs are of the following format:
#     devices/<deviceId>/modules/<moduleId>/inputs/<inputName>
#     :param topic: The topic string
#     """
#     parts = topic.split("/")
#     if len(parts) > 5 and parts[4] == "inputs":
#         return parts[5]
#     else:
#         raise ValueError("topic has incorrect format")


# def is_method_topic(topic):
#     """
#     Topics for methods are of the following format:
#     "$iothub/methods/POST/{method name}/?$rid={request id}"
#
#     :param str topic: The topic string.
#     """
#     if "$iothub/methods/POST" in topic:
#         return True
#     return False
#
#
# def get_method_name_from_topic(topic):
#     """
#     Extract the method name from the method topic.
#     Topics for methods are of the following format:
#     "$iothub/methods/POST/{method name}/?$rid={request id}"
#
#     :param str topic: The topic string
#     """
#     parts = topic.split("/")
#     if is_method_topic(topic) and len(parts) >= 4:
#         return parts[3]
#     else:
#         raise ValueError("topic has incorrect format")


def extract_properties_from_topic(topic):
    """
    Topics for responses from DPS are of the following format:
    $dps/registrations/res/<statuscode>/?$<key1>=<value1>&<key2>=<value2>&<key3>=<value3>
    Extract key=value pairs from the latter part of the topic.
    :param topic: The topic string
    :return key_values_dict : a dictionary of key mapped to a list of values.
    """
    topic_parts = topic.split("$")
    key_value_dict = urllib.parse.parse_qs(topic_parts[2])
    return key_value_dict


def extract_status_code_from_topic(topic):
    """
    Topics for responses from DPS are of the following format:
    $dps/registrations/res/<statuscode>/?$<key1>=<value1>&<key2>=<value2>&<key3>=<value3>
    Extract the status code part from the topic.
    :param topic: The topic string
    """
    POS_STATUS_CODE_IN_TOPIC = 3
    topic_parts = topic.split("$")
    url_parts = topic_parts[1].split("/")
    status_code = url_parts[POS_STATUS_CODE_IN_TOPIC]
    return status_code


#
# # TODO: leverage this helper in all property extraction functions
# def _extract_properties(properties_str):
#     """Return a dictionary of properties from a string in the format
#     ${key1}={value1}&${key2}={value2}&...{keyn}={valuen}
#     """
#     d = {}
#     kv_pairs = properties_str.split("&")
#
#     for entry in kv_pairs:
#         pair = entry.split("=")
#         key = urllib.parse.unquote_plus(pair[0]).lstrip("$")
#         value = urllib.parse.unquote_plus(pair[1])
#         d[key] = value
#
#     return d

#
# def get_method_request_id_from_topic(topic):
#     """
#     Extract the Request ID (RID) from the method topic.
#     Topics for methods are of the following format:
#     "$iothub/methods/POST/{method name}/?$rid={request id}"
#
#     :param str stopic: the topic string
#     :raises: ValueError if topic has incorrect format
#     :returns: request id from topic string
#     """
#     parts = topic.split("/")
#     if is_method_topic(topic) and len(parts) >= 4:
#
#         properties = _extract_properties(topic.split("?")[1])
#         return properties["rid"]
#     else:
#         raise ValueError("topic has incorrect format")
