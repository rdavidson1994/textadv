import json

web_new_line = "WEBNEWLINE"


def menu_wrap(noun, verbs):
    json_object = {
        "type": "dropdown",
        "label": noun,
        "options": [
            {"label": verb, "input": verb+" "+noun}
            for verb in verbs
        ],
    }
    return web_new_line+json.dumps(json_object)+web_new_line
