# This module must be imported before CMFActivity product is installed.

import base64, errno, select, socket, time
from threading import Thread
import Lifetime
import transaction
from BTrees.OIBTree import OIBTree
from Testing import ZopeTestCase
from Products.CMFActivity import ActivityTool as _ActivityTool
from Products.CMFActivity.Activity.Queue import VALIDATION_ERROR_DELAY
from Products.ERP5Type.tests import backportUnittest
from Products.ERP5Type.tests.utils import createZServer


class ActivityTool(_ActivityTool.ActivityTool):
  """Class redefining CMFActivity.ActivityTool.ActivityTool for unit tests
  """

  # When a ZServer can't be started, the node name ends with ':' (no port).
  def _isValidNodeName(self, node_name):
    return True

  # Divert location to register processing and distributing nodes.
  # Load balancing is configured at the root instead of the activity tool,
  # so that additional can register even if there is no portal set up yet.
  # Properties at the root are:
  # - 'test_processing_nodes' to list processing nodes
  # - 'test_distributing_node' to select the distributing node
  def getNodeDict(self):
    app = self.getPhysicalRoot()
    if getattr(app, 'test_processing_nodes', None) is None:
      app.test_processing_nodes = OIBTree()
    return app.test_processing_nodes

  def getDistributingNode(self):
    return self.getPhysicalRoot().test_distributing_node

  def manage_setDistributingNode(self, distributingNode, REQUEST=None):
    # A property to catch setattr on 'distributingNode' doesn't work
    # because self would lose all acquisition wrappers.
    previous_node = self.distributingNode
    try:
      super(ActivityTool, self).manage_setDistributingNode(distributingNode,
                                                           REQUEST=REQUEST)
      self.getPhysicalRoot().test_distributing_node = self.distributingNode
    finally:
      self.distributingNode = previous_node

  # When there is more than 1 node, prevent the distributing node from
  # processing activities.
  def tic(self, processing_node=1, force=0):
    processing_node_list = self.getProcessingNodeList()
    if len(processing_node_list) > 1 and \
       self.getCurrentNode() == self.getDistributingNode():
      # Sleep between each distribute.
      time.sleep(0.3)
      transaction.commit()
    else:
      super(ActivityTool, self).tic(processing_node, force)

_ActivityTool.ActivityTool = ActivityTool


class ProcessingNodeTestCase(backportUnittest.TestCase, ZopeTestCase.TestCase):
  """Minimal ERP5 TestCase class to process activities

  When a processing node starts, the portal may not exist yet, or its name is
  unknown, so an additional 'test_portal_name' property at the root is set by
  the node running the unit tests to tell other nodes on which portal activities
  should be processed.
  """

  @staticmethod
  def asyncore_loop():
    try:
      Lifetime.lifetime_loop()
    except KeyboardInterrupt:
      pass
    Lifetime.graceful_shutdown_loop()

  def startZServer(self):
    """Start HTTP ZServer in background"""
    utils = ZopeTestCase.utils
    if utils._Z2HOST is None:
      try:
        hs = createZServer()
      except RuntimeError, e:
        ZopeTestCase._print(str(e))
      else:
        utils._Z2HOST, utils._Z2PORT = hs.server_name, hs.server_port
        t = Thread(target=Lifetime.loop)
        t.setDaemon(1)
        t.start()
    return utils._Z2HOST, utils._Z2PORT

  def _registerNode(self, distributing, processing):
    """Register node to process and/or distribute activities"""
    try:
      activity_tool = self.portal.portal_activities
    except AttributeError:
      activity_tool = ActivityTool().__of__(self.app)
    currentNode = activity_tool.getCurrentNode()
    if distributing:
      activity_tool.manage_setDistributingNode(currentNode)
    if processing:
      activity_tool.manage_addToProcessingList((currentNode,))
    else:
      activity_tool.manage_removeFromProcessingList((currentNode,))

  def tic(self, verbose=0):
    """Execute pending activities"""
    portal_activities = self.portal.portal_activities
    if 1:
      if verbose:
        ZopeTestCase._print('Executing pending activities ...')
        old_message_count = 0
        start = time.time()
      count = 1000
      getMessageList = portal_activities.getMessageList
      message_count = len(getMessageList(include_processing=1))
      while message_count:
        if verbose and old_message_count != message_count:
          ZopeTestCase._print(' %i' % message_count)
          old_message_count = message_count
        portal_activities.process_timer(None, None)
        if Lifetime._shutdown_phase:
          # XXX CMFActivity contains bare excepts
          raise KeyboardInterrupt
        message_count = len(getMessageList(include_processing=1))
        # This prevents an infinite loop.
        count -= 1
        if count == 0:
          # Get the last error message from error_log.
          error_message = ''
          error_log = self.portal.error_log._getLog()
          if len(error_log):
            last_log = error_log[-1]
            error_message = '\nLast error message:\n%s\n%s\n%s\n' % (
              last_log['type'],
              last_log['value'],
              last_log['tb_text'],
              )
          raise RuntimeError,\
            'tic is looping forever. These messages are pending: %r %s' % (
          [('/'.join(m.object_path), m.method_id, m.processing_node, m.retry)
          for m in portal_activities.getMessageList()],
          error_message
          )
        # This give some time between messages
        if count % 10 == 0:
          portal_activities.timeShift(3 * VALIDATION_ERROR_DELAY)
      if verbose:
        ZopeTestCase._print(' done (%.3fs)\n' % (time.time() - start))

  def afterSetUp(self):
    """Initialize a node that will only process activities"""
    self.startZServer()
    self._registerNode(distributing=0, processing=1)
    transaction.commit()

  def processing_node(self):
    """Main loop for nodes that process activities"""
    try:
      while not Lifetime._shutdown_phase:
        time.sleep(.3)
        transaction.begin()
        try:
          portal = self.app[self.app.test_portal_name]
        except AttributeError:
          continue
        portal.portal_activities.process_timer(None, None)
    except KeyboardInterrupt:
      pass
