##############################################################################
#
# Copyright (c) 2002 Nexedi SARL and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
#                    Sebastien Robin <seb@nexedi.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from Products.CMFCore.utils import UniqueObject

from Acquisition import Implicit
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass, DTMLFile
from Products.ERP5Type import Permissions
from Products.ERP5Type import _dtmldir
from Products.ERP5Type.Tool.BaseTool import BaseTool
from Products.ERP5Type.Document.Folder import Folder
from zLOG import LOG

class DomainTool(BaseTool):
    """
         A tool to define ranges and subranges (predicates)
    """
    id = 'portal_domains'
    meta_type = 'ERP5 Domain Tool'    
    portal_type     = 'Domain Tool'
    allowed_types   = ( 'ERP5 Domain',)

    # Declarative Security
    security = ClassSecurityInfo()

    #
    #   ZMI methods
    #
    #manage_options =  Folder.manage_options                     

    security.declareProtected( Permissions.ManagePortal, 'manage_overview' )
    manage_overview = DTMLFile( 'explainDomainTool', _dtmldir )

    security.declarePublic('searchPredicateList')
    def searchPredicateList(self,context,test=1,sort_method=None,
                            ignored_category_list=None,filter_method=None,**kw):
      """
      Search all predicates wich corresponds to this particular context.
      
      - The sort_method parameter allows to give a method wich will be
        used in order to sort the list of predicates founds. The most
        important predicate is the first one in the list.

      - ignored_category_list :  this is the list of category that we do
        not want to test. For example, we might want to not test the 
        destination or the source of a predicate.

      """
      portal_catalog = context.portal_catalog
      portal_categories = context.portal_categories
      column_list = []
      expression_list = []
      checked_column_list = []
      sql_kw = {}
      for column in portal_catalog.getColumnIds():
        if column.startswith('predicate.'):
          column_list.append(column.split('.')[1])
      for column in column_list:
        if column in checked_column_list:
          continue
        range_property = 0
        if column.endswith('_min') or column.endswith('_max'):
          range_property = 1
          property = column[-len('_min')]
        if '%s_min' % column in column_list:
          range_property = 1
          property = column
        if range_property:
          # We have to check a range property
          base_name = 'predicate.%s' % property
          value = context.getProperty(property)
          if value is None:
            expression_list.append('%s is NULL AND %s_min is NULL AND %s_max is NULL' % ((base_name,)*3))
          else:
            expression =     '%s is NULL AND %s_min is NULL AND %s_max is NULL ' % ((base_name,)*3) 
            expression += 'OR %s = %s ' % (base_name,value)
            expression += 'OR %s_min <= %s AND %s_max is NULL ' % (base_name,value,base_name)
            expression += 'OR %s_min is NULL AND %s_max > %s ' % (base_name,base_name,value)
            expression += 'OR %s_min <= %s AND %s_max > %s ' % (base_name,value,base_name,value)
            expression_list.append(expression)
          checked_column_list.append('%s' % property)
          checked_column_list.append('%s_min' % property)
          checked_column_list.append('%s_max' % property)
      # Add predicate.uid for automatic join
      sql_kw['predicate.uid'] = '!=0'
      where_expression = ' OR '.join(expression_list)

      # Add category selection
      category_list = context.getCategoryList()
      if len(category_list)==0:
        category_list = ['NULL']
      category_expression = portal_categories.buildSQLSelector(category_list,query_table='predicate_category')
      if len(where_expression)>0:
        where_expression = '(%s) AND (%s)' % (where_expression,category_expression)
      else:
        where_expression = category_expression
      sql_kw['where_expression'] = where_expression
      # Add predicate_category.uid for automatic join
      sql_kw['predicate_category.uid'] = '!=0'
      kw.update(sql_kw)

      sql_result_list = portal_catalog.searchResults(**kw)
      if kw.has_key('src__') and kw['src__']:
        return sql_result_list
      result_list = []
      for predicate in [x.getObject() for x in sql_result_list]:
        if test==0 or predicate.test(context):
          result_list.append(predicate)
      #LOG('searchPredicateList, result_list before sort',0,result_list)
      if filter_method is not None:
        result_list = filter_method(result_list)
      if sort_method is not None:
        result_list.sort(sort_method)
      #LOG('searchPredicateList, result_list after sort',0,result_list)
      return result_list

    security.declarePublic('generateMappedValue')
    def generateMappedValue(self,context,test=1,predicate_list=None,**kw):
      """
      We will generate a mapped value with the list of all predicates founds. Let's say
      we have 3 predicates (in the order we want) like this:
      Predicate 1   [ base_price1,           ,   ,   ,    ,    , ]
      Predicate 2   [ base_price2, quantity2 ,   ,   ,    ,    , ]
      Predicate 3   [ base_price3, quantity3 ,   ,   ,    ,    , ]

      Our MappedValue generated will have the base_price of the predicate1, and the quantity of 
      the Predicate2, because Predicate 1 is the first one wich defines a base_price and the
      Predicate2 is the first one wich defines a quantity
      """
      # First get the list of predicates
      if predicate_list is None:
        predicate_list = self.searchPredicateList(context,test=test,**kw)
      if len(predicate_list)==0:
        return None

      #mapped_value = newTempBase(self.getPortalObject(),'new_mapped_value')
      from Products.ERP5Type.Document import newTempDeliveryCell
      mapped_value = newTempDeliveryCell(self.getPortalObject(),'new_mapped_value')
      mapped_value_property_dict = {}

      # Look for each property the first predicate wich defines the property
      for predicate in predicate_list:
        for mapped_value_property in predicate.getMappedValuePropertyList():
          if not mapped_value_property_dict.has_key(mapped_value_property):
            value = predicate.getProperty(mapped_value_property)
            if value is not None:
              mapped_value_property_dict[mapped_value_property] = value
      mapped_value = mapped_value.asContext(**mapped_value_property_dict)
      return mapped_value
      


InitializeClass(DomainTool)
