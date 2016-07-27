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
import re

import sgtk
from sgtk import TankError

hook = sgtk.get_hook_baseclass()

import nuke


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
        engine = self.parent.engine
        if hasattr(engine, "hiero_enabled") and self.parent.engine.hiero_enabled:
            return self._hiero_execute()
        elif hasattr(engine, "studio_enabled") and self.parent.engine.studio_enabled:
            return self._studio_execute()
        else:
            return self._nuke_execute()
            
    def _studio_execute(self):
        """
        The Nuke Studio-specific scan_scene routine.
        """
        # Run both the Hiero and Nuke routines, and combine the results.
        hiero_references_scanned, hiero_tasks = self._hiero_execute()
        nuke_references_scanned, nuke_tasks = self._nuke_execute()
        references_scanned = hiero_references_scanned + nuke_references_scanned
        tasks = hiero_tasks + nuke_tasks
        return references_scanned, tasks
    
    def _hiero_execute(self):
        """
        The Hiero-specific scan_scene routine.
        """
        
        #Declare some stuff we will need:
        import hiero.core
        
        engine = self.parent.engine
        types = self.parent.get_setting("scene_item_types")
        
        references_scanned = 0
        tasks = []
        
        # iterate through scene_item_types from config:
        for type in types:
            destination_path_template = engine.sgtk.templates[type["destination_path_template"]]
            if type["type"] == "clip":
                 continue
        
        return references_scanned, tasks
    
    def _nuke_execute(self):
        """
        The Nuke-specific scan_scene routine.
        """
        
        #Declare some stuff we will need:
        
        engine = self.parent.engine
        types = self.parent.get_setting("scene_item_types")
        project_path = engine.sgtk.project_path.replace("\\","/")
        
        references_scanned = 0
        tasks = []
        
        # iterate through scene_item_types from config:
        for type in types:
            destination_path_template = engine.sgtk.templates[type["destination_path_template"]]
            
            all_nodes = nuke.allNodes()
            
            # We're processing the read nodes three times based on content, because
            
            if type["type"] == "read_node_sequence":
                # For read nodes, we go through all read node objects, see if their path is inside 
                # the project path. If not, we must determine if it is a sequence before listing all the 
                # files we need.
                
                read_nodes = [node for node in all_nodes if 'Read' in node['name'].value()]
                
                if len(read_nodes) == 0:
                    print "tk-multi-collectfiles found no read nodes to process."
                    continue
                
                fields = engine.context.as_template_fields(destination_path_template)
                
                for node in read_nodes:
                    filename = node['file'].value()
                    ext = os.path.splitext(filename)[1].lower()
                    # Make sure the file is a type we care about:
                    if ext not in type["extensions"]:
                        continue
                    
                    source_path,file = os.path.split(filename)
                    
                    # Then determine if it is a sequence:
                    if file.find("%") != -1:
                        sequence_name = file.split("%")[0]
                        sequence_ext = file.split(re.search('%[0-9]{2}d',file).group(0))[1]
                        is_sequence = True
                    else:
                        is_sequence = False
                        continue
                    
                    # Now that we're sure this is the right type, we can increment the counter.
                    references_scanned += 1
                    
                    # Next determine if the file is inside the project:
                    if not os.path.isabs(filename):
                        # Relative paths should always be inside the project.
                        continue
                    if filename.startswith(project_path):
                        continue
                    
                                        
                    # Now we get the rest of the stuff we may need for our template
                    version_search = re.search('_v[0-9]{2,5}',filename)
                    if version_search:
                        version = int(version_search.group(0)[2:])
                        fields['pass'] = file.split(version_search.group(0))[0]
                    else:
                        version = 1
                        fields['pass'] = sequence_name.rstrip('.')
                    
                    fields['version'] = version
                    
                    target_path = destination_path_template.apply_fields(fields)
                    
                    # Now we build the lists of source and target filenames:
                        
                    if is_sequence:
                        source_files = glob.glob(os.path.join(source_path,sequence_name+"*"+sequence_ext))
                        target_files = [os.path.join(target_path,os.path.split(source_file)[1]) for source_file in source_files]
                        new_filename = os.path.join(target_path,file)
                    else:
                        new_filename = os.path.join(target_path,file)
                        source_files = [filename]
                        target_files = [new_filename]
                        
                    
                    tasks += [{ "type": "read_node_sequence",
                                "name": node['name'].value(),
                                "source_files":source_files,
                                "target_files":target_files,
                                "error":False,
                                "other_params":{"new_filename":new_filename,
                                    "task_object":node
                                    }
                                }]
            elif type["type"] == "read_node_movie":
                # For read nodes, we go through all read node objects, see if their path is inside 
                # the project path. If not, we must determine if it is a sequence before listing all the 
                # files we need.
                
                read_nodes = [node for node in all_nodes if 'Read' in node['name'].value()]
                
                if len(read_nodes) == 0:
                    print "tk-multi-collectfiles found no read nodes to process."
                    continue
                
                fields = engine.context.as_template_fields(destination_path_template)
                
                for node in read_nodes:
                    
                    filename = node['file'].value()
                    ext = os.path.splitext(filename)[1].lower()
                    # Make sure the file is a type we care about:
                    if ext not in type["extensions"]:
                        continue
                    
                    # Now that we're sure this is the right type, we can increment the counter.
                    references_scanned += 1
                    
                    
                    # Next determine if the file is inside the project:
                    if not os.path.isabs(filename):
                        # Relative paths should always be inside the project.
                        continue
                    if filename.startswith(project_path):
                        continue
                    
                    source_path,file = os.path.split(filename)
                    
                      
                    # Now we get the rest of the stuff we may need for our template
                    version_search = re.search('_v[0-9]{2,5}',filename)
                    if version_search:
                        version = int(version_search.group(0)[2:])
                        fields['pass'] = file.split(version_search.group(0))[0]
                    else:
                        version = 1
                        fields['pass'] = sequence_name.rstrip('.')
                    
                    fields['version'] = version
                                        
                    target_path = destination_path_template.apply_fields(fields)
                    
                    # Now we build the lists of source and target filenames:
                        
                    new_filename = os.path.join(target_path,file)
                    source_files = [filename]
                    target_files = [new_filename]
                        
                    
                    tasks += [{ "type": "read_node_movie",
                                "name": node['name'].value(),
                                "source_files":source_files,
                                "target_files":target_files,
                                "error":False,
                                "other_params":{"new_filename":new_filename,
                                    "task_object":node
                                    }
                                }]
            elif type["type"] == "read_node_still":
                # For read nodes, we go through all read node objects, see if their path is inside 
                # the project path. If not, we must determine if it is a sequence before listing all the 
                # files we need.
                
                read_nodes = [node for node in all_nodes if 'Read' in node['name'].value()]
                
                if len(read_nodes) == 0:
                    print "tk-multi-collectfiles found no read nodes to process."
                    continue
                
                fields = engine.context.as_template_fields(destination_path_template)
                
                for node in read_nodes:
                    
                    filename = node['file'].value()
                    ext = os.path.splitext(filename)[1].lower()
                    # Make sure the file is a type we care about:
                    if ext not in type["extensions"]:
                        continue
                    
                    source_path,file = os.path.split(filename)
                    
                    # Then determine if it is a sequence:
                    if file.find("%") != -1:
                        continue
                    
                    # Now that we're sure this is the right type, we can increment the counter.
                    references_scanned += 1
                    
                    # Next determine if the file is inside the project:
                    if not os.path.isabs(filename):
                        # Relative paths should always be inside the project.
                        continue
                    
                    if filename.startswith(project_path):
                        continue
                    
                    
                    # Now we get the rest of the stuff we may need for our template
                    version_search = re.search('_v[0-9]{2,5}',filename)
                    if version_search:
                        version = int(version_search.group(0)[2:])
                    else:
                        version = 1
                    
                    fields['version'] = version
                    
                    target_path = destination_path_template.apply_fields(fields)
                    
                    # Now we build the lists of source and target filenames:
                        
                    new_filename = os.path.join(target_path,file)
                    source_files = [filename]
                    target_files = [new_filename]
                        
                    
                    tasks += [{ "type": "read_node_still",
                                "name": node['name'].value(),
                                "source_files":source_files,
                                "target_files":target_files,
                                "error":False,
                                "other_params":{"new_filename":new_filename,
                                    "task_object":node
                                    }
                                }]
            elif type["type"] == "clip_source":
                #Nuke Studio / Hiero thing
                pass
            elif type["type"] == "nuke_script":
                #Nuke Studio / Hiero thing
                # To-do
                pass
            else:
                raise TankError("Item type '"+type["type"]+" in configuration is not supported by hook!")
            print "DEBUG INFO: ",
            for task in tasks:
                print task['name'],
            print "\n"
        return references_scanned, tasks