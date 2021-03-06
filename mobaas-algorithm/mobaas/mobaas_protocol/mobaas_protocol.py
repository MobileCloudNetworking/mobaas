import json

from mobaas.mobaas_protocol import message_objects as mo

'''
All possible prefixes in one list
'''
PREFIXES = [ mo.Request.prefix
           , mo.Answer.prefix
           , mo.Error.prefix
           , mo.EndConversation.prefix
           ]

'''
All messages that contain a type field
'''
TYPED_MESSAGES = {
                 mo.Request: [ mo.MPSingleUserRequest
                             , mo.MPMultiUserRequest
                             , mo.BPSingleLinkRequest
                             , mo.MaaSSingleUserDataRequest
                             , mo.MaaSSingleLinkDataRequest
                             , mo.MaaSSingleLinkCapacityRequest
                             ]
                 ,
                 mo.Answer: [ mo.MPSingleUserAnswer
                            , mo.MPMultiUserAnswer
                            , mo.BPSingleLinkAnswer
                            , mo.MaaSSingleUserDataAnswer
                            , mo.MaaSSingleLinkDataAnswer
                            , mo.MaaSSingleLinkCapacityAnswer
                            ]
                 }

'''
All messages without a type field and can be recognized just by
the prefix
'''
TYPELESS_MESSAGES = [ mo.Error
                    , mo.EndConversation
                    ]


'''
Parses a message from an input string to a message_objects class
'''
def parse_message(input_str):
    result = None
    json_body_begins_at = input_str.find("{")
    json_body_ends_at = input_str.rfind("}")
    prefix = input_str[:json_body_begins_at].strip()
    json_body_str = input_str[json_body_begins_at:json_body_ends_at + 1]
    typed_prefixes = [x.prefix for x, _ in TYPED_MESSAGES.items()]

    decoder = json.JSONDecoder()
    json_obj = decoder.decode(json_body_str)

    if prefix in typed_prefixes:
        type_value = find_message_type(json_body_str)

        for typed_message, messages in TYPED_MESSAGES.items():
            if prefix == typed_message.prefix:
                for message in messages:
                    if type_value == message.type:
                        del json_obj["type"]
                        result = message.parse_json(json_obj)
                        break
    else:

        for typeless_message in TYPELESS_MESSAGES:
            if prefix == typeless_message.prefix:
                result = typeless_message.parse_json(json_obj)
                break

    return result


'''
Based on an input string, tries to find the type field within the input string
to determine the type of the message
'''
def find_message_type(input_str):
    type_begins_at = input_str.find("type")
    type_value_begins_at = input_str.find(":", type_begins_at) + 1
    type_value_ends_at = input_str.find(",", type_value_begins_at)

    if type_begins_at == -1 or type_value_begins_at == -1 or type_value_ends_at == -1:
        type_value = None
    else:
        type_value = input_str[type_value_begins_at: type_value_ends_at].strip()
        type_value = type_value[1: len(type_value) - 1] #Remove the quotes

    return type_value

'''
Determines the entire json body of a message as a tuple
with a starting int and an ending int
'''
def _find_json_body(input_str):
    json_body_starts_at = input_str.find("{")
    result = (None, None)

    if json_body_starts_at != -1:
        counter = 0
        json_body_ends_at = None
        for i, c in enumerate(input_str[json_body_starts_at:]):
            if c == '{':
                counter += 1
            elif c == '}':
                counter -= 1

                if counter == 0:
                    json_body_ends_at = i + json_body_starts_at
                    break

        if json_body_ends_at and counter == 0:
            result = (json_body_starts_at, json_body_ends_at)

    return result

'''
Used to determine if there are no characters where
a gap(whitespace) is expected.
'''
def _check_gap(input_str, begin, end):
    #Change ranges to the actual string to check
    begin += 1
    end -= 1

    #If the gap was not an empty string
    if begin >= end:
        gap = input_str[begin: end + 1].strip()
        gap_is_clean = gap == ""
    else:
        #Gap was empty
        gap_is_clean = True

    return gap_is_clean


'''
Finds the first is_func(character) index where
a certain character is expected
'''
def _find_first_in_string(input_str, is_func):
    result = None

    i = 0
    for c in input_str:
        if is_func(c):
            result = i
            break
        i += 1
    return result

'''
Checks the message for any defects and returns the last index
of the message if no defects are found.
'''
def first_complete_message_ends_at(input_str):
    result = -1
    json_body_start, json_body_end = _find_json_body(input_str)

    if json_body_start and json_body_end:
        prefix_start = _find_first_in_string(input_str, lambda x: not str.isspace(x))
        prefix = input_str[prefix_start: json_body_start].strip()
        prefix_end = len(prefix) - 1

        newline_start = input_str[json_body_end + 1:].find('\n') + json_body_end + 1
        newline_end = newline_start + 1

        newline = input_str[newline_start: newline_end + 1]

        if (    prefix in PREFIXES
            and newline == "\n\n"
            and _check_gap(input_str, prefix_end, json_body_start)
            and _check_gap(input_str, json_body_end, newline_start)):
                result = newline_end

    return result

'''
Checks if the input_str contains a complete message or not
'''
def contains_complete_message(input_str):
    return (first_complete_message_ends_at(input_str) != -1)
