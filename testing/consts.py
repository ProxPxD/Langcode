import src.logic.consts as consts

KEEP_GRAPH_FLAG = '--keep-graph'
KEEP_GRAPH_OPT = KEEP_GRAPH_FLAG.lstrip('-').replace('-', '_')

URI_PREFIX = f'{consts.db.URI_PREFIX}/test/'
