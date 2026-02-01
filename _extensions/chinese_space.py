from docutils.nodes import GenericNodeVisitor, Text, TextElement, literal_block

def setup(app):
    app.connect('doctree-resolved', process_chinese_para)

def process_chinese_para(app, doctree, docname):
    doctree.walk(ParaVisitor(doctree))

def _is_asiic_end(text):
    if not text:
        return False
    return bytes(text[-1], 'utf-8')[0] < 128

def _this_is_asiic(text):
    if not text:
        return False
    return bytes(text[0], 'utf-8')[0] < 128

def _tran_chinese_text(text):
    if not text:
        return text

    secs = text.split('\n')

    out = ''
    last_is_asiic = False
    for sec in secs:
        if not sec:
            continue

        if last_is_asiic and _this_is_asiic(sec):
            out += ' '

        out += sec

        last_is_asiic = _is_asiic_end(sec)

    return out

class ParaVisitor(GenericNodeVisitor):
    def default_visit(self, node):
        pass

    def default_departure(self, node):
        pass

    def visit_TextElement(self, node):
        if not isinstance(node, literal_block):
            for i in range(len(node.children)):
                if isinstance(node[i], Text):
                    node[i] = Text(_tran_chinese_text(node[i]))
