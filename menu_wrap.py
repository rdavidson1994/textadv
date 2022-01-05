import json

begin_raw = "###[[[JSON]]]###"
begin_pretty = "###[[[TEXT]]]###"


def menu_wrap(noun, verbs, display_noun=None):
    if display_noun is None:
        display_noun = noun
    json_object = {
        "type": "dropdown",
        "label": display_noun,
        "options": [
            {"label": verb, "input": verb+" "+noun}
            for verb in verbs
        ],
    }
    return begin_raw+json.dumps(json_object)+begin_pretty
