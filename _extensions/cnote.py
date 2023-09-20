# Kenneth Lee 版权所有 2021-2023
# 用于取代note的directive，可以自己决定标题。
# 用法：
# .. cnote::
#    :caption: 标题
#
#    内容
 
from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives

class cnote_directive(SphinxDirective):

    has_content = True
    required_arguments = 0
    option_spec = { 'caption' : directives.unchanged }

    def run(self):
        node = nodes.admonition()
        if 'caption' in self.options.keys():
            node += nodes.title(text=self.options['caption'])
        else:
            node += nodes.title(text=u'说明')

        self.state.nested_parse(self.content, self.content_offset, node)

        return [node]

def setup(app):
    app.add_directive("cnote", cnote_directive)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
