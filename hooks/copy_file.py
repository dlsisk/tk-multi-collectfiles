# Copyright (c) 2015 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import os
import shutil
import sgtk
import re

HookClass = sgtk.get_hook_baseclass()


class CopyFile(HookClass):
    """
    Hook called when a file needs to be copied
    """

    def execute(self, source_path, target_path, **kwargs):
        """
        Main hook entry point

        :source_path:   String
                        Source file path to copy

        :target_path:   String
                        Target file path to copy to
        """
        # Do some error catching:
        if (os.path.getmtime(source_path) == os.path.getmtime(target_path)) and (os.path.getsize(source_path) == os.path.getsize(target_path)):
            # If the modified time and file size are both the same, the content
            # is virtually guaranteed to be the same so we'll skip it.
            
            # We have artists who use both the network location and a mapped drive 
            # for the same file location, so without getting too specific this makes
            # it "safe enough" for my purposes.
            return
        
        # create the folder if it doesn't exist
        dirname = os.path.dirname(target_path)
        if not os.path.isdir(dirname):
            old_umask = os.umask(0)
            os.makedirs(dirname, 0777)
            os.umask(old_umask)

        shutil.copy(source_path, target_path)
