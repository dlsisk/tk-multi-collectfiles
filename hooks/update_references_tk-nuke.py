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



import nuke

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
                bad_object_names.add(task["name"])
                print "Skipping "+task["name"]+" because files did not copy successfully."
                continue
            # This should get read_node_still, read_node_sequence, and read_node_movie.
            if task["type"].startswith("read_node"):
                try:
                    self._update_read_node(task)
                    task_count += 1
                except:
                    bad_object_names.add(task["name"])
                
        return task_count, bad_object_names
    
    
    def _update_read_node(self, task):
        
        # Windows likes \. Nuke likes /.
        new_filename = task["other_params"]["new_filename"].replace("\\","/")
        
        task["other_params"]["task_object"]['file'].setValue(new_filename)
                    