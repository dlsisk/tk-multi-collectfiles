# Copyright (c) 2013 Shotgun Software Inc.
# 
# CONFIDENTIAL AND PROPRIETARY
# 
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit 
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your 
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights 
# not expressly granted therein are reserved by Shotgun Software Inc.

import sgtk
import os
import sys
import threading

# by importing QT from sgtk rather than directly, we ensure that
# the code will be compatible with both PySide and PyQt.
from sgtk.platform.qt import QtCore, QtGui
#from .ui.dialog import Ui_Dialog

def execute():
    self = CollectFiles()
    CollectFiles.execute(self)

class CollectFiles(QtGui.QWidget):
    """
    
    """
    
    def __init__(self):
        """
        Constructor
        """
        
        # first, call the base class and let it do its thing.
        QtGui.QWidget.__init__(self)
        
        """
        # now load in the UI that was created in the UI designer
        self.ui = Ui_Dialog() 
        self.ui.setupUi(self)
        """
        # most of the useful accessors are available through the Application class instance
        # it is often handy to keep a reference to this. You can get it via the following method:
        self._app = sgtk.platform.current_bundle()
        
        # via the self._app handle we can for example access:
        # - The engine, via self._app.engine
        # - A Shotgun API instance, via self._app.shotgun
        # - A tk API instance, via self._app.tk 
        
        """
        # lastly, set up our very basic UI
        self.ui.context.setText("Current Context: %s" % self._app.context)
        """
        
    def execute(self):
        """
        Make thing go.
        """
                
        references_scanned, tasks = self._app.execute_hook_method("hook_scan_scene", "execute")
        count = len(tasks)
        
        tasks, bad_object_names = self._copy_files(tasks)
        updated_count, more_bad_object_names = self._app.execute_hook_method("hook_update_references","execute", tasks=tasks)
        bad_object_names = bad_object_names.union(more_bad_object_names)
        log_msg = "Found "+str(references_scanned)+" external file references, and copied & updated links on "+str(updated_count)+"."
        if bad_object_names:
            log_msg += "\n\ntk-multi-collectfiles also encountered errors processing the following scene objects. Please relocate their external files and update links manually:\n"
            object_list = list(bad_object_names)
            object_list.sort()
            for object_name in object_list:
                log_msg += "\n"+object_name
        self._app.engine.execute_in_main_thread(QtGui.QMessageBox.information, None, "Collect External Files", log_msg)
        return True
    
    def _copy_files(self,tasks):
        """
        Internal method to copy files
        """
        bad_object_names = set()
        result =  QtGui.QMessageBox.Yes
        for i, task in enumerate(tasks):
            files = [(task["source_files"][j], task["target_files"][j]) for j in range(len(task["source_files"]))]
            error_count = 0
            
            if files:
                source0, target0 = files[0]
                isfile = os.path.isfile(target0)
                if isfile and (result != QtGui.QMessageBox.YesToAll and result != QtGui.QMessageBox.NoToAll):
                    result = QtGui.QMessageBox.question(QtGui.QWidget(),"Overwrite File?", "One or more files relating to object "+task["name"]+" already exist in the target location. Overwrite files for this task?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.YesToAll | QtGui.QMessageBox.NoToAll, QtGui.QMessageBox.Yes)
                if (not isfile) or (result == QtGui.QMessageBox.Yes or result == QtGui.QMessageBox.YesToAll):
                    for source,target in files:
                        try:
                            self._app.execute_hook_method("hook_copy_file","execute",source_path=source,target_path=target)
                        except:
                            error_count += 1

                if error_count == 0:
                    tasks[i]["error"] = False
                else:
                    bad_object_names.add(task["name"])
                    tasks[i]["error"] = True
                

        return tasks, bad_object_names