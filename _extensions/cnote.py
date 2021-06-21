# Kenneth Lee 版权所有 2021
# 用于取代note的directive，可以自己决定标题。
# 用法：
# .. cnote:: 标题
#
#    内容
 
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives

class cnote_node(nodes.Admonition, nodes.Element):
    pass

def visit_cnote_node(self, node):
    self.visit_admonition(node)

def depart_cnote_node(self, node):
    self.depart_admonition(node)

class cnote_directive(SphinxDirective):

    has_content = True
    required_arguments = 0
    option_spec = { 'caption' : directives.unchanged }

    def run(self):
        node = cnote_node("cnote")
        if 'caption' in self.options.keys():
            node += nodes.title(text=self.options['caption'])
        else:
            node += nodes.title(text=u'说明')

        self.state.nested_parse(self.content, self.content_offset, node)

        return [node]

def setup(app):
    vd = visit_cnote_node, depart_cnote_node
    app.add_node(cnote_node, html=vd, latex=vd, text=vd)
    app.add_directive("cnote", cnote_directive)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
