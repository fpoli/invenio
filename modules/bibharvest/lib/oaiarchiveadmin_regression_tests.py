# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""OAIArchive Admin Regression Test Suite."""

__revision__ = "$Id$"

import unittest

from invenio.config import CFG_SITE_URL
from invenio.testutils import make_test_suite, run_test_suite, \
                              test_web_page_content, merge_error_messages

class OAIArchiveAdminWebPagesAvailabilityTest(unittest.TestCase):
    """Check OAIArchive Admin web pages whether they are up or not."""

    def test_oaiarchiveadmin_interface_pages_availability(self):
        """oaiarchiveadmin - availability of OAIArchive Admin interface pages"""

        baseurl = CFG_SITE_URL + '/admin/bibharvest/oaiarchiveadmin.py/'

        _exports = ['', 'delset', 'editset', 'addset']

        error_messages = []
        for url in [baseurl + page for page in _exports]:
            # first try as guest:
            error_messages.extend(test_web_page_content(url,
                                                        username='guest',
                                                        expected_text=
                                                        'Authorization failure'))
            # then try as admin:
            error_messages.extend(test_web_page_content(url,
                                                        username='admin'))
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_oaiarchiveadmin_edit_set(self):
        """oaiarchiveadmin - edit set page"""
        test_edit_url = CFG_SITE_URL + \
               "/admin/bibharvest/oaiarchiveadmin.py/editset?oai_set_id=1"
        error_messages = test_web_page_content(test_edit_url,
                                               username='admin')
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

    def test_oaiarchiveadmin_delete_set(self):
        """oaiarchiveadmin - delete set page"""
        test_edit_url = CFG_SITE_URL + \
               "/admin/bibharvest/oaiarchiveadmin.py/delset?oai_set_id=1"
        error_messages = test_web_page_content(test_edit_url,
                                               username='admin')
        if error_messages:
            self.fail(merge_error_messages(error_messages))
        return

TEST_SUITE = make_test_suite(OAIArchiveAdminWebPagesAvailabilityTest)

if __name__ == "__main__":
    run_test_suite(TEST_SUITE, warn_user=True)