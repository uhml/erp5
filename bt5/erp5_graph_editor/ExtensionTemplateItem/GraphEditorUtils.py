
def ERP5Site_getGraphLayout(input_graph):
  """Uses graphviz to position nodes of the graph.

  This uses pydot, which depends on pyparsing == 1.5.7 (latest versions of
  pyparsing are for python 3).
  Luckily, the python files from those packages can be dropped in
  $INSTANCE_HOME/lib/python
  """
  import pydot
  graph = pydot.Dot()

  for node_id in input_graph['nodes']:
    graph.add_node(pydot.Node(node_id))

  for transition in input_graph['edges']:
    graph.add_edge(pydot.Edge(transition['source'], transition['destination']))

  new_graph = pydot.graph_from_dot_data(graph.create_dot())

  # calulate the ratio from the size of the bounding box
  ratio = new_graph.get_bb()
  origin_left, origin_top, max_left, max_top = [float(p) for p in
    new_graph.get_bb()[1:-1].split(',')]
  ratio_top = max_top - origin_top
  ratio_left = max_left - origin_left

  preference_dict = dict()
  for node in new_graph.get_nodes():
    # skip technical nodes
    if node.get_name() in ('graph', 'node', 'edge'):
      continue
    left, top = [float(p) for p in node.get_pos()[1:-1].split(",")]
    preference_dict[node.get_name()] = dict(
      top=1-(top/ratio_top),
      left=1-(left/ratio_left),)

  return preference_dict


