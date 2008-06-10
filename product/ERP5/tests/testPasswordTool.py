##############################################################################
#
# Copyright (c) 2004 Nexedi SARL and Contributors. All Rights Reserved.
#          Aurelien Calonne <aurel@nexedi.com>
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

from Testing import ZopeTestCase
from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase
from AccessControl.SecurityManagement import newSecurityManager
from zLOG import LOG
from Products.ERP5Type.tests.Sequence import SequenceList
from Products.ERP5Type.tests.utils import DummyMailHost
from DateTime import DateTime

class TestPasswordTool(ERP5TypeTestCase):
  """
  Test reset of password
  """
  run_all_test = 1
  quiet = 1

  def getBusinessTemplateList(self):
    return ('erp5_base', )

  def getTitle(self):
    return "Password Tool"


  def afterSetUp(self):
    portal = self.getPortal()
    if 'MailHost' in portal.objectIds():
      portal.manage_delObjects(['MailHost'])
    portal._setObject('MailHost', DummyMailHost('MailHost'))
    portal.email_from_address = 'site@example.invalid'
    self.portal.portal_caches.clearAllCache()

  def beforeTearDown(self):
    get_transaction().abort()
    # clear modules if necessary
    self.portal.person_module.manage_delObjects(list(self.portal.person_module.objectIds()))
    get_transaction().commit()
    self.tic()

  def stepTic(self,**kw):
    get_transaction().commit()
    self.tic()

  def getUserFolder(self):
    """Returns the acl_users. """
    return self.getPortal().acl_users

  def _assertUserExists(self, login, password):
    """Checks that a user with login and password exists and can log in to the
    system.
    """
    from Products.PluggableAuthService.interfaces.plugins import\
                                                      IAuthenticationPlugin
    uf = self.getUserFolder()
    self.assertNotEquals(uf.getUserById(login, None), None)
    for plugin_name, plugin in uf._getOb('plugins').listPlugins(
                                IAuthenticationPlugin ):
      if plugin.authenticateCredentials(
                  {'login':login, 'password':password}) is not None:
        break
    else:
      self.fail("No plugin could authenticate '%s' with password '%s'" %
              (login, password))

  def _assertUserDoesNotExists(self, login, password):
    """Checks that a user with login and password does not exists and cannot
    log in to the system.
    """
    from Products.PluggableAuthService.interfaces.plugins import\
                                                        IAuthenticationPlugin
    uf = self.getUserFolder()
    for plugin_name, plugin in uf._getOb('plugins').listPlugins(
                              IAuthenticationPlugin ):
      if plugin.authenticateCredentials(
                {'login':login, 'password':password}) is not None:
        self.fail(
           "Plugin %s should not have authenticated '%s' with password '%s'" %
           (plugin_name, login, password))

  def stepAddUser(self, sequence=None, sequence_list=None, **kw):
    """
    Create a user
    """
    person = self.portal.person_module.newContent(portal_type="Person",
                                    reference="userA",
                                    password="passwordA",
                                    default_email_text="userA@example.invalid")
    assignment = person.newContent(portal_type='Assignment')
    assignment.open()

  def stepCheckPasswordToolExists(self, sequence=None, sequence_list=None, **kw):
    """
    Check existence of password tool
    """
    self.failUnless(self.getPasswordTool() is not None)

  def stepCheckUserLogin(self, sequence=None, sequence_list=None, **kw):
    """
    Check existence of password tool
    """
    self._assertUserExists('userA', 'passwordA')
    
  def stepCheckUserLoginWithNewPassword(self, sequence=None, sequence_list=None, **kw):
    """
    Check existence of password tool
    """
    self._assertUserExists('userA', 'secret')

  def stepCheckUserNotLoginWithBadPassword(self, sequence=None, sequence_list=None, **kw):
    """
    Check existence of password tool
    """
    self._assertUserDoesNotExists('userA', 'secret')

  def stepCheckUserNotLoginWithFormerPassword(self, sequence=None, sequence_list=None, **kw):
    """
    Check existence of password tool
    """
    self._assertUserDoesNotExists('userA', 'passwordA')

  def stepLostPassword(self, sequence=None, sequence_list=None, **kw):
    """
    Required a new password
    """
    self.portal.portal_password.mailPasswordResetRequest(user_login="userA")

  def stepTryLostPasswordWithBadUser(self, sequence=None, sequence_list=None, **kw):
    """
    Required a new password
    """
    self.portal.portal_password.mailPasswordResetRequest(user_login="userZ")

  def stepCheckNoMailSent(self, sequence=None, sequence_list=None, **kw):
    """
    Check mail has not been sent after fill in wrong the form password
    """
    last_message = self.portal.MailHost._last_message
    self.assertEquals((), last_message)

  def stepCheckMailSent(self, sequence=None, sequence_list=None, **kw):
    """
    Check mail has been sent after fill in the form password
    """
    last_message = self.portal.MailHost._last_message
    self.assertNotEquals((), last_message)
    mfrom, mto, messageText = last_message
    self.assertEquals('site@example.invalid', mfrom)
    self.assertEquals(['userA@example.invalid'], mto)


  def stepGoToRandomAddress(self, sequence=None, sequence_list=None, **kw):
    """
    Call method that change the password
    We don't check use of random url in mail here as we have on request
    But random is also check by changeUserPassword, so it's the same
    """
    key = self.portal.portal_password.password_request_dict.keys()[0]
    self.portal.portal_password.changeUserPassword(user_login="userA",
                                                   password="secret",
                                                   password_confirmation="secret",
                                                   password_key=key)
    # reset cache
    self.portal.portal_caches.clearAllCache()


  def stepGoToRandomAddressWithBadUserName(self, sequence=None, sequence_list=None, **kw):
    """
    Call method that change the password with a bad user name
    This must not work
    """
    key = self.portal.portal_password.password_request_dict.keys()[0]
    sequence.edit(key=key)
    self.portal.portal_password.changeUserPassword(user_login="userZ",
                                                   password="secret",
                                                   password_confirmation="secret",
                                                   password_key=key)
    # reset cache
    self.portal.portal_caches.clearAllCache()


  def stepGoToRandomAddressTwice(self, sequence=None, sequence_list=None, **kw):
    """
    As we already change password, this must npot work anylonger
    """
    key = sequence.get('key')
    self.portal.portal_password.changeUserPassword(user_login="userA",
                                                   password="passwordA",
                                                   password_confirmation="passwordA",
                                                   password_key=key)
    # reset cache
    self.portal.portal_caches.clearAllCache()


  def stepGoToBadRandomAddress(self, sequence=None, sequence_list=None, **kw):
    """
    Try to reset a password with bad random part
    """
    self.portal.portal_password.changeUserPassword(user_login="userA",
                                                   password="secret",
                                                   password_confirmation="secret",
                                                   password_key="toto")
    # reset cache
    self.portal.portal_caches.clearAllCache()



  def stepModifyExpirationDate(self, sequence=None, sequence_list=None, **kw):
    """
    Change expiration date so that reset of password is not available
    """
    # save key for url
    key = self.portal.portal_password.password_request_dict.keys()[0]
    sequence.edit(key=key)
    # modify date
    new_kw = {}
    for k, v in self.portal.portal_password.password_request_dict.items():
      login, date = v
      date = DateTime() - 1
      new_kw[k] = (login, date)
      
    self.portal.portal_password.password_request_dict = new_kw

  def stepSimulateExpirationAlarm(self, sequence=None, sequence_list=None, **kw):
    """
    Simulate alarm wich remove expired request
    """
    self.portal.portal_password.removeExpiredRequests()

  def stepCheckNoRequestRemains(self, sequence=None, sequence_list=None, **kw):
    """
    after alarm all expired request must have been removed
    """
    self.assertEqual(len(self.portal.portal_password.password_request_dict), 0)


  def stepLogout(self, sequence=None, sequence_list=None, **kw):
    """
    Logout
    """
    self.logout()

  # tests
  def test_01_checkPasswordTool(self, quiet=quiet, run=run_all_test):
    if not run: return
    if not quiet:
      message = 'Test Password Tool'
      ZopeTestCase._print('\n%s ' % message)
      LOG('Testing... ', 0, message)
    sequence_list = SequenceList()
    sequence_string = 'CheckPasswordToolExists '  \
                      'AddUser Tic ' \
                      'Logout ' \
                      'CheckUserLogin CheckUserNotLoginWithBadPassword ' \
                      'TryLostPasswordWithBadUser Tic ' \
                      'CheckNoMailSent ' \
                      'GoToBadRandomAddress Tic ' \
                      'CheckUserLogin CheckUserNotLoginWithBadPassword ' \
                      'LostPassword Tic ' \
                      'CheckMailSent GoToRandomAddress Tic '  \
                      'CheckUserLoginWithNewPassword ' \
                      'CheckUserNotLoginWithFormerPassword ' \
                      'GoToRandomAddressTwice Tic ' \
                      'CheckUserLoginWithNewPassword ' \
                      'CheckUserNotLoginWithFormerPassword ' \

    sequence_list.addSequenceString(sequence_string)
    sequence_list.play(self, quiet=quiet)


  def test_02_checkPasswordToolDateExpired(self, quiet=quiet, run=run_all_test):
    if not run: return
    if not quiet:
      message = 'Test no login reset if date expired'
      ZopeTestCase._print('\n%s ' % message)
      LOG('Testing... ', 0, message)
    sequence_list = SequenceList()
    sequence_string = 'CheckPasswordToolExists '  \
                      'AddUser Tic ' \
                      'Logout ' \
                      'CheckUserLogin CheckUserNotLoginWithBadPassword ' \
                      'LostPassword Tic ' \
                      'CheckMailSent ' \
                      'ModifyExpirationDate ' \
                      'GoToRandomAddress Tic '  \
                      'CheckUserLogin CheckUserNotLoginWithBadPassword ' \
                      
    sequence_list.addSequenceString(sequence_string)
    sequence_list.play(self, quiet=quiet)


  def test_03_checkPasswordToolAlarm(self, quiet=quiet, run=run_all_test):
    if not run: return
    if not quiet:
      message = 'Test alarm remove expired request'
      ZopeTestCase._print('\n%s ' % message)
      LOG('Testing... ', 0, message)
    sequence_list = SequenceList()
    sequence_string = 'CheckPasswordToolExists '  \
                      'AddUser Tic ' \
                      'Logout ' \
                      'CheckUserLogin CheckUserNotLoginWithBadPassword ' \
                      'LostPassword Tic ' \
                      'CheckMailSent ' \
                      'ModifyExpirationDate ' \
                      'SimulateExpirationAlarm ' \
                      'CheckNoRequestRemains ' \
                      'GoToRandomAddressTwice Tic '  \
                      'CheckUserLogin CheckUserNotLoginWithBadPassword ' \
                      
    sequence_list.addSequenceString(sequence_string)
    sequence_list.play(self, quiet=quiet)


def test_suite():
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(TestPasswordTool))
  return suite
