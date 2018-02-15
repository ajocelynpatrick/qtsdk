#!/usr/bin/env python
#############################################################################
##
## Copyright (C) 2017 The Qt Company Ltd.
## Contact: https://www.qt.io/licensing/
##
## This file is part of the release tools of the Qt Toolkit.
##
## $QT_BEGIN_LICENSE:GPL-EXCEPT$
## Commercial License Usage
## Licensees holding valid commercial Qt licenses may use this file in
## accordance with the commercial license agreement provided with the
## Software or, alternatively, in accordance with the terms contained in
## a written agreement between you and The Qt Company. For licensing terms
## and conditions see https://www.qt.io/terms-conditions. For further
## information use the contact form at https://www.qt.io/contact-us.
##
## GNU General Public License Usage
## Alternatively, this file may be used under the terms of the GNU
## General Public License version 3 as published by the Free Software
## Foundation with exceptions as appearing in the file LICENSE.GPL3-EXCEPT
## included in the packaging of this file. Please review the following
## information to ensure the GNU General Public License requirements will
## be met: https://www.gnu.org/licenses/gpl-3.0.html.
##
## $QT_END_LICENSE$
##
#############################################################################

import os
import getpass
import glob
import unittest
import shutil
from build_wrapper import init_snapshot_dir_and_upload_files


class TestStringMethods(unittest.TestCase):

    def test_init_snapshot_dir_and_upload_files(self):
        temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build_wrapper_test')
        optionDict = {}
        optionDict['WORK_DIR'] = os.getcwd()
        optionDict['SSH_COMMAND'] = 'ssh'
        optionDict['SCP_COMMAND'] = 'scp'
        user = getpass.getuser()
        optionDict['PACKAGE_STORAGE_SERVER_ADDR'] = user + '@127.0.0.1'
        optionDict['PACKAGE_STORAGE_SERVER_BASE_DIR'] = temp_dir
        filesToUpload = [os.path.basename(x) for x in glob.glob('./*.sh')]
        init_snapshot_dir_and_upload_files(optionDict, 'test-project-name', '1.0', '1234567890', filesToUpload)

        remote_path_base            = os.path.join(temp_dir, 'test-project-name', '1.0')
        remote_path_snapshot_dir    = os.path.join(remote_path_base, '1234567890')
        remote_path_latest_link     = os.path.join(remote_path_base, 'latest')
        print(remote_path_latest_link)
        self.assertTrue(os.path.isdir(remote_path_base))
        self.assertTrue(os.path.isdir(remote_path_snapshot_dir))
        self.assertTrue(os.path.islink(remote_path_latest_link))

        searchDir = os.path.join(remote_path_latest_link, '*.sh')
        uploadedFiles = [os.path.basename(x) for x in glob.glob(searchDir)]
        self.assertListEqual(sorted(filesToUpload), sorted(uploadedFiles))

        shutil.rmtree(remote_path_base)

if __name__ == '__main__':
    unittest.main()
