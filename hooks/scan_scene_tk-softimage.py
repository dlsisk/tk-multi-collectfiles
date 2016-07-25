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
import glob

import sgtk
from sgtk import TankError

hook = sgtk.get_hook_baseclass()

import win32com
from win32com.client import Dispatch as d
from win32com.client import constants as c
from pywintypes import com_error

Application = d("XSI.Application").Application
log = Application.LogMessage

class ScanSceneHook(hook):
    """
    Hook to scan scene for external files to copy
    """
    
    #def execute(self, app_instance, **kwargs):
    def execute(self, **kwargs):
        """
        Main hook entry point
        :returns:   
                    references_scanned: int
                                        Number of external file references found.
                    tasks:              list
                                        A list of any items that were found that need to be copied into 
                                        the project. Each item in the list should be a dictionary 
                                        containing the following keys:
                                        {
                                            type:   String
                                                    This should match a scene_item_type defined in
                                                    one of the outputs in the configuration and is 
                                                    used to determine how the item is processed.
                                                    
                                            name:   String
                                                    Associated scene object name for the item.
                                            
                                            source_files:   List
                                                            List of files associated with the object that 
                                                            need to be copied.
                                            target_files:   List
                                                            List of file locations corresponding to 
                                                            source_files, each of which is the target
                                                            for the copy_file method.
                                            other_params:   Dictionary
                                                            Optional dictionary that will be passed to the
                                                            update_references hook.
                                        }
        """
        
        #Declare some more stuff we will need:
        engine = sgtk.platform.current_engine()
        types = self.parent.get_setting("scene_item_types")
        
        references_scanned = 0
        tasks = []
        
        # iterate through scene_item_types from config:
        for type in types:
            destination_path_template = engine.sgtk.templates[type["destination_path_template"]]
            if type["type"] == "image_source":
                # For image sources, we go through all image source objects, see if their path is inside 
                # the project path. If so, we must determine if it is a sequence before listing all the 
                # files we need.
                
                sourceType = "{BB74AA1E-12C5-11D3-B37A-00105A1E70DE}" # This is an image source.
                images = Application.FindObjects("",sourceType)
                images.Remove("Sources.noIcon_pic") #Generally speaking, we don't care about collecting noIcon_pic.
                
                if len(images) == 0:
                    log("tk-multi-collectfiles found no image sources to process.", 8)
                    continue
                
                fields = engine.context.as_template_fields(destination_path_template)
                target_path = destination_path_template.apply_fields(fields)
                
                for image in images:
                    references_scanned += 1
                    filename = image.FileName.Value
                    ext = os.path.splitext(filename)[1]
                    # Make sure the file is a type we care about:
                    if ext not in type["extensions"]:
                        continue
                    
                    # Next determine if the file is inside the project:
                    if not os.path.isabs(filename):
                        # Relative paths should always be inside the project.
                        continue
                    if filename.startswith(engine.sgtk.project_path):
                        continue
                    
                    
                    source_path,file = os.path.split(filename)
                    
                    # Then determine if it is a sequence:
                    if file.find("[") != -1:
                        log("Image source is a sequence.",16)
                        sequence_name = file.split("[")[0]
                        sequence_ext = file.split("]")[1]
                        is_sequence = True
                    elif file.find("<UDIM>") != -1:
                        log("Image source is a UDIM sequence.",16)
                        sequence_name, sequence_ext = file.split("<UDIM>")
                        is_sequence = True
                    else:
                        log("Image source is not a sequence.",16)
                        is_sequence = False
                    
                    # Now we build the lists of source and target filenames:
                        
                    if is_sequence:
                        source_files = glob.glob(os.path.join(source_path,sequence_name+"*"+sequence_ext))
                        target_files = [os.path.join(target_path,sequence_name.rstrip('.'),os.path.split(source_file)[1]) for source_file in source_files]
                        new_filename = os.path.join(target_path,sequence_name.rstrip('.'),file)
                    else:
                        new_filename = os.path.join(target_path,file)
                        source_files = [filename]
                        target_files = [new_filename]
                        
                    
                    tasks += [{ "type": "image_source",
                                "name": image.FullName,
                                "source_files":source_files,
                                "target_files":target_files,
                                "error":False,
                                "other_params":{"new_filename":new_filename,
                                    "task_object":image
                                    }
                                }]
            else:
                raise TankError("Item type '"+type["type"]+" in configuration is not supported by hook!")
        return references_scanned, tasks