import os
import bpy
import logging
import tempfile
from bpy.props import StringProperty, EnumProperty, BoolProperty

# Set up logging
log_dir = tempfile.gettempdir()
log_file = os.path.join(log_dir, "multirender.log")
logging.basicConfig(filename=log_file, level=logging.INFO)

# Define plugin info
bl_info = {
    "name": "MultiRender",
    "author": "Zack Maril",
    "version": (1, 0),
    "blender": (3, 5, 1),
    "location": "Properties > Render",
    "description": "Render multiple images with a click of the button",
    "category": "Render",
}

# Define properties
class MultiRenderProperties(bpy.types.PropertyGroup):
    output_path: StringProperty(
        name="Output Path",
        subtype='DIR_PATH',
    )
    output_format: EnumProperty(
        name="Output Format",
        items=[
            ('PNG', 'PNG', ''),
            ('JPEG', 'JPEG', ''),
            ('TIFF', 'TIFF', ''),
        ],
        default='PNG',
    )
    parallel: BoolProperty(
        name="Parallel Processing",
        default=False,
    )
    log_path: StringProperty(
        name="Log File Path",
        default=log_file,
        subtype='FILE_PATH',
        options={'HIDDEN', 'SKIP_SAVE'},
    )

# Define operator
class RENDER_OT_multirender(bpy.types.Operator):
    bl_idname = "render.multirender"
    bl_label = "Start MultiRender"
    bl_description = "Render multiple images from each camera for each timeline marker"
    
    def execute(self, context):
        # Get properties
        props = context.scene.multi_render_props
        output_path = props.output_path
        output_format = props.output_format
        parallel = props.parallel

        # Get all cameras and timeline markers
        cameras = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
        markers = bpy.context.scene.timeline_markers

        if not cameras:
            self.report({'ERROR'}, "No cameras found in the scene. Please add at least one camera.")
            return {'CANCELLED'}

        if not markers:
            self.report({'ERROR'}, "No timeline markers found in the scene. Please add at least one marker.")
            return {'CANCELLED'}

        # Set output settings
        bpy.context.scene.render.image_settings.file_format = output_format

        # Loop over each marker
        for marker in markers:
            # Create directory for marker
            marker_dir = os.path.join(output_path, marker.name)
            os.makedirs(marker_dir, exist_ok=True)
            
            # Loop over each camera
            for camera in cameras:
                # Set camera as active
                bpy.context.scene.camera = camera
                
                # Set current frame to marker
                bpy.context.scene.frame_set(marker.frame)
                
                # Set output path
                bpy.context.scene.render.filepath = os.path.join(marker_dir, f"{camera.name}.{output_format.lower()}")

                # Render
                bpy.ops.render.render(write_still=True)

        return {'FINISHED'}

# Define panel
class RENDER_PT_multirender(bpy.types.Panel):
    bl_idname = "RENDER_PT_multirender"
    bl_label = "MultiRender"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Draw properties
        layout.prop(scene.multi_render_props, "output_path")
        layout.prop(scene.multi_render_props, "output_format")
        layout.prop(scene.multi_render_props, "parallel")

        # Draw render button
        layout.operator(RENDER_OT_multirender.bl_idname)

        # Draw log file path
        layout.label(text="Log File Path:")
        layout.label(text=scene.multi_render_props.log_path)

# Register
def register():
    bpy.utils.register_class(MultiRenderProperties)
    bpy.utils.register_class(RENDER_OT_multirender)
    bpy.utils.register_class(RENDER_PT_multirender)
    bpy.types.Scene.multi_render_props = bpy.props.PointerProperty(type=MultiRenderProperties)

# Unregister
def unregister():
    bpy.utils.unregister_class(RENDER_OT_multirender)
    bpy.utils.unregister_class(RENDER_PT_multirender)
    bpy.utils.unregister_class(MultiRenderProperties)
    del bpy.types.Scene.multi_render_props

if __name__ == "__main__":
    register()
