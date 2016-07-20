##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# Copyright (c) 2002,2005 Nexedi SARL and Contributors. All Rights Reserved.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

# Stribger repair of BTreeFolder2
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2Base

class ERP5BTreeFolder2Base(BTreeFolder2Base):
  """
    This class is only for backward compatibility.
  """
  pass

# Work around for the performance regression introduced in Zope 2.12.23.
# Otherwise, we use superclass' __contains__ implementation, which uses
# objectIds, which is inefficient in HBTreeFolder2 to lookup a single key.
BTreeFolder2Base.__contains__ = BTreeFolder2Base.has_key

# BBB: Remove workaround on recent BTreeFolder2Base
#      OFS.ObjectManager really needs to be fixed properly.
try:
  del BTreeFolder2Base.__getitem__
except AttributeError:
  pass
