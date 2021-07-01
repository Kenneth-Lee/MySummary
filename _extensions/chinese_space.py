from docutils.nodes import NodeVisitor, Text, TextElement, literal_block

def setup(app):
    app.connect('doctree-resolved', process_chinese_para)

def process_chinese_para(app, doctree, docname):
    doctree.walk(ParaVisitor(doctree))

def _is_asiic_end(text): return bytes(text[-1], 'utf-8')[0] < 128

def _this_is_asiic(text): return bytes(text[0], 'utf-8')[0] < 128

def _tran_chinese_text(text):
    secs=text.split('\n')

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

class ParaVisitor(NodeVisitor):
    def dispatch_visit(self, node):
        if isinstance(node, TextElement) and not isinstance(node, literal_block):
            for i in range(len(node.children)):
                if type(node[i]) == Text:
                    node[i] = Text(_tran_chinese_text(node[i].astext()))
