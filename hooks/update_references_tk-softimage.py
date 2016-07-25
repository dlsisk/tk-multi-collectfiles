# Copyright (c) 2015 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
from sgtk import Hook
from sgtk import TankError

import win32com
from win32com.client import Dispatch as d
from win32com.client import constants as c
from pywintypes import com_error

Application = d("XSI.Application").Application
log = Application.LogMessage

class UpdateReferencesHook(Hook):   
    """
    Hook to scan scene for items to publish
    """
    def execute(self, tasks, **kwargs):
        """
        Main hook entry point
        :tasks:         List of tasks to be updated. Each task is a dictionary
                        containing the following keys:
                        {
                            type:           String
                            name:           String
                            source_files:   List of path strings
                            target_files:   List of path strings
                            error:          Boolean
                            other_params:   Dictionary
                        }
        
        :returns:       updated_count:  Integer
                                        Number of tasks successfully processed.
                        bad_object_names: Set
                                        Set of scene objects that were not successfully processed.
        """
        engine = sgtk.platform.current_engine()
        task_count = 0
        bad_object_names = set()
        for task in tasks:
            if task["error"]:
                log("Skipping "+task["name"]+" because files did not copy successfully.",4)
                continue
            if task["type"] == "image_source":
                try:
                    task["other_params"]["task_object"].FileName.Value = task["other_params"]["new_filename"]
                    task_count += 1
                except:
                    bad_object_names.add(task["name"])
        return task_count, bad_object_names