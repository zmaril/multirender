import os
import bpy
import logging
import tempfile
from bpy.props import StringProperty, EnumProperty, BoolProperty

from bpy.app.handlers import persistent

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
    produce_contact_sheet: BoolProperty(
       name="Produce Contact Sheet",
       default=False,
       update=lambda self, context: check_pillow_installed(self, context),
    )
    log_path: StringProperty(
        name="Log File Path",
        default=log_file,
        subtype='FILE_PATH',
        options={'HIDDEN', 'SKIP_SAVE'},
    )

def check_pillow_installed(self, context):
    try:
        import PIL
    except ImportError:
        self.produce_contact_sheet = False
        self.report({'ERROR'}, "Pillow library is not installed. Please install it to use the Contact Sheet feature.")
        

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
                #bpy.ops.render.render(write_still=True)

        # Create contact sheet
        if props.produce_contact_sheet:
          create_contact_sheet(cameras, markers, output_path)

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
        layout.prop(scene.multi_render_props, "produce_contact_sheet")
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

def create_contact_sheet(cameras, markers, output_path):
    from PIL import Image, ImageDraw, ImageFont
    
    # Load images
    images = [[Image.open(os.path.join(output_path, marker.name, f"{camera.name}.png")) for marker in markers] for camera in cameras]

    # Create contact sheet
    widths, heights = zip(*(i.size for i in images[0]))
    total_width = sum(widths)
    avg_width = sum(widths) // len(cameras)
    max_height = max(heights) * len(cameras)
    avg_height = sum(heights) // len(cameras)
    contact_sheet = Image.new('RGB', (total_width, max_height))

    # Paste images
    
    # for row, camera in enumerate(cameras):
    #    for column, marker in enumerate(markers):
    #         print(f"Adding text for camera {camera.name}, marker {marker.name}")
    #         draw = ImageDraw.Draw(composite_image)
    #         text = f"Camera: {camera.name}\nMarker: {marker.name}"
    #         font = ImageFont.truetype("arial", 20)  # ensure the font size is large enough to be visible
    #         text_width, text_height = draw.textsize(text, font=font)
    #         text_position = (current_x + image_width // 2 - text_width // 2,
    #                          current_y + image_height // 2 - text_height // 2)
    #         draw.text(text_position, text, font=font, fill='white')  # ensure the text color contrasts with the image
    #         print(f"Added text at position {text_position} with size {(text_width, text_height)}")

    draw = ImageDraw.Draw(contact_sheet)
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Tahoma.ttf", 30)

    y_offset = 0
    for i in range(len(cameras)):
        # Add in text header for camera here 
        x_offset = 0
        for j in range(len(markers)):
            contact_sheet.paste(images[i][j], (x_offset, y_offset))
            #if i == 0:
                #draw.text((x_offset+ 100, 20), f"Marker: {markers[i].name}", font=font, fill='black')
            draw.text((x_offset+ 100, y_offset+50), f"{cameras[i].name} at {markers[j].name}", font=font, fill='black')
            x_offset += images[i][j].width

        #draw.text((20, y_offset+50), f"Camera: {cameras[i].name}", font=font, fill='black')
        y_offset += images[i][0].height

    contact_sheet_path = os.path.join(output_path, "contact_sheet.png")
    contact_sheet.save(contact_sheet_path)
