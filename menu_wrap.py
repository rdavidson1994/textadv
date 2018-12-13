import yattag

def menu_wrap(noun, verbs):
    doc, tag, text = yattag.Doc().tagtext()
    with tag("a", klass="dropdown-container"):
        with tag("button",  klass="dropdown-link"):
            text(noun)
        with tag("div", klass="dropdown-menu"):
            for verb in verbs:
                with tag("button",
                         type="button",
                         klass="dropdown-option"):
                    doc.attr(("data-text", verb+" "+noun))
                    text(verb)
    return doc.getvalue()

