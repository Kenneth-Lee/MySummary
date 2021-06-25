# Kenneth Lee 版权所有 2021
# 增加两个role：dtag和dtaglist。用于自动生成文档tag
# 用法：
# 在一个文档中增加：
#
#       :dtag:`tag1, tag2, ...`
#
# 然后你可以在其他地方可以这样产生一组索引这些主题的文档的目录：
#
#       :dtaglist:`tag1, tag2, ...`
#
# 当然，这里一般只需要一个索引就够了，你还可以用@all列出所有tag
#

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives

class Tags(nodes.Element):
    def __init__(self, content):
        super().__init__(self)
        raw_tags = content.split(',')
        self.tags = [x.strip() for x in raw_tags]

class DtagNode(Tags):
    def __init__(self, content, docname):
        super().__init__(content)
        self.docname = docname

def visit_dtag_node(self, node):
    pass

def depart_dtag_node(self, node):
    pass

class DtagListNode(Tags):
    def __init__(self, content):
        super().__init__(content)

def process_dtags(app, doctree):
    env = app.builder.env
    if not hasattr(env, 'dtag_db'):
        env.dtag_db = {} #字典：{tag: 文档列表}

    for node in doctree.traverse(DtagNode):
        node.docname = env.docname
        for tag in node.tags:
            if tag in env.dtag_db.keys():
                if not (node.docname in env.dtag_db[tag]):
                    env.dtag_db[tag].append(node.docname)
            else:
                env.dtag_db[tag] = [node.docname]

def _create_dtag_entries(tag, db, entries, builder, fromdocname):
    for docname in db[tag]:
        ref = nodes.reference('', '', internal=True)
        ref['refuri'] = builder.get_relative_uri(fromdocname, docname)
        ref.append(nodes.emphasis(docname, docname))

        para = nodes.paragraph('', '', ref)
        item = nodes.list_item('', para)
        entries.append(item)
    return entries

def process_dtags_list(app, doctree, fromdocname):
    env = app.builder.env
    if not hasattr(env, 'dtag_db'):
        env.dtag_db = {}
    
    for node in doctree.traverse(DtagListNode):
        if len(node.tags)>0 and node.tags[0] == '@all':
            para = nodes.paragraph('', '')
            para['columns'] = 3
            for tag in env.dtag_db.keys():
                para += nodes.strong(tag, tag);
                entries = []
                _create_dtag_entries(tag, env.dtag_db, entries, app.builder, fromdocname)
                contents = nodes.bullet_list('', *entries)
                para += contents
            node.replace_self(para)
        else:
            entries = []
            for tag in node.tags:
                if tag in env.dtag_db.keys():
                    _create_dtag_entries(tag, env.dtag_db, entries, app.builder, fromdocname)
            contents = nodes.bullet_list('', *entries)
            node.replace_self(contents)

def dtag_role(typ, rawtext, etext, lineno, inliner, options={}, content=[]):
    node = DtagNode(etext, inliner.document)
    return [node], []

def dtaglist_role(typ, rawtext, etext, lineno, inliner, options={}, content=[]):
    node = DtagListNode(etext)
    return [node], []

def setup(app):
    vd = visit_dtag_node, depart_dtag_node
    app.add_node(DtagNode, html=vd, latex=vd, text=vd)
    app.add_node(DtagListNode, html=vd, latex=vd, text=vd)

    app.add_role("dtag", dtag_role)
    app.add_role("dtaglist", dtaglist_role)

    app.connect('doctree-read', process_dtags)
    app.connect('doctree-resolved', process_dtags_list)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
