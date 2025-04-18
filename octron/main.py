"""
OCTRON
Main GUI file

"""
import os, sys
import time
from typing import List, Optional
# if using Apple MPS, fall back to CPU for unsupported ops
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import shutil
from datetime import datetime
import warnings
# Suppress specific warnings
# warnings.filterwarnings("ignore", message="Duplicate name: 'masks/c/")
# warnings.filterwarnings("ignore", category=FutureWarning)
warnings.simplefilter("ignore")

from pathlib import Path
cur_path  = Path(os.path.abspath(__file__)).parent.parent
base_path = Path(os.path.dirname(__file__)) # Important for example for .svg files
sys.path.append(cur_path.as_posix()) 

# PyTorch
import torch

# Napari plugin QT components
from qtpy.QtCore import Qt
from qtpy.QtWidgets import (
    QWidget,
    QDialog,
    QApplication,
    QStyleFactory,
    QFileDialog,
    QMessageBox,
    QHeaderView,
)
import napari
from napari.utils.notifications import (
    show_info,
    show_warning,
    show_error,
)
from napari.qt import create_worker
from napari.utils import DirectLabelColormap

# Napari PyAV reader 
from napari_pyav._reader import FastVideoReader

# GUI 
from octron.gui_elements import octron_gui_elements
from octron.gui_tables import ExistingDataTable

# SAM2 specific 
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
import numpy as np
from octron.sam2_octron.helpers.video_loader import probe_video, get_vfile_hash
from octron.sam2_octron.helpers.build_sam2_octron import build_sam2_octron  
from octron.sam2_octron.helpers.sam2_checks import check_sam2_models
from octron.sam2_octron.helpers.sam2_zarr import (
    create_image_zarr,
    load_image_zarr,
)

# YOLO specific 
from octron.yolo_octron.helpers.training import collect_labels, load_object_organizer
from octron.yolo_octron.yolo_octron import YOLO_octron

# Annotation layer creation tools
from octron.sam2_octron.helpers.sam2_layer import (
    add_sam2_mask_layer,
    add_sam2_shapes_layer,
    add_sam2_points_layer,
    add_annotation_projection,
)                

# Layer callbacks classes
from octron.sam2_octron.helpers.sam2_layer_callback import sam2_octron_callbacks

# OCTRON Object organizer
from octron.sam2_octron.object_organizer import Obj, ObjectOrganizer
  
# Custom dialog boxes
from octron.gui_dialog_elements import (
    add_new_label_dialog,
    remove_label_dialog,
    remove_video_dialog,
)

# If there's already a QApplication instance (as may be the case when running as a napari plugin),
# then set its style explicitly:
# Enable high DPI support
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
app = QApplication.instance()
if app is not None:
    # This is a hack to get the style to look similar on darwin and windows systems
    # for the ToolBox widget
    app.setStyle(QStyleFactory.create("Fusion")) 


