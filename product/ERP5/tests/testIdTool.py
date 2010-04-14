# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Nexedi SARL and Contributors. All Rights Reserved.
#          Aurélien Calonne <aurel@nexedi.com>
#          Danièle Vanbaelinghem <daniele@nexedi.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
##############################################################################

import unittest
import transaction

from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase

class TestIdTool(ERP5TypeTestCase):

  # Different variables used for this test
  def afterSetUp(self):
    self.login()
    self.portal = self.getPortal()
    self.id_tool = self.portal.portal_ids
    self.createGenerators()
    transaction.commit()
    self.tic()

  def beforeTearDown(self):
    self.id_tool.clearGenerator(all=True)
    self.id_tool.initializeGenerator(all=True)

  def getTitle(self):
    """
      Return the title of test
    """
    return "Test Id Tool"

  def createGenerators(self):
    """
      Initialize some generators for the tests
    """
    self.application_sql_generator = self.id_tool.newContent(\
                            portal_type='Application Id Generator',
                            reference='test_application_sql',
                            version='001')
    self.conceptual_sql_generator = self.id_tool.newContent(\
                           portal_type='Conceptual Id Generator',
                           reference='test_non_continuous_increasing',
                           version='001')
    self.sql_generator = self.id_tool.newContent(\
                    portal_type='SQL Non Continuous Increasing Id Generator',
                    reference='test_sql_non_continuous_increasing',
                    version='001')
    self.application_sql_generator.setSpecialiseValue(\
                                   self.conceptual_sql_generator)
    self.conceptual_sql_generator.setSpecialiseValue(self.sql_generator)

    self.application_zodb_generator = self.id_tool.newContent(\
                            portal_type='Application Id Generator',
                            reference='test_application_zodb',
                            version='001')
    self.conceptual_zodb_generator = self.id_tool.newContent(\
                           portal_type='Conceptual Id Generator',
                           reference='test_continuous_increasing',
                           version='001')
    self.zodb_generator = self.id_tool.newContent(\
                    portal_type='ZODB Continuous Increasing Id Generator',
                    reference='test_zodb_continuous_increasing',
                    version='001')
    self.application_zodb_generator.setSpecialiseValue(\
                                    self.conceptual_zodb_generator)
    self.conceptual_zodb_generator.setSpecialiseValue(self.zodb_generator)

  def getLastGenerator(self, id_generator):
    """
      Return Last Id Generator
    """
    document_generator = self.id_tool.searchFolder(reference=id_generator)[0]
    application_generator = document_generator.getLatestVersionValue()
    conceptual_generator = application_generator.getSpecialiseValue()\
                           .getLatestVersionValue()
    last_generator = conceptual_generator.getSpecialiseValue()\
                     .getLatestVersionValue()
    return last_generator

  def test_01a_checkVersionGenerator(self):
    """
      Add technical generator with a higher version
      test if the id_tool use the last version of a generator with the same
      reference
    """
    conceptual_sql_generator = self.application_sql_generator.getSpecialiseValue().\
                               getLatestVersionValue()
    last_sql = self.conceptual_sql_generator.getSpecialiseValue().\
                    getLatestVersionValue()
    self.assertEquals(last_sql.getVersion(), '001')
    # Create new id generator with a more higher version
    sql_generator_2 = self.id_tool.newContent(\
                    portal_type='SQL Non Continuous Increasing Id Generator',
                    reference='test_sql_non_continuous_increasing',
                    version='002')
    conceptual_sql_generator.setSpecialiseValue(sql_generator_2)
    transaction.commit()
    self.tic()
    # The last version is cached - reset cache
    self.portal.portal_caches.clearAllCache()
    last_sql = self.conceptual_sql_generator.getSpecialiseValue().\
                    getLatestVersionValue()
    self.assertEquals(last_sql.getVersion(), '002')

  def checkGenerateNewId(self, id_generator):
    """
      Check the method generateNewId
    """
    self.assertEquals(0, self.id_tool.generateNewId(id_generator=id_generator,
                                      id_group='a02'))
    # Different groups generate different ids
    self.assertEquals(0, self.id_tool.generateNewId(id_generator=id_generator,
                                      id_group='b02'))
    self.assertEquals(1, self.id_tool.generateNewId(id_generator=id_generator,
                                      id_group='a02'))
    # With default value
    self.assertEquals(0, self.id_tool.generateNewId(id_generator=id_generator,
                                      id_group='c02', default=0))
    self.assertEquals(20, self.id_tool.generateNewId(id_generator=id_generator,
                                      id_group='d02', default=20))
    self.assertEquals(21, self.id_tool.generateNewId(id_generator=id_generator,
                                      id_group='d02', default=3))

  def test_02a_generateNewIdWithZODBGenerator(self):
    """
      Check the generateNewId with a zodb id generator
      Test that the dictionary of the zodb is filled
    """
    # check zodb dict is empty
    zodb_generator = self.getLastGenerator('test_application_zodb')
    zodb_portal_type = 'ZODB Continuous Increasing Id Generator'
    self.assertEquals(zodb_generator.getPortalType(), zodb_portal_type)
    self.assertEqual(getattr(zodb_generator, 'last_id_dict', None), None)
    # generate ids
    self.checkGenerateNewId('test_application_zodb')
    # check zodb dict
    self.assertEqual(zodb_generator.last_id_dict['c02'], 1)
    self.assertEqual(zodb_generator.last_id_dict['d02'], 20)

  def checkGenerateNewIdWithSQL(self, store):
    """
      Check the generateNewId with a sql id generator
      Test that the database is update and also the zodb dictionary
      (if the store is True)
    """
     # check zodb dict is empty
    sql_generator = self.getLastGenerator('test_application_sql')
    sql_portal_type = 'SQL Non Continuous Increasing Id Generator'
    self.assertEquals(sql_generator.getPortalType(), sql_portal_type)
    self.assertEqual(getattr(sql_generator, 'last_max_id_dict', None), None)
    # retrieve method to recovery the last id in the database
    last_id_method = getattr(self.portal, 'IdTool_zGetLastId', None)
    self.assertNotEquals(last_id_method, None)
    # store the ids in zodb
    if store:
      sql_generator.setStoredInZodb(True)
    # generate ids
    self.checkGenerateNewId('test_application_sql')
    # check last_id in sql
    self.assertEquals(last_id_method(id_group='c02')[0]['LAST_INSERT_ID()'], 1)
    self.assertEquals(last_id_method(id_group='d02')[0]['LAST_INSERT_ID()'], 20)
    # check zodb dict
    if store:
      self.assertEqual(sql_generator.last_max_id_dict['c02'].value, 1)
      self.assertEqual(sql_generator.last_max_id_dict['d02'].value, 20)
    else:
      self.assertEqual(getattr(sql_generator, 'last_max_id_dict', None), None)

  def test_02b_generateNewIdWithSQLGeneratorWithoutStorageZODB(self):
    """
      Check the generateNewId, the update of the database and 
      that the zodb dictionary is empty
    """
    self.checkGenerateNewIdWithSQL(store=False)

  def test_02c_generateNewIdWithSQLGeneratorWithStorageZODB(self):
    """
      Check the generateNewId,the update of the database and
      that the the zodb dictionary is filled
    """
    self.checkGenerateNewIdWithSQL(store=True)

  def checkGenerateNewIdList(self, id_generator):
    """
      Check the generateNewIdList
    """
    self.assertEquals([0], self.id_tool.generateNewIdList(\
                         id_generator=id_generator, id_group='a03'))
    # Different groups generate different ids
    self.assertEquals([0, 1], self.id_tool.generateNewIdList(\
                                      id_generator=id_generator,
                                      id_group='b03', id_count=2))
    self.assertEquals([1 ,2, 3], self.id_tool.generateNewIdList(\
                                      id_generator=id_generator,
                                      id_group='a03', id_count=3))
    # With default value
    self.assertEquals([0, 1, 2], self.id_tool.generateNewIdList(\
                                      id_generator=id_generator,
                                      id_group='c03', default=0, id_count=3))
    self.assertEquals([20, 21, 22], self.id_tool.generateNewIdList(\
                                      id_generator=id_generator,
                                      id_group='d03', default=20, id_count=3))
    self.assertEquals([23, 24], self.id_tool.generateNewIdList(\
                                      id_generator=id_generator,
                                      id_group='d03', default=3, id_count=2))

  def test_03a_generateNewIdListWithZODBGenerator(self):
    """
      Check the generateNewIdList with zodb generator
    """
    self.checkGenerateNewIdList('test_application_zodb')

  def test_03b_generateNewIdListWithSQLGenerator(self):
    """
      Check the generateNewIdList with sql generator
    """
    self.checkGenerateNewIdList('test_application_sql')

  def test_04_generateNewIdAndgenerateNewIdListWithTwoGenerator(self):
    """
      Check that the same id_group between the generators is not modified
      Check the generateNewIdList and generateNewId in the same test
    """
    self.assertEquals([1, 2, 3], self.id_tool.generateNewIdList(
                                        id_generator='test_application_zodb',
                                        id_group='a04', default=1, id_count=3))
    self.assertEquals(4, self.id_tool.generateNewId(
                                        id_generator='test_application_zodb',
                                        id_group='a04'))
    self.assertEquals(1, self.id_tool.generateNewId(
                                        id_generator='test_application_sql',
                                        id_group='a04', default=1))
    self.assertEquals([2, 3, 4], self.id_tool.generateNewIdList(
                                        id_generator='test_application_sql',
                                        id_group='a04', id_count=3))

def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestIdTool))
  return suite