class octron_widget(QWidget):
    """
    Main OCTRON widget class.
    """

    def __init__(self, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(parent)
        base_path_parent = base_path # TODO: Get rid of this path madness
        self.base_path = Path(os.path.abspath(__file__)).parent
        self._viewer = viewer
        self.app = QApplication.instance()
        self.remove_all_layers() # Aggressively delete all pre-existing layers in the viewer ...🪦 muahaha
        
        # Initialize some variables
        self.project_path = None # Main project path that the user selects
        self.project_path_video = None # Video path that the user selects
        self.video_layer = None
        self.current_video_hash = None # Hashed video file
        self.video_zarr = None
        self.all_zarrs = [] # Collect zarrs in list so they can be cleaned up upon closing
        self.prefetcher_worker = None
        self.predictor, self.device, self.device_label = None, None, None
        self.object_organizer = ObjectOrganizer() # Initialize top level object organizer
        self.remove_current_layer = False # Removal of layer yes/no
        self.layer_to_remove_idx = None # Index of layer to remove
        self.layer_to_remove = None # The actual layer to remove
        self.polygon_interrupt  = False # Training data generation interrupt
        self.polygons_generated = False
        self.training_data_interrupt  = False # Training data generation interrupt
        self.training_data_generated = False
        self.training_finished = False # YOLO training
        self.trained_models = {}
        self.videos_to_predict = {}
        # ... and some parameters
        self.chunk_size = 15 # Global parameter valid for both creation of zarr array and batch prediction 
                             # For zarr arrays I set the minimum to ~50 frames for now
        self.skip_frames = 1 # Skip frames for prefetching images
        
        # Device label?
        if torch.cuda.is_available():
            self.device_label = "cuda" # torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device_label = "cpu" #"mps" # torch.device("mps")
            print(f'MPS is available, but not yet supported. Using CPU instead.')
        else:
            self.device_label = "cpu" #torch.device("cpu")
        print(f'Using YOLO device: "{self.device_label}"')
        
        # Model yaml for SAM2
        sam2models_yaml_path = self.base_path / 'sam2_octron/sam2_models.yaml'
        self.sam2models_dict = check_sam2_models(SAM2p1_BASE_URL='',
                                             models_yaml_path=sam2models_yaml_path,
                                             force_download=False,
                                             )
        # Model yaml for YOLO
        yolo_models_yaml_path = self.base_path / 'yolo_octron/yolo_models.yaml'
        self.yolo_octron = YOLO_octron(models_yaml_path=yolo_models_yaml_path) # Feeding in yaml to initiate models dict
        self.yolomodels_dict = self.yolo_octron.models_dict 
        
        # Initialize all UI components
        octron_gui = octron_gui_elements(self)
        octron_gui.setupUi(base_path=base_path_parent) # base_path is important for .svg files
        
        # (De)activate certain functionality while WIP 
        last_index = self.layer_type_combobox.count() - 1
        self.layer_type_combobox.model().item(last_index).setEnabled(False)
        
        # Populate SAM2 dropdown list with available models
        for model_id, model in self.sam2models_dict.items():
            print(f"Adding SAM2 model {model_id}")
            self.sam2model_list.addItem(model['name'])
            
        # Populate YOLO dropdown list with available models
        for model_id, model in self.yolomodels_dict.items():
            print(f"Adding YOLO model {model_id}")
            self.yolomodel_list.addItem(model['name'])
            
        # Connect (global) GUI callbacks 
        self.gui_callback_functions()
        # Connect layer specific callbacks
        self.octron_sam2_callbacks = sam2_octron_callbacks(self)

    ###################################################################################################
    
    def gui_callback_functions(self):
        """
        Connect all callback functions to buttons and lists in the main GUI
        """
        # Global layer insertion callback
        self._viewer.layers.events.inserted.connect(self.consolidate_layers)
        
        # Global layer removal callback
        self._viewer.layers.events.removing.connect(self.on_layer_removing)
        self._viewer.layers.events.removed.connect(self.on_layer_removed)
        
        # Buttons 
        # ... project 
        self.create_project_btn.clicked.connect(self.open_project_folder_dialog)
        # ... SAM2 and annotations 
        self.load_sam2model_btn.clicked.connect(self.load_sam2model)
        self.create_annotation_layer_btn.clicked.connect(self.create_annotation_layers)
        self.predict_next_batch_btn.clicked.connect(self.init_prediction_threaded)
        self.predict_next_oneframe_btn.clicked.connect(self.init_prediction_threaded)    
        self.create_projection_layer_btn.clicked.connect(self.create_annotation_projections)
        self.hard_reset_layer_btn.clicked.connect(self.reset_predictor)
        self.hard_reset_layer_btn.setEnabled(False)
        # ... YOLO
        self.generate_training_data_btn.setText('')
        self.generate_training_data_btn.clicked.connect(self.init_training_data_threaded)
        self.start_stop_training_btn.setText('')
        self.start_stop_training_btn.clicked.connect(self.init_yolo_training_threaded)
        self.predict_start_btn.setText('')
        self.predict_start_btn.clicked.connect(self.init_yolo_prediction_threaded)
        # ... YOLO predictions 
        self.predict_iou_thresh_spinbox.valueChanged.connect(self.on_iou_thresh_change)
        # Lists
        self.label_list_combobox.currentIndexChanged.connect(self.on_label_change)
        self.videos_for_prediction_list.currentIndexChanged.connect(self.on_video_prediction_change)
        # Upon start, disable some of the toolbox tabs and functionality for video drop 
        self.project_video_drop_groupbox.setEnabled(False)
        self.toolBox.widget(1).setEnabled(False) # Annotation
        self.toolBox.widget(2).setEnabled(False) # Training
        self.toolBox.widget(3).setEnabled(False) # Prediction
        
        # Disable layer annotation until SAM2 model is loaded
        self.annotate_layer_create_groupbox.setEnabled(False)
        
        # And ... 
        self.train_generate_groupbox.setEnabled(False)
        self.train_train_groupbox.setEnabled(False)
        # ... 
        self.predict_video_drop_groupbox.setEnabled(False)
        self.predict_video_predict_groupbox.setEnabled(False)
        
        # Connect to the Napari viewer close event
        self.app.lastWindowClosed.connect(self.closeEvent)
    

    ###### SAM2 SPECIFIC CALLBACKS ####################################################################
    
    def load_sam2model(self):
        """
        Load the selected SAM2 model and enable the batch prediction button, 
        setting the progress bar to the chunk size and the button text to predict next chunk size
        
        """
        index = self.sam2model_list.currentIndex()
        if index == 0:
            return
    
        model_name = self.sam2model_list.currentText()
        # Reverse lookup model_id
        for model_id, model in self.sam2models_dict.items():
            if model['name'] == model_name:
                break
        
        print(f"Loading SAM2 model {model_id}")
        model = self.sam2models_dict[model_id]
        config_path = Path(model['config_path'])
        checkpoint_path = self.base_path / Path(f"sam2_octron/{model['checkpoint_path']}")
        self.predictor, self.device = build_sam2_octron(config_file_path=config_path.as_posix(),
                                                        ckpt_path=checkpoint_path.as_posix(),
                                                        )
        self.predictor.is_initialized = False
        show_info(f"SAM2 model {model_name} loaded on {self.device}")
        # Deactivate the dropdown menu upon successful model loading
        self.sam2model_list.setEnabled(False)
        self.load_sam2model_btn.setEnabled(False)
        self.load_sam2model_btn.setText(f'{model_name} ✓')

        # Enable the predict next batch button
        # Take care of chunk size for batch prediction
        self.batch_predict_progressbar.setMaximum(self.chunk_size)
        self.batch_predict_progressbar.setValue(0)
        
        self.predict_next_batch_btn.setText(f'▷ {self.chunk_size} frames')
        self.predict_next_oneframe_btn.setText('▷')
        self.predict_next_oneframe_btn.setEnabled(True)
        self.predict_next_batch_btn.setEnabled(True)
        
        # Check if you can create a zarr store for video
        # Creating a zarr store for the video is only possible if a video has been loaded
        # AND a model has been loaded
        self.init_zarr_prefetcher_threaded()
        # Enable the annotation layer creation tab
        self.annotate_layer_create_groupbox.setEnabled(True)
        
        
    def reset_predictor(self):
        """
        Reset the predictor and all layers.
        """
        self.predictor.reset_state()
        annotation_layers = self.object_organizer.get_annotation_layers()
        for layer in annotation_layers:
            layer.data = []
        show_info("SAM2 predictor was reset.")
        
    
    def _batch_predict_yielded(self, value):
        """
        prediction_worker()
        Called upon yielding from the batch prediction thread worker.
        Updates the progress bar and the mask layer with the predicted mask.
        """
        progress, frame_idx, obj_id, mask, last_run = value
        organizer_entry = self.object_organizer.get_entry(obj_id)
        # Extract current mask layer
        prediction_layer = organizer_entry.prediction_layer
        prediction_layer.data[frame_idx,:,:] = mask
        prediction_layer.refresh()  
        if self._viewer.dims.current_step[0] != frame_idx and not last_run:
            self._viewer.dims.set_point(0, frame_idx)
        self.batch_predict_progressbar.setValue(progress)
          
    def _on_prediction_finished(self):
        """
        prediction_worker()
        Callback for when worker within init_prediction_threaded() 
        has finished executing. 
        """
        # Enable the predcition button again
        self.predict_next_batch_btn.setEnabled(True)
        self.predict_next_oneframe_btn.setEnabled(True)
        self.skip_frames_spinbox.setEnabled(True)
        self.batch_predict_progressbar.setValue(0)
        
        # Save the object organizer and also refresh the table view
        # ! TODO: Make this more efficient. This slows down everything a lot since 
        # what we are doing here is creating a video hash from scratch twice (?) and 
        # load the video data, plus we find out which indices have annotation data in the 
        # video. So, that is a lot of processing for just refreshing the table view for example 
        self.save_object_organizer()
        self.refresh_label_table_list() # This is the table in the project tab
        self.batch_predict_progressbar.setMaximum(self.chunk_size)    

    def init_prediction_threaded(self):
        """
        Thread worker for predicting the next batch of images
        """
        
        # Before doing anything, make sure, some input has been provided
        valid = False
        if (self.predictor.inference_state['point_inputs_per_obj'] or 
            self.predictor.inference_state['mask_inputs_per_obj']):
            valid = True
        if not valid:
            show_warning("Please annotate at least one object first.")
            return

        # Identify the sender (button) that called this function
        sender = self.sender()
        
        # Disable the prediction button
        self.predict_next_batch_btn.setEnabled(False)
        self.predict_next_oneframe_btn.setEnabled(False)
        self.skip_frames_spinbox.setEnabled(False)
        if sender == self.predict_next_batch_btn:
            self.prediction_worker = create_worker(self.octron_sam2_callbacks.batch_predict)
            self.prediction_worker.setAutoDelete(True)
            self.prediction_worker.yielded.connect(self._batch_predict_yielded)
            self.prediction_worker.finished.connect(self._on_prediction_finished)
            self.prediction_worker.start()
        elif sender == self.predict_next_oneframe_btn:
            self.batch_predict_progressbar.setMaximum(1)
            self.prediction_worker_one = create_worker(self.octron_sam2_callbacks.next_predict)
            self.prediction_worker_one.setAutoDelete(True)
            self.prediction_worker_one.yielded.connect(self._batch_predict_yielded)
            self.prediction_worker_one.finished.connect(self._on_prediction_finished)
            self.prediction_worker_one.start()
        

    ###### YOLO SPECIFIC CALLBACKS ####################################################################
    
    def _create_worker_polygons(self):
        # Create a new worker for polygon generation
        # Watershed? 
        enable_watershed = self.train_data_watershed_checkBox.isChecked()
        self.yolo_octron.enable_watershed = enable_watershed
        self.polygon_worker = create_worker(self.yolo_octron.prepare_polygons)
        self.polygon_worker.setAutoDelete(True) # auto destruct !!
        self.polygon_worker.yielded.connect(self._polygon_yielded)
        self.polygon_worker.finished.connect(self._on_polygon_finished)
        self.train_polygons_overall_progressbar.setEnabled(True)    
        self.train_polygons_frames_progressbar.setEnabled(True)
        self.train_polygons_label.setEnabled(True)
        
    def _create_worker_training_data(self):
        # Create a new worker for training data generation / export
        self.training_data_worker = create_worker(self.yolo_octron.create_training_data)
        self.training_data_worker.setAutoDelete(True) # auto destruct !!
        self.training_data_worker.yielded.connect(self._training_data_yielded)
        self.training_data_worker.finished.connect(self._on_training_data_finished)
        self.train_export_overall_progressbar.setEnabled(True)    
        self.train_export_frames_progressbar.setEnabled(True)
        self.train_polygons_label.setEnabled(True)
    
    def _uncouple_worker_polygons(self):
        try:
            self.polygon_worker.yielded.disconnect(self._polygon_yielded)
            self.polygon_worker.finished.disconnect(self._on_polygon_finished)
            self.polygon_worker.quit()
        except Exception as e:
            print(f"Error when uncoupling polygon worker: {e}")
            
    def _uncouple_worker_training_data(self):
        try:
            self.training_data_worker.yielded.disconnect(self._training_data_yielded)
            self.training_data_worker.finished.disconnect(self._on_training_data_finished)
            self.training_data_worker.quit()
        except Exception as e:
            print(f"Error when uncoupling training data worker: {e}")   

    def _polygon_yielded(self, value):
        """
        polygon_worker()
        Called upon yielding from the batch polygon generation thread worker.
        Updates the progress bar and label text next to it.
        """
        no_entry, total_label_dict, label, frame_no, total_frames = value
        self.train_polygons_overall_progressbar.setMaximum(total_label_dict)
        self.train_polygons_overall_progressbar.setValue(no_entry-1)
        self.train_polygons_frames_progressbar.setMaximum(total_frames) 
        self.train_polygons_frames_progressbar.setValue(frame_no)   
        self.train_polygons_label.setText(label)    

    def _on_polygon_finished(self):
        """
        polygon_worker()
        Callback for when polygon generation worker has finished executing. 
        """

        self.train_polygons_overall_progressbar.setValue(0)
        self.train_polygons_frames_progressbar.setValue(0)
        self.train_polygons_overall_progressbar.setEnabled(False)    
        self.train_polygons_frames_progressbar.setEnabled(False)
        self.train_polygons_label.setText('')
        self.train_polygons_label.setEnabled(False) 
        
        if self.polygon_interrupt:
            show_warning("Polygon generation interrupted.")  
            self.polygons_generated = False
            self.generate_training_data_btn.setStyleSheet('QPushButton { color: #8ed634;}')
            self.generate_training_data_btn.setText(f'▷ Generate')
        else:
            self.polygons_generated = True
            
        # If self.polygons_generated is True, then start the 
        # training data export worker right after ...
        if self.polygons_generated and not self.training_data_generated:
            # First call the data splitting function to split frames into train,test,val 
            self.yolo_octron.prepare_split() # This is so fast, we can just do it here
            self._training_data_export() 
        else:
            pass
            
            
    def _training_data_yielded(self, value):
        """
        training_data_worker()
        Called upon yielding from the batch training data generation thread worker.
        Updates the progress bar and label text next to it.
        """
        no_entry, total_label_dict, label, split, frame_no, total_frames = value
        self.train_export_overall_progressbar.setMaximum(total_label_dict)
        self.train_export_overall_progressbar.setValue(no_entry-1)
        self.train_export_frames_progressbar.setMaximum(total_frames) 
        self.train_export_frames_progressbar.setValue(frame_no)   
        self.train_export_label.setText(f'{label} ({split})')   
    
        
    def _on_training_data_finished(self):
        """
        training_data_worker()
        Callback for when training data generation worker has finished executing. 
        """
        self.generate_training_data_btn.setStyleSheet('QPushButton { color: #8ed634;}')
        self.generate_training_data_btn.setText(f'▷ Generate')
        self.train_export_overall_progressbar.setValue(0)
        self.train_export_frames_progressbar.setValue(0)
        self.train_export_overall_progressbar.setEnabled(False)    
        self.train_export_frames_progressbar.setEnabled(False)
        self.train_export_label.setText('')
        self.train_export_label.setEnabled(False) 
        
        if self.training_data_interrupt:
            show_warning("Training data generation interrupted.")  
            self.training_data_generated = False
        else:
            show_info("Training data generation finished.")
            self.training_data_generated = True
            self.generate_training_data_btn.setText(f'✓ Done.')
            self.generate_training_data_btn.setEnabled(False)   
            self.train_data_overwrite_checkBox.setEnabled(False)
            self.train_prune_checkBox.setEnabled(False)
            self.train_data_watershed_checkBox.setEnabled(False)
            # Write yolo config file 
            self.yolo_octron.write_yolo_config()    
            # Enable next part (YOLO training) of the pipeline 
            self.train_train_groupbox.setEnabled(True)
            self.launch_tensorboard_checkBox.setEnabled(True)
            self.start_stop_training_btn.setStyleSheet('QPushButton { color: #8ed634;}')
            self.start_stop_training_btn.setText(f'▷ Train')
        
    def _training_data_export(self):
        """
        MAIN MANAGER FOR TRAINING DATA EXPORT
        training_data_worker()
        Manages thread worker for exporting training data
        """
        if not self.training_data_interrupt and self.training_data_generated:
            self._on_training_data_finished()
            return
        # Otherwise, create a new worker and manage interruptions
        if not hasattr(self, 'training_data_worker'):
            self._create_worker_training_data()
            self.generate_training_data_btn.setStyleSheet('QPushButton { color: #e7a881;}')
            self.generate_training_data_btn.setText(f'🅧 Interrupt')
            self.training_data_worker.start()
            self.training_data_interrupt = False
        if hasattr(self, 'training_data_worker') and not self.training_data_worker.is_running:
            # Worker exists but is not running - clean up and create a new one
            self._uncouple_worker_training_data()
            self._create_worker_training_data()
            self.generate_training_data_btn.setStyleSheet('QPushButton { color: #e7a881;}')
            self.generate_training_data_btn.setText(f'🅧 Interrupt')
            self.training_data_worker.start()
            self.training_data_interrupt = False
        elif hasattr(self, 'training_data_worker') and self.training_data_worker.is_running:
            self.training_data_worker.quit()
            self.generate_training_data_btn.setStyleSheet('QPushButton { color: #8ed634;}')
            self.generate_training_data_btn.setText(f'▷ Generate')
            self.training_data_interrupt = True
            self.polygons_generated = False # this needs to be here, since polygon generation needs to run

        self.training_data_folder_label.setEnabled(True)
        self.training_data_folder_label.setText(f'→{self.yolo_octron.training_path.as_posix()[-38:]}')


    def _polygon_generation(self):
        """
        MAIN MANAGER FOR POLYGON GENERATION
        polygon_worker()
        Manages thread worker for generating polygons
        """
        # Check if the worker has already run and was not interrupted.
        # If so, do not create a new worker, but just call the callback function.
        if not self.polygon_interrupt and self.polygons_generated:
            self._on_polygon_finished()
            return
        # Otherwise, create a new worker and manage interruptions
        if not hasattr(self, 'polygon_worker'):
            self._create_worker_polygons()
            self.generate_training_data_btn.setStyleSheet('QPushButton { color: #e7a881;}')
            self.generate_training_data_btn.setText(f'🅧 Interrupt')
            self.polygon_worker.start()
            self.polygon_interrupt = False
        elif hasattr(self, 'polygon_worker') and not self.polygon_worker.is_running:
            # Worker exists but is not running - clean up and create a new one
            self._uncouple_worker_polygons()
            self._create_worker_polygons()
            self.generate_training_data_btn.setStyleSheet('QPushButton { color: #e7a881;}')
            self.generate_training_data_btn.setText(f'🅧 Interrupt')
            self.polygon_worker.start()
            self.polygon_interrupt = False
        elif hasattr(self, 'polygon_worker') and self.polygon_worker.is_running:
            self.polygon_worker.quit()
            self.generate_training_data_btn.setStyleSheet('QPushButton { color: #8ed634;}')
            self.generate_training_data_btn.setText(f'▷ Generate')
            self.polygon_interrupt = True
            

    def init_training_data_threaded(self):
        """
        This function manages the creation of polygon data and the subsequent
        creation / the export of training data.
        It kicks off the pipeline by calling the polygon generation function.
        
        """
        # Whenever the button "Generate" is clicked, 
        # the training data generation pipeline is started anew.
        if not hasattr(self, 'polygon_worker') and not hasattr(self, 'training_data_worker'):   
            self.polygons_generated = False
            self.training_data_generated = False   
        
        # Sanity check 
        if not self.project_path:
            show_warning("Please select a project directory first.")
            return
        if not hasattr(self, 'yolo_octron'):
            show_warning("Please load a YOLO first.")
            return
        # Check status of "Prune" checkbox
        prune = self.train_prune_checkBox.isChecked()
        if not self.yolo_octron.project_path:
            self.yolo_octron.project_path = self.project_path
        elif self.yolo_octron.project_path != self.project_path: 
            # Assuming that the user wants to change the project path
            self.yolo_octron.project_path = self.project_path

        self.save_object_organizer() # This is safe, since it checks whether a video was loaded
        try:
            # After saving the object organizer, extract info from all 
            # available .json files in the project directory
            self.yolo_octron.prepare_labels(
                        prune_empty_labels=prune, 
                        min_num_frames=5, # hardcoded ... less than 5 frames are not useful
                        verbose=True, 
            )
      
        except AssertionError as e:
            print(f"😵 Error when preparing labels: {e}")
            return
        # Kick off polygon generation - check are done within the following functions 
        self._polygon_generation()
            
    ###### YOLO TRAINERS ###########################################################################
    
            
    def _update_training_progress(self, progress_info):
        """
        Handle training progress updates from the worker thread.
        When finished, enable the next step.
        
        Parameters
        ----------
        progress_info : dict
            Dictionary containing training progress information
        """
        current_epoch = progress_info['epoch']
        total_epochs = progress_info['total_epochs']
        epoch_time = progress_info['epoch_time']
        remaining_time = progress_info['remaining_time']
        finish_time = progress_info['finish_time']
        
        # Format the finish time (without year as requested)
        finish_time_str = ' '.join(time.ctime(finish_time).split()[:-1])
   
        self.train_epochs_progressbar.setMaximum(total_epochs)
        self.train_epochs_progressbar.setValue(current_epoch)        
        self.train_finishtime_label.setText(f'↬ {finish_time_str}')
        
        print(f"Epoch {current_epoch}/{total_epochs} - Time for epoch: {epoch_time:.1f}s")
        print(f"Estimated time remaining: {remaining_time:.1f} seconds")    
        print(f"Estimated finish time: {finish_time_str}")  

        if current_epoch == total_epochs: 
            self.training_finished = True
            self.start_stop_training_btn.setStyleSheet('QPushButton { color: #8ed634;}')
            self.start_stop_training_btn.setText(f'✓ Done.')
            self.train_epochs_progressbar.setEnabled(False)  
            self.train_finishtime_label.setEnabled(False)
            # Enable the prediction tab
            self.toolBox.widget(3).setEnabled(True) # Prediction
            self.predict_video_drop_groupbox.setEnabled(True)
            self.predict_video_predict_groupbox.setEnabled(True)
            
    
    def _yolo_trainer(self):
        if not self.device_label:
            show_error("No device label found for YOLO.")
            return
        else:
            show_info(f"Training on device: {self.device_label}")
        
        # Call the training function which yields progress info
        for progress_info in self.yolo_octron.train(
                                            device=self.device_label, 
                                            imagesz=self.image_size_yolo,
                                            epochs=self.num_epochs_yolo,
                                            save_period=self.save_period,
                                        ):
            # Yield the progress info back to the GUI thread
            yield progress_info
            
            
    def _create_yolo_trainer(self):
        # Create a new worker for YOLO training 
        self.yolo_trainer_worker = create_worker(self._yolo_trainer)
        self.yolo_trainer_worker.setAutoDelete(True)  # auto destruct !!
        self.yolo_trainer_worker.yielded.connect(self._update_training_progress)
        self.train_epochs_progressbar.setEnabled(True)    
        self.train_finishtime_label.setEnabled(True)
        self.train_finishtime_label.setText('↬ ... wait one epoch')    
        if self.launch_tensorbrd:
            self.yolo_octron.quit_tensorboard()
            self.yolo_octron.launch_tensorboard()
            

    def init_yolo_training_threaded(self):
        """
        This function manages the training of the YOLO model.
        
        
        """
        if self.training_finished:
            return
        
        # Sanity check 
        if not self.project_path:
            show_warning("Please select a project directory first.")
            return
        if not hasattr(self, 'yolo_octron'):
            show_warning("Please load YOLO first.")
            return
        
        index_model_list = self.yolomodel_list.currentIndex()
        if index_model_list == 0:
            show_warning("Please select a YOLO model")
            return
        model_name = self.yolomodel_list.currentText()
        # Reverse lookup model_id
        for model_id, model in self.yolomodels_dict.items():
            if model['name'] == model_name:
                break        
        index_imagesize_list = self.yoloimagesize_list.currentIndex()
        if index_imagesize_list == 0:
            show_warning("Please select an image size")
            return 
        self.image_size_yolo = int(self.yoloimagesize_list.currentText())                                     
        # Check status of "Launch Tensorboard" checkbox
        self.launch_tensorbrd = self.launch_tensorboard_checkBox.isChecked()   
        # TODO: Implement these options
        #resume_training = self.train_resume_checkBox.isChecked()    
        #overwrite = self.train_training_overwrite_checkBox.isChecked()  
        
        self.num_epochs_yolo = int(self.num_epochs_input.value())   
        if self.num_epochs_yolo <= 1:
            show_warning("Please select a number of epochs >1")
            return
        self.save_period = int(self.save_period_input.value())
        
        # LOAD YOLO MODEL 
        print(f"Loading YOLO model {model_id}")
        yolo_model = self.yolo_octron.load_model(model_id)
        if not yolo_model:
            show_warning("Could not load YOLO model.")
            return
        
        # Deactivate the training data generation box 
        self.train_generate_groupbox.setEnabled(False)
        # Otherwise, create a new worker and manage interruptions
        if not hasattr(self, 'yolo_trainer_worker'):
            self._create_yolo_trainer()
            self.start_stop_training_btn.setStyleSheet('QPushButton { color: #e7a881;}')
            self.start_stop_training_btn.setText(f'↯ Training')
            self.yolo_trainer_worker.start()
            self.start_stop_training_btn.setEnabled(False)
            # Disable the training data generation box
            self.toolBox.widget(1).setEnabled(False) # Annotation
            
    ###### YOLO PREDICTION ###########################################################################
    
    def on_iou_thresh_change(self, value):
        """
        Callback for self.predict_iou_thresh_spinbox.
        If IOU threshold is < 0.01, 
        check and disable the 'single_subject_checkBox'.
        This is because at IOU < 0.01, only one object will be tracked
        by fusing all detections into 1 -> so it has the same effect. 
        
        """
        if value < 0.01:
            self.single_subject_checkBox.setChecked(True)
            self.single_subject_checkBox.setEnabled(False)
        else:
            self.single_subject_checkBox.setEnabled(True)
            self.single_subject_checkBox.setChecked(False)
            
        
    def _update_prediction_progress(self, progress_info):
        """
        Handle prediction progress updates from the worker thread.
        Updates progress bars and displays timing information.
        
        Parameters
        ----------
        progress_info : dict
            Dictionary containing prediction progress information
        """
        stage = progress_info.get('stage', '')
        
        if stage == 'processing':
            # Update UI for video processing
            video_name = progress_info.get('video_name', '')
            video_index = progress_info.get('video_index', 0)
            total_videos = progress_info.get('total_videos', 1)
            frame = progress_info.get('frame', 0)
            total_frames = progress_info.get('total_frames', 1)
            frame_time = progress_info.get('frame_time', 0) 
            
            remaining_time = (total_frames * frame_time) - (frame * frame_time)
            finish_time = time.time() + remaining_time
            finish_time_str = ' '.join(time.ctime(finish_time).split()[:-1])

            # Update labels
            if len(video_name) > 21:
                prefix = '...'
            else:
                prefix = ''
            shortened_video_name = f'{prefix}{video_name[-21:]}'
            
            self.predict_current_videoname_label.setText(f"{shortened_video_name}")
            self.predict_finish_time_label.setText(f"{frame_time:.2f}s per frame | Video completes ~ {finish_time_str}")
            
            # Update progress bars
            self.predict_overall_progressbar.setMaximum(total_videos)
            self.predict_current_video_progressbar.setMaximum(total_frames)
            self.predict_overall_progressbar.setValue(video_index)
            self.predict_current_video_progressbar.setValue(frame)
            
        elif stage == 'video_complete':
            # Show results? 
            save_dir = progress_info.get('save_dir', '')
            if self.view_prediction_resuts: 
                for label, track_id, _, _, _  in self.yolo_octron.show_predictions(save_dir=save_dir):
                    print(f"Adding tracking result to viewer | Label: {label}, Track ID: {track_id}")     
            
        elif stage == 'complete':
            self.yolo_prediction_worker.quit()
            # Reset video progress bar for next video
            self.predict_current_video_progressbar.setValue(0)
            self.predict_overall_progressbar.setValue(0)
            self.predict_current_video_progressbar.setEnabled(False)
            self.predict_overall_progressbar.setEnabled(False)
            
            
            self.predict_current_videoname_label.setText('')
            self.predict_finish_time_label.setText('')
            self.predict_current_videoname_label.setEnabled(False)
            self.predict_finish_time_label.setEnabled(False)
            
            # Re-enable UI elements
            self.predict_start_btn.setStyleSheet('QPushButton { color: #8ed634;}')
            self.predict_start_btn.setText('▷ Predict')
            self.predict_start_btn.setEnabled(True)
            self.toolBox.widget(1).setEnabled(True)  # Re-enable Annotation tab
            self.toolBox.widget(2).setEnabled(True)  # Re-enable Training tab
            self.predict_video_drop_groupbox.setEnabled(True)
                
            
    
    def _yolo_predictor(self):
        if not self.device_label:
            show_error("No device label found for YOLO.")
            return
        else:
            show_info(f"Predicting on device: {self.device_label}")
        
        one_object_per_label = self.single_subject_checkBox.isChecked()
        # Call the training function which yields progress info
        for progress_info in self.yolo_octron.predict_batch(
                                            videos_dict=self.videos_to_predict,
                                            model_path=self.model_predict_path,
                                            device=self.device_label,
                                            tracker_name=self.yolo_tracker_name,
                                            one_object_per_label=one_object_per_label,
                                            iou_thresh=self.iou_thresh,
                                            conf_thresh=self.conf_thresh,
                                            polygon_sigma=self.polygon_sigma,
                                            overwrite=self.overwrite_predictions, 
                                        ):

            # Yield the progress info back to the GUI thread
            yield progress_info
            
            
    def _create_yolo_predictor(self):
        # Create a new worker for YOLO prediction 
        self.yolo_prediction_worker = create_worker(self._yolo_predictor)
        self.yolo_prediction_worker.setAutoDelete(True)  # auto destruct !!
        self.yolo_prediction_worker.yielded.connect(self._update_prediction_progress)
        self.predict_overall_progressbar.setEnabled(True)  
        self.predict_current_video_progressbar.setEnabled(True)   
        self.predict_current_videoname_label.setEnabled(True)
        self.train_finishtime_label.setText('↬ ... waiting for estimate')    
        self.predict_finish_time_label.setEnabled(True)


    def init_yolo_prediction_threaded(self):
        """
        This function manages the prediction of videos
        with custom trained YOLO models
        
        
        """
        
        # Sanity check 
        if not self.project_path:
            show_warning("Please select a project directory first.")
            return
        if not hasattr(self, 'yolo_octron'):
            show_warning("Please load YOLO first.")
            return
        
        index_model_list = self.yolomodel_trained_list.currentIndex()
        if index_model_list == 0:
            show_warning("Please select a YOLO model")
            return
        model_name = self.yolomodel_trained_list.currentText()
        model_name = Path(model_name).stem
        # The self.trained_models dictionary contains the model name as key
        # and the model path as value
        assert model_name in self.trained_models, \
            f"Model {model_name} not found in trained models: {self.trained_models}"
        self.model_predict_path = self.trained_models[model_name]
        index_tracker_list = self.yolomodel_tracker_list.currentIndex()
        if index_tracker_list == 0:
            show_warning("Please select a tracker")
            return 
        # Check if there are any videos to predict 
        if not self.videos_to_predict:
            show_warning("Please select a video to predict.")
            return
        
        self.yolo_tracker_name = self.yolomodel_tracker_list.currentText()                              
        # Check status of "view results" checkbox
        self.view_prediction_resuts = self.open_when_finish_checkBox.isChecked()   
        self.polygon_sigma = float(self.predict_polygo_sigma_spinbox.value())
        self.conf_thresh = float(self.predict_conf_thresh_spinbox.value())
        self.iou_thresh = float(self.predict_iou_thresh_spinbox.value())
        self.overwrite_predictions = self.overwrite_prediction_checkBox.isChecked()    
        
        # Deactivate the training data generation box 
        self.train_generate_groupbox.setEnabled(False)
        # Create new prediction worker
        self._create_yolo_predictor()
        self.predict_start_btn.setStyleSheet('QPushButton { color: #e7a881;}')
        self.predict_start_btn.setText(f'↯ Predicting')
        self.yolo_prediction_worker.start()
        self.predict_start_btn.setEnabled(False)
        # Disable the annotation + training data generation tabs
        self.toolBox.widget(1).setEnabled(False) # Annotation
        self.toolBox.widget(2).setEnabled(False) # Training
        # And the video dropbox
        self.predict_video_drop_groupbox.setEnabled(False)
            
    ###### NAPARI SPECIFIC CALLBACKS ##################################################################
    
    def closeEvent(self):
        """
        Callback for the Napari viewer close event
        """
        
        for zarr_store in self.all_zarrs:
            if zarr_store is not None:
                store = zarr_store.store
                if hasattr(store, 'close'):
                    store.close()
                    print(f"Zarr {zarr_store} store closed.")
        # Clean up the prefetcher worker
        if self.prefetcher_worker is not None:
            self.prefetcher_worker.quit()
        # Lastly, save object organizer to json 
        if self.project_path:
            self.save_object_organizer()
            
    def save_object_organizer(self):
        """
        Save the object organizer to the project directory
        """
        if self.project_path_video is None or not self.project_path_video.exists():
            print("No project video path set or found. Not exporting object organizer.")
            return
        organizer_path = self.project_path_video  / "object_organizer.json"
        self.object_organizer.save_to_disk(organizer_path)

    def refresh_label_table_list(self):
        """
        Refresh the label list combobox with the current labels in the object organizer
        """
        # Check this folder for existing project data
        label_dict = collect_labels(self.project_path, 
                                    subfolder=self.current_video_hash, 
                                    prune_empty_labels=False,  
                                    min_num_frames=0
                                    )  
        if not label_dict:
            return
        
        # Initialize the table model if not already done
        if not hasattr(self, 'label_table_model'):
            self.label_table_model = ExistingDataTable()
            self.existing_data_table.setModel(self.label_table_model)
            
            # Configure the table appearance
            self.existing_data_table.horizontalHeader().setStretchLastSection(False)
            self.existing_data_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            # Connect double-click event on table rows 
            self.existing_data_table.doubleClicked.connect(self.on_label_table_double_clicked)
        
        # Update the table with new data
        self.label_table_model.update_data(label_dict)
        
        # Enable the groupbox for existing data and the training generation box
        self.project_existing_data_groupbox.setEnabled(True)
        self.train_generate_groupbox.setEnabled(True)
        self.generate_training_data_btn.setStyleSheet('QPushButton { color: #8ed634;}')
        self.generate_training_data_btn.setText(f'▷ Generate')
        
        # Enable training tab if data is available
        if label_dict and any(v for k, v in label_dict.items() if k != 'video' and k != 'video_file_path'):
            print("Data available, enabling training tab.")
            self.toolBox.widget(2).setEnabled(True)  # Training
            self.train_generate_groupbox.setEnabled(True)
            self.train_train_groupbox.setEnabled(True)
            # Enable some buttons too 
            self.train_data_watershed_checkBox.setEnabled(True)
            self.train_prune_checkBox.setEnabled(True)

    def on_label_table_double_clicked(self, index):
        """
        Handle double-click events on the existing data table.
        This is the ExistingDataTable() instance.
        
        Parameters
        ----------
        index : QModelIndex
            The index of the clicked cell
        """
        # Get the full folder path from the model
        folder_path = self.label_table_model.get_folder_path(index)
        if not folder_path:
            return

        # Load the video from the folder path
        video_file_path = Path(self.label_table_model.label_dict[folder_path].get('video_file_path'))
        if not video_file_path.exists():
            show_warning("No video file found in folder.")
            return
        
        # Remove the current video layer
        # This triggers a bunch of things -> check function for details
        if self.video_layer is not None:
            self._viewer.layers.remove(self.video_layer)
            
        # Reset variables for a clean start
        self.object_organizer = ObjectOrganizer()
        # SAM2 
        self.sam2model_list.setEnabled(True)
        self.load_sam2model_btn.setEnabled(True)
        self.load_sam2model_btn.setText(f'Load model')
        self.predict_next_batch_btn.setText('')
        self.predict_next_oneframe_btn.setText('')
        self.predict_next_oneframe_btn.setEnabled(False)
        self.predict_next_batch_btn.setEnabled(False)
            
        # Use the file drop method to load the video
        self.on_mp4_file_dropped_area([video_file_path])
        
        # Re-instantiate all layers
        # Find .json 
        folder_path = Path(folder_path)
        json_files = list(folder_path.glob('*.json'))
        if not json_files:
            show_warning("No .json files found in folder.")
            return
        if len(json_files) > 1:
            show_warning("More than one .json file found in folder.")
            return
        json_file = json_files[0]
        # Load the object organizer from the .json file
        object_organizer_data = load_object_organizer(json_file)
        if not object_organizer_data:
            show_warning("Could not load object organizer data.")
            return
        
        # Clear the label list combobox and re-initialize it
        self.label_list_combobox.clear()
        self.label_list_combobox.addItem("Label ...")
        self.label_list_combobox.addItem(u"\u2295 Create")
        self.label_list_combobox.addItem(u"\u2296 Remove")
        
        # Track unique labels to avoid duplicates
        unique_labels = set()
        # Loop over all objects in the object organizer data
        # and re-create the layers
        for obj_id, obj_data in object_organizer_data['entries'].items():
            print(f"Loading object with ID {obj_id}")
            obj_id = int(obj_id)
            label = obj_data.get('label', '')
            suffix = obj_data.get('suffix', '')
            obj_color = obj_data.get('color', [0.7, 0.7, 0.7, 1])
            
            # Add label to combobox if not already added
            if label and label not in unique_labels:
                unique_labels.add(label)
                self.label_list_combobox.addItem(label)
            
            # Determine layer type from metadata
            layer_type = None
            if 'annotation_layer_metadata' in obj_data:
                annotation_type = obj_data['annotation_layer_metadata'].get('type')
                if annotation_type == 'Shapes':
                    layer_type = 'Shapes'
                elif annotation_type == 'Points':
                    layer_type = 'Points'
            if not layer_type:  
                layer_type = 'Points' # Default to Points if not specified
             # Create layers with the reconstructed information
            print(f"Recreating layer: {label} {suffix} (ID: {obj_id}, Type: {layer_type})")
            self.create_annotation_layers(
                recreate=True,
                label=label,
                layer_type=layer_type,
                label_suffix=suffix,
                obj_id=obj_id,
                obj_color=obj_color
            )
            
            
        # Reset the combobox to the first item
        self.label_list_combobox.setCurrentIndex(0)    
        return
    
    
    def refresh_trained_model_list(self):
        """
        Refresh the trained model list combobox with the current models in the project directory
        """
        # Clear the old list, and re-instantiate
        self.yolomodel_trained_list.clear()
        self.yolomodel_trained_list.addItem('Choose model ...')
        
        trained_models = self.yolo_octron.find_trained_models(project_path=self.project_path)
        if not trained_models:
            self.toolBox.widget(3).setEnabled(False)
            return
        
        # Write the trained models to yolomodel_trained_list one by one
        for model in trained_models:
            if model.stem not in self.trained_models:
                self.trained_models[model.stem] = model
            self.yolomodel_trained_list.addItem('/'.join(model.parts[-5:]))
        # Enable prediction tab if trained models are available
        self.toolBox.widget(3).setEnabled(True)
        self.predict_video_drop_groupbox.setEnabled(True)
        self.predict_video_predict_groupbox.setEnabled(True)
        self.predict_start_btn.setEnabled(True)
        self.predict_start_btn.setStyleSheet('QPushButton { color: #8ed634;}')
        self.predict_start_btn.setText(f'▷ Predict')

    def open_project_folder_dialog(self):
        """
        Open a file dialog for the user to choose a base folder for the current OCTRON project.
        This yields self.project_path, which is used to store all project-related data.
        
        If the project path is an existing OCTRON project, it will be inspected and 
        the existing annotation data will be quickly displayed in a table view.
        
        """
        # Open a directory selection dialog
        folder = QFileDialog.getExistingDirectory(self, "Select Base Folder", str(Path.home()))
        if folder:
            print(f"Project base folder selected: {folder}")
            
            # Remove the current video layer
            # This triggers a bunch of things -> check function for details
            if self.video_layer is not None:
                self._viewer.layers.remove(self.video_layer)
            # Reset variables for a clean start
            self.object_organizer = ObjectOrganizer()
            
            folder = Path(folder)
            self.project_folder_path_label.setEnabled(False)
            self.project_folder_path_label.setText(f'→{folder.as_posix()}')
            
            self.project_path = folder
            self.project_video_drop_groupbox.setEnabled(True)
            self.refresh_label_table_list()
            self.refresh_trained_model_list()
        else:
            print("No folder selected.")
        return 
    

    def remove_all_layers(self, spare=[]):
        """
        Remove all layers from the napari viewer.
        
        Parameters
        ----------
        spare : list
            List of layers that should not be removed
        """
        if not isinstance(spare, list):
            spare = [spare]
        print(f'🗑️  Deleting all layers except "{spare}"')
        # First remove mask layers (to avoid dependencies with annotation layers)
        mask_layers = []
        other_layers = []
        
        # Categorize layers
        for layer in list(self._viewer.layers):
            if layer in spare:
                continue
            elif 'masks' in layer.name.lower():
                mask_layers.append(layer)
            else:
                other_layers.append(layer)
        # Remove mask layers first
        for layer in mask_layers:
            if layer in self._viewer.layers:
                self._viewer.layers.remove(layer)
        # Then remove other layers
        for layer in other_layers:
            if layer in self._viewer.layers:
                self._viewer.layers.remove(layer)
                
        total_deleted = len(mask_layers) + len(other_layers)
        if total_deleted:
            print(f"💀 Auto-deleted {total_deleted} layers")


    def on_layer_removed(self, event):
        """
        Callback triggered from within the layer removal event.
        (self.on_layer_removing() is called first)
        This gives the user a chance to cancel the removal of the layer.
        It also organizes the removal process according to which layer type is being removed. 
        
        """        
        if not self.remove_current_layer:
            # TODO: This is a bit of a hack, seems ugly. Is there a better way?
            new_old_layer = self._viewer.add_layer(self.layer_to_remove)
            self._viewer.layers.selection.active = new_old_layer
            self._viewer.layers.selection.active.mode = 'pan_zoom'
        else:
            print(f"❌ Removed layer {self.layer_to_remove.name}")
            # What else do you need to remove? 
            # Two cases:
            # 1. The layer is a mask layer
            # 2. The layer is an annotation layer
            # 3. The layer is a video layer 
            
            # 1. Mask layer
            if self.layer_to_remove._basename() == 'Labels' \
                and 'mask' in self.layer_to_remove.metadata['_name']:
                # Remove the zarr zip file containing the layer data
                # zarr_file_path = self.project_path / self.layer_to_remove.metadata['_zarr']
                # if Path(zarr_file_path).exists():
                #     shutil.rmtree(zarr_file_path)
                #     print(f'Removed Zarr file {zarr_file_path}')
                # Get the object entry from the object organizer
                obj_id = self.layer_to_remove.metadata['_obj_id']
                organizer_entry = self.object_organizer.get_entry(obj_id)
                annotation_layer = organizer_entry.annotation_layer
                # Remove the object entry from the object organizer
                self.object_organizer.remove_entry(obj_id)
                # Remove obj_id from current SAM2 predictor
                try:
                    self.predictor.remove_object(obj_id, strict=True)
                    print(f"Removed object with ID{obj_id} from organizer and predictor")
                except (RuntimeError, AttributeError) as e:
                    print(f"Error when removing object from SAM2 predictor: {e}")
                    print("This is likely due to the SAM2 model not being loaded and can be ignored.")
                
                # Finally, trigger removal of the annotation layer
                if annotation_layer is not None:
                    self._viewer.layers.remove(annotation_layer)
            # 2. Annotation layer
            elif self.layer_to_remove._basename() in ['Shapes', 'Points']:
                # Get the object entry from the object organizer
                obj_id = self.layer_to_remove.metadata['_obj_id']
                organizer_entry = self.object_organizer.get_entry(obj_id)
                if organizer_entry is not None:
                    organizer_entry.annotation_layer = None
            # 3. Video layer
            # This has more drastic consequences ...
            elif self.layer_to_remove._basename() == 'Image' and 'VIDEO' in self.layer_to_remove.name:
                # What to do: 
                # Remove all layers and reset SAM predictor
                self.remove_all_layers(spare=self.layer_to_remove)
                # Also re-instantiate variables
                self.project_path_video = None
                self.video_layer = None 
                self.current_video_hash = None
                self.video_zarr = None
                if hasattr(self, 'prefetcher_worker') and self.prefetcher_worker is not None:
                    self.prefetcher_worker.quit()
                self.prefetcher_worker = None
                self.all_zarrs = []
                # SAM2 
                self.predictor = None   
                self.sam2model_list.setEnabled(True)
                self.load_sam2model_btn.setEnabled(True)
                self.load_sam2model_btn.setText(f'Load model')
                self.predict_next_batch_btn.setText('')
                self.predict_next_oneframe_btn.setText('')
                self.predict_next_oneframe_btn.setEnabled(False)
                self.predict_next_batch_btn.setEnabled(False)
                # Object organizer
                self.object_organizer = ObjectOrganizer()
                # Disable the layer annotation box until SAM2 is loaded 
                self.annotate_layer_create_groupbox.setEnabled(False)
                # Reset naming of annotation tab 
                self.toolBox.setItemText(1, "Generate annotation data")
            # Reset the flag 
            self.remove_current_layer = False
    
        return
    
    
    def on_layer_removing(self, event):
        """ 
        Callback triggered when a layer is about to be removed.
        The call to on_layer_removed() is triggered after this, and gives 
        the user a chance to cancel the removal of the layer.
        """
        self.layer_to_remove = event.source[event.index]
        self.layer_to_remove_idx = event.index  
        # Not sure if possible to delete more than one at once.
        # If so, then take care of it ... event.sources is a list.
        if self.layer_to_remove._basename() in ['Shapes', 'Points', 'Image', 'Labels']:
            # Silent removal of annotation layers
            self.remove_current_layer = True
        # elif self.layer_to_remove._basename() == 'Image': #and 'VIDEO' not in self.layer_to_remove.name:
        #     # Silent removal of image layers (visualizations)
        #     self.remove_current_layer = True
        
        # LEAVE THIS IN HERE, it can be useful in the future. 
        # else:
        #     # Ask for confirmation for other layers, i.e. mask layers
        #     reply = QMessageBox.question(
        #         None, 
        #         "Confirmation", 
        #         f"Are you sure you want to delete layer\n'{self.layer_to_remove}'",
        #         QMessageBox.Yes | QMessageBox.No,
        #         QMessageBox.No
        #     )
        #     if reply == QMessageBox.No:
        #         self.remove_current_layer = False
        #     else:
        #         self.remove_current_layer = True
        return
          
    
    def consolidate_layers(self, event):
        """
        Callback triggered when a layers are changed in the viewer.
        Currently triggered only on INSERTION events (layers are added).
        
        Takes care of defining video layers.
        Searches for video layers with a basename of "Image" and "VIDEO" in
        the name. 


        Sets
        ----
        self.video_layer : napari.layers.Image
            The current video layer
        self.current_video_hash : str   
            The hash of the current video layer
        self.video_zarr : zarr.storage
            The zarr storage for the video layer (via the prefetcher)
        self.all_zarrs : list
            List of all zarr stores for the video layer (via the prefetcher)
        self.prefetcher_worker : QThread
            The worker thread for the prefetcher (via the prefetcher)
        self.project_path_video : Path
            The path to the video project directory
        """
        
        layer_name = event.value
        
        # Search through viewer layers for video layers with the expected criteria
        # Starting here as an example with video layers, but 
        # this could be anything in the future ... let's see if we need it 
        video_layers = []
        # Loop through all layers and check if they are video layers
        for l in self._viewer.layers:
            try:
                if l._basename() == 'Image' and 'VIDEO' in l.name:
                    video_layers.append(l)
            except Exception as e:
                show_error(f"💀 Error when checking layer: {e}")

        if len(video_layers) > 1:
            # This should never happen
            show_warning("🙀 More than one video layer found. Skipping.")
            return
        if not video_layers:
            return
        
        # If there is only one video layer, set it as the current video layer
        video_layer = video_layers[0]    
        if self.video_layer == video_layer:
            return
        else:
            self.video_layer = video_layer 
            video_metadata = video_layer.metadata
            self.current_video_hash = video_metadata['hash'][-8:] # Save it globally for quick access       
            self.project_path_video = self.project_path / self.current_video_hash
            self._viewer.dims.set_point(0,0)
            
            # Check if you can create a zarr store for video
            # Creating a zarr store for the video is only possible if a video has been loaded
            # AND a model has been loaded
            self.init_zarr_prefetcher_threaded()
            
            print(f"VIDEO LAYER >>> {layer_name}")
            self.toolBox.widget(1).setEnabled(True) 
            self.toolBox.setItemText(1, f"Generate annotation data for: {self.current_video_hash}")

        return
        
    def on_mp4_file_dropped_area(self, video_paths):
        """
        Adds video layer on freshly dropped mp4 file.
        Callback function for the file drop area in the project management tab.
        The area itself (a widget) is already filtering for mp4 files.
        """
        # Check if project path is set
        if self.video_layer is not None:
            show_warning("A video layer already exists. Please remove it first.")
            return
        if not self.project_path:
            show_error("Please select a project directory first.")
            return
    
        if len(video_paths) > 1:
            show_warning("Please drop only one file at a time.")
            return
        
        video_path = Path(video_paths[0]) # Take only the first file if there are multiple
        # Load video file and meta info
        if not video_path.exists():
            show_error("File does not exist.")
            return
        # Check if the video is within the project directory or a subdirectory
        try:
            # Resolve to absolute paths to handle symlinks
            video_absolute = video_path.resolve()
            project_absolute = self.project_path.resolve()
            
            # Check if video path is within project path
            if not str(video_absolute).startswith(str(project_absolute)):
                # Video is not in project path, ask if user wants to copy it
                reply = QMessageBox.question(
                    None,
                    "Video Location",
                    f"The video file is outside the project directory.\n\n"
                    f"Video: {video_path}\n"
                    f"Project: {self.project_path}\n\n"
                    f"Would you like to copy the video to the project directory?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Cancel:
                    return
                if reply == QMessageBox.Yes:
                    # Create videos directory if it doesn't exist
                    videos_dir = self.project_path / "videos"
                    videos_dir.mkdir(exist_ok=True)
                    # Copy video to project directory
                    new_video_path = videos_dir / video_path.name
                    # Show progress dialog for large files
                    if video_path.stat().st_size > 50_000_000:  # 50 MB
                        show_info(f"Copying large video file to project directory... Please wait.")
                    # Copy the file
                    shutil.copy2(video_path, new_video_path)
                    video_path = new_video_path
                    show_info(f"Video copied to {new_video_path}")
        
        except Exception as e:
            show_error(f"Error checking video path: {str(e)}")
            return
        
        video_dict = probe_video(video_path)
        # Create hash and save it in the metadata
        video_file_hash = get_vfile_hash(video_path)
        video_dict['hash'] = video_file_hash # Save it locally as metadata
        # Layer name 
        layer_name = f'VIDEO [name: {video_path.stem}]'
        video_dict['_name'] = layer_name # Octron convention. Save the name in metadata.
        layer_dict = {'name'    : layer_name,
                      'metadata': video_dict,
                     }
        add_layer = getattr(self._viewer, "add_image")
        add_layer(FastVideoReader(video_path, read_format='rgb24'), **layer_dict)


    def on_mp4_predict_dropped_area(self, video_paths):
        """
        Adds mp4 files for prediction. 
        Callback function for the file drop area.
        """
        
        video_paths = [Path(v) for v in video_paths]
        for v_path in video_paths:
            if v_path.name in self.videos_to_predict:
                print(f"Video {v_path.name} already in prediction list.")
                return
            if not v_path.exists():
                print(f"File {v_path} does not exist.")
                return
            if not v_path.suffix == '.mp4':
                print(f"File {v_path} is not an mp4 file.")
                return
            # Get video dictionary metadata
            # contains 'file_path', 'num_frames', 'height', 'width'
            video_dict = probe_video(v_path) 
            self.videos_to_predict[v_path.name] = video_dict
            video_reader= FastVideoReader(v_path, read_format='rgb24')
            self.videos_to_predict[v_path.name]['video'] = video_reader
            # Add video to self.videos_for_prediction_list
            self.videos_for_prediction_list.addItem(v_path.name)
            # Change the first entry of the list to "Choose video ..."
            if len(self.videos_to_predict):
                self.videos_for_prediction_list.setItemText(0, f"Videos (n={len(self.videos_to_predict)})")
            else:
                self.videos_for_prediction_list.setItemText(0, "Videos")
            print(f"Added video {v_path.name} to prediction list.")
        return
    
    
    def on_video_prediction_change(self):
        """
        Callback function for the video prediction list widget.
        Handles the removal of videos from the prediction list.
        
        """
        index = self.videos_for_prediction_list.currentIndex()
        all_list_entries = [self.videos_for_prediction_list.itemText(i) \
            for i in range(self.videos_for_prediction_list.count())]
        if index == 0:
            return
        
        elif index == 1:
            if len(all_list_entries) <= 2: 
                self.videos_for_prediction_list.setCurrentIndex(0)
                return
             # User wants to remove a video from the list
            dialog = remove_video_dialog(self, all_list_entries[2:])
            dialog.exec_()
            if dialog.result() == QDialog.Accepted:
                selected_video = dialog.list_widget.currentItem().text()
                item_to_remove = self.videos_for_prediction_list.findText(selected_video)
                self.videos_for_prediction_list.removeItem(item_to_remove)
                self.videos_for_prediction_list.setCurrentIndex(0)
                self.videos_to_predict.pop(selected_video)
                print(f'Removed video "{selected_video}"')
                # Change the first entry of the list to "Choose video ..."
                if len(self.videos_to_predict):
                    self.videos_for_prediction_list.setItemText(0, f"Videos (n={len(self.videos_to_predict)})")
                else:
                    self.videos_for_prediction_list.setItemText(0, "Videos")
            else:
                self.videos_for_prediction_list.setCurrentIndex(0)
                return
        else:
            pass
        
    def init_sam2_model(self):
        """
        Initialize the SAM2 model for the current session.
        This function requires a video to be loaded AND a model to be selected / loaded. 
        It is called only once from within the prefetcher worker.
        
        """
        if not self.predictor:
            show_warning("Please select a SAM2 model first.")
            return
        if not self.video_layer:
            print("No video layer found.")
            return
        if not self.video_zarr:
            show_warning("No video zarr store found.")
            return
        
        # Prewarm SAM2 predictor (model)
        # This needs the zarr store to be initialized first
        # -> that happens when either the model is loaded or a video layer is found
        # -> on_changed_layer() and load_sam2model() take care of this
        if not self.predictor.is_initialized:
            self.predictor.init_state(video_data=self.video_layer.data, 
                                      zarr_store=self.video_zarr,
                                      )
            self.hard_reset_layer_btn.setEnabled(True)
            self.predictor.is_initialized = True
            
        return
    
        
    def init_zarr_prefetcher_threaded(self):
        """
        This function deals with storage (temporary and long term).
        Long term: Zarr store
        Short term: Threaded prefetcher worker
        
        ...
        Create a zarr store for the video layer.
        This will only work if a video layer is found and a sam2 model is loaded, 
        since both video and model information are required to create the zarr store.

        """
        if not self.project_path:
            return
        if self.video_zarr:
            # Zarr store already exists
            return
        if not self.video_layer or not self.current_video_hash:
            # only when a video layer and corresponding hash are found
            return
        if not self.predictor:
            # only when a model is loaded
            return
        
        # Collect some info about video layer before loading or creating zarr archive
        metadata =  self.video_layer.metadata
        num_frames = metadata['num_frames']
        video_height = metadata['height']
        video_width = metadata['width']    
        predictor_image_size = self.predictor.image_size # SAM2 model image size
        largest_edge = max(video_height, video_width) 

        image_scaler = predictor_image_size / largest_edge
        # Resize both (!) edges to the same size 
        # This is a hack since I did not get SAM2 to work for non-square videos
        resized_height = int(np.floor(image_scaler * largest_edge)) 
        resized_width = int(np.floor(image_scaler * largest_edge))
        print(f'📐 Resized video dimensions: {resized_height}x{resized_width}')
        
        # Create zarr store for video layer
        
        video_zarr_path = self.project_path_video / 'video data.zarr'
        status = False
        
        if video_zarr_path.exists():
            # Zarr store already exists. Check and load. 
            # If the checks fail, the zarr store will be recreated.
            video_zarr, status = load_image_zarr(video_zarr_path,
                                                 num_frames=num_frames,
                                                 image_height=resized_height,
                                                 image_width=resized_width,
                                                 chunk_size=self.chunk_size,
                                                 num_ch=3,
                                                 video_hash_abrrev=self.current_video_hash,
                                                 )
                                            
        if not status or not video_zarr_path.exists():
            if video_zarr_path.exists():
                shutil.rmtree(video_zarr_path)
            self.video_zarr = create_image_zarr(video_zarr_path,
                                                num_frames=num_frames,
                                                image_height=resized_height,
                                                image_width=resized_width,
                                                chunk_size=self.chunk_size,
                                                num_ch=3,
                                                video_hash_abbrev=self.current_video_hash,
                                                )
            # Write video information to a text file
            video_info_path = self.project_path_video / "video_info.txt"
            with open(video_info_path, 'w') as f:
                f.write("# This info here is just for information purposes.\n")    
                f.write("# It is not actually used anywhere in OCTRON and can be deleted\n")   
                f.write("# or edited without consequences.\n") 
                f.write("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n") 
                f.write(f"Video path: {metadata['video_file_path']}\n")
                f.write(f"Video hash: {metadata['hash']}\n")
                f.write(f"Video abbreviated hash: {self.current_video_hash}\n") # Used throughout as identifier
                f.write(f"Number of frames: {num_frames}\n")
                f.write(f"Original resolution (hxw): {video_height}x{video_width}\n")
                f.write(f"Info file created on: {datetime.now()}\n")
            print(f'💾 New video zarr archive created "{video_zarr_path.as_posix()}"')
            print(f'📝 Video info saved to "{video_info_path.as_posix()}"')
        else:
            self.video_zarr = video_zarr
            print(f'📖 Video zarr archive loaded "{video_zarr_path.as_posix()}"')
        
        # Add to list of zarrs for cleanup upon closing
        self.all_zarrs.append(self.video_zarr)
        # Set up thread worker to deal with prefetching batches of images
        self.prefetcher_worker = create_worker(self.octron_sam2_callbacks.prefetch_images)
        self.prefetcher_worker.setAutoDelete(False)
        self.prefetcher_worker.start()
        
    
    def on_label_change(self):
        """
        Callback function for the label list combobox.
        Handles the selection of labels, adding new labels, and removing labels. 
        
        """
        index = self.label_list_combobox.currentIndex()
        current_text = self.label_list_combobox.currentText()
        all_list_entries = [self.label_list_combobox.itemText(i) for i in range(self.label_list_combobox.count())]
        if index == 0:
            return
        elif index == 1:
            # Add new label was selected by user
            dialog = add_new_label_dialog(self)
            dialog.exec_()
            if dialog.result() == QDialog.Accepted:
                new_label_name = dialog.label_name.text()
                new_label_name = new_label_name.strip().lower() # Make sure things are somehow unified
                if not new_label_name:
                    show_warning("Please enter a valid label name.")
                    self.label_list_combobox.setCurrentIndex(0)
                    return
                if new_label_name in all_list_entries:
                    # Select the existing label
                    existing_index = all_list_entries.index(new_label_name)
                    self.label_list_combobox.setCurrentIndex(existing_index)
                    show_warning(f'Label "{new_label_name}" already exists.')
                else:
                    self.label_list_combobox.addItem(new_label_name)
                    new_index = self.label_list_combobox.count()-1
                    self.label_list_combobox.setCurrentIndex(new_index)
                    show_info(f'Added new label "{new_label_name}"')
            else:
                self.label_list_combobox.setCurrentIndex(0)
                return
            
        elif index == 2:
            if len(all_list_entries) <= 3: 
                self.label_list_combobox.setCurrentIndex(0)
                return
             # User wants to remove a label
            dialog = remove_label_dialog(self, all_list_entries[3:])
            dialog.exec_()
            if dialog.result() == QDialog.Accepted:
                selected_label = dialog.list_widget.currentItem().text()
                self.label_list_combobox.removeItem(self.label_list_combobox.findText(selected_label))
                self.label_list_combobox.setCurrentIndex(0)
                show_info(f'Removed label "{selected_label}"')
            else:
                self.label_list_combobox.setCurrentIndex(0)
                return
        else:
            print(f'Selected label {current_text}')   
   
   
    def create_annotation_layers(self,
                                 recreate : bool = False,
                                 label: str = "",
                                 layer_type: str = "",
                                 label_suffix: str = "",
                                 obj_id: Optional[int] = None,
                                 obj_color: List[float] = [],
                                 ):
        """
        This is the main callback function for the create annotation layer button.
        Creates a new annotation layer based on the selected label 
        and layer type (recreate=False).
        It is also utilized to re-create layers from the object organizer when the user 
        double clicks on a table row (recreate=True). 
        
        
        """
        # Check if a video layer is loaded
        if not self.video_layer:
            show_warning("No video layer found.")
            return
        if not self.project_path_video:
            show_warning("No project video path found.")
            return

        if not recreate:
            # Sanity check for dropdown 
            # ... exclude the first entries (Choose, Add, Remove)
            label_idx_ = self.label_list_combobox.currentIndex()
            layer_idx_ = self.layer_type_combobox.currentIndex()     
            if layer_idx_ == 0 or label_idx_ <= 2:
                show_warning("Please select a layer type and a label.")
                return
            # Get the selected label and layer type from dropdowns
            label = self.label_list_combobox.currentText().strip()
            label_suffix = self.label_suffix_lineedit.text()
            label_suffix = label_suffix.strip().lower() # Make sure things are somehow unified    
            layer_type = self.layer_type_combobox.currentText().strip()
        
        # Check if the object organizer already has an entry for this label and suffix 
        organizer_entry = self.object_organizer.get_entry_by_label_suffix(label, label_suffix)
        if organizer_entry is not None:
            if organizer_entry.prediction_layer is None:
                # Should never happen!
                show_warning(f"Combination ({label}, {label_suffix}) exists. No mask layer found.")
                return
            elif organizer_entry.annotation_layer is not None:
                show_warning(f"Combination ({label}, {label_suffix}) already exists.")
                return
            else:
                create_prediction_layer = False
                obj_id = self.object_organizer.get_entry_id(organizer_entry)
        else:
            # No entry found, so create a new prediction and annotation layer from scratch
            create_prediction_layer = True
            if obj_id is None:
                obj_id = self.object_organizer.min_available_id()
            status = self.object_organizer.add_entry(obj_id, Obj(label=label, suffix=label_suffix))
            if not status: 
                show_error("Error when adding new entry to object organizer.")
                return
            organizer_entry = self.object_organizer.entries[obj_id] # Re-fetch to add more later
        
        ######### Create new layers #############################################################################
        
        if not obj_color:
            obj_color = organizer_entry.color # Get the color from the organizer entry

        layer_name = f"{label} {label_suffix}".strip() # This is used in all layer names
        
        ######### Create a new prediction (mask) layer  ######################################################### 
        
        if create_prediction_layer:
            prediction_layer_name = f"{layer_name} masks"
            mask_colors = DirectLabelColormap(color_dict={None: [0.,0.,0.,0.], 1: obj_color}, 
                                              use_selection=True, 
                                              selection=1,
                                              )
            prediction_layer, zarr_data, zarr_file_path = add_sam2_mask_layer(viewer=self._viewer,
                                                                 video_layer=self.video_layer,
                                                                 name=prediction_layer_name,
                                                                 project_path=self.project_path_video,
                                                                 color=mask_colors,
                                                                 video_hash_abrrev=self.current_video_hash,
                                                                 )
            # Add zarr store to list for cleanup upon closing
            self.all_zarrs.append(zarr_data)
            if prediction_layer is None:
                show_error("Error when creating mask layer.")
                return
            # For each layer that we create, write the object ID and the name to the metadata
            prediction_layer.metadata['_name']   = prediction_layer_name # Save a copy of the name
            prediction_layer.metadata['_obj_id'] = obj_id # This corresponds to organizer entry id
            prediction_layer.metadata['_zarr'] = zarr_file_path.relative_to(self.project_path)
            prediction_layer.metadata['_hash'] = self.current_video_hash
            try:
                # By default, try to extract a relative file path. 
                # This enables users to move the project folder around without breaking the link.
                prediction_layer.metadata['_video_file_path'] = Path(self.video_layer.metadata['video_file_path']).relative_to(self.project_path)
            except ValueError:
                # If the video file is not in a subdirectory of the project folder,
                # save the absolute path instead.
                prediction_layer.metadata['_video_file_path'] = Path(self.video_layer.metadata['video_file_path'])
            organizer_entry.prediction_layer = prediction_layer

        ######### Create a new annotation layer ###############################################################
        
        if layer_type == 'Shapes':
            annotation_layer_name = f"{layer_name} shapes"
            # Create a shape layer
            annotation_layer = add_sam2_shapes_layer(viewer=self._viewer,
                                                     name=annotation_layer_name,
                                                     color=obj_color,
                                                     )
            annotation_layer.metadata['_name']   = annotation_layer_name 
            annotation_layer.metadata['_obj_id'] = obj_id 
            annotation_layer.metadata['_hash'] = self.current_video_hash
            organizer_entry.annotation_layer = annotation_layer
            # Connect callback
            annotation_layer.events.data.connect(self.octron_sam2_callbacks.on_shapes_changed)
            print(f"Created new mask + annotation layer '{layer_name}'")
            
            
        elif layer_type == 'Points':
            # Create a point layer
            annotation_layer_name = f"{layer_name} points"
            # Create a shape layer
            annotation_layer = add_sam2_points_layer(viewer=self._viewer,
                                                     name=annotation_layer_name,
                                                     )
            annotation_layer.metadata['_name']   = annotation_layer_name 
            annotation_layer.metadata['_obj_id'] = obj_id 
            annotation_layer.metadata['_hash'] = self.current_video_hash
            organizer_entry.annotation_layer = annotation_layer
            # Connect callback
            annotation_layer.mouse_drag_callbacks.append(self.octron_sam2_callbacks.on_mouse_press)
            annotation_layer.events.data.connect(self.octron_sam2_callbacks.on_points_changed)
            print(f"Created new mask + annotation layer '{layer_name}'")
            
            
        else: 
            # Reserved space for anchor point layer here ... 
            pass
           
           
        # Reset the dropdowns
        self.label_list_combobox.setCurrentIndex(0)
        self.layer_type_combobox.setCurrentIndex(0)

        return
    

    def create_annotation_projections(self):
        """
        Create a projection layer for annotated label.
        """
        self.create_projection_layer_btn.setEnabled(False)  

        # Loop over all annotation labels and execute add_annotation_projection
        for label in self.object_organizer.get_current_labels():
            add_annotation_projection(self._viewer,
                                      self.object_organizer,
                                      label,
                                      )
        
        self.create_projection_layer_btn.setEnabled(True) 
        










###############################################################################################################
###############################################################################################################
###############################################################################################################

def octron_gui():
    """
    This is the main entry point for the GUI call
    defined in the pyproject.toml file as 
    #      [project.gui-scripts]
    #      octron-gui = "octron.main:octron_gui"

    """
    viewer = napari.Viewer()
    
    # If there's already a QApplication instance (as may be the case when running as a napari plugin),
    # then set its style explicitly:
    app = QApplication.instance()
    if app is not None:
        # This is a hack to get the style to look similar on darwin and windows systems
        # for the ToolBox widget
        app.setStyle(QStyleFactory.create("Fusion")) 
    
    viewer.window.add_dock_widget(octron_widget(viewer))
    napari.run()


if __name__ == "__main__":
    viewer = napari.Viewer()
    viewer.window.add_dock_widget(octron_widget(viewer))
    napari.run()