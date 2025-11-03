import streamlit as st
from pathlib import Path
import os
import shutil
import tempfile
import subprocess
import open3d as o3d
import trimesh
from streamlit_stl import stl_from_file

BASE_DIR = Path(__file__).parent
COLMAP_FOLDER = BASE_DIR / "colmap-x64-windows-cuda"

colmap_exe = str(COLMAP_FOLDER / "COLMAP.bat")

PERSISTENT_FOLDER = "generated_models"

def clear_persistent_folder():
    if os.path.exists(PERSISTENT_FOLDER):
        shutil.rmtree(PERSISTENT_FOLDER)
    os.makedirs(PERSISTENT_FOLDER)

if not os.path.exists(PERSISTENT_FOLDER):
    os.makedirs(PERSISTENT_FOLDER)

custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
:root {
   --bg-color: #141414;
   --text-color: #f0f0f0;
   --accent-color: #00af87;
   --navbar-bg: #1e1e1e;
   --footer-bg: #1e1e1e;
}
html, body {
   background-color: var(--bg-color);
   color: var(--text-color);
   font-family: 'Roboto', sans-serif;
   margin: 0; padding: 0;
   transition: background-color 0.3s ease;
}
a, a:hover, a:visited, a:active {
   color: inherit; 
   text-decoration: none; 
}

/* Style the file uploader: enlarge, center contents, green dotted border, arrow & custom text */
[data-testid="stFileUploadDropzone"] {
   padding: 60px 20px !important;
   min-height: 250px !important;
   border: 2px dotted #00ff00 !important;
   border-radius: 8px !important;
   display: flex !important;
   flex-direction: column !important;
   align-items: center !important;
   justify-content: center !important;
   text-align: center !important;
   background-color: #1b1b1b !important;
   color: #00ff00 !important;
}
[data-testid="stFileUploadDropzone"] label div:first-child {
    visibility: hidden !important;
}
[data-testid="stFileUploadDropzone"] label div:first-child::before {
    content: "⬆";
    font-size: 3rem;
    color: #00ff00;
    display: block;
    margin-bottom: 8px;
}
[data-testid="stFileUploadDropzone"] label div:first-child::after {
    content: "Drag and drop your images here";
    font-size: 1.1rem;
    color: #00ff00;
    display: block;
    margin-top: 8px;
}

/* Footer */
.footer {
   background-color: var(--footer-bg);
   text-align: center;
   padding: 10px 20px;
   border-radius: 5px;
   margin-top: 40px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

with st.sidebar:
    st.image("vib3_logo.png", width=120)

    st.header("Project Setup")
    project_name = st.text_input("Project Name", "My 3D Project")
    
    st.subheader("Reconstruction Settings")
    uploaded_images = st.file_uploader("", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="recon_images")
    # Remove the COLMAP path input as we now set it automatically.
    # st.text_input("COLMAP Executable Path", placeholder="e.g., /path/to/COLMAP or COLMAP.bat")
    
    output_dir = st.text_input("Output Directory", placeholder="Directory to save reconstruction files")
    run_recon = st.button("Run 3D Reconstruction")
    
    st.markdown("---")
    st.subheader("Viewer Controls")
    color_view = st.color_picker("Pick a color (or use default)", "#0099FF")
    material_view = st.selectbox("Select a material", ["material", "flat", "wireframe"])
    auto_rotate_view = st.checkbox("Auto rotation", False)
    auto_rotation_axis_view = st.selectbox("Auto Rotation Axis", ["Horizontal", "Left"])
    opacity_view = st.slider("Opacity", 0.0, 1.0, 1.0)
    height_view = st.slider("Height", 50, 1000, 500)
    cam_v_angle_view = st.number_input("Camera Vertical Angle", 60)
    cam_h_angle_view = st.number_input("Camera Horizontal Angle", -90)
    cam_distance_view = st.number_input("Camera Distance", 0)
    max_view_distance_view = st.number_input("Max view distance", 1, 1000, 1000)
    
    st.markdown("---")
    st.subheader("OBJ/PLY to STL Conversion")
    file_input = st.file_uploader("", type=["obj", "ply", "stl"], key="uploader_viewer")

st.title(project_name)

# --- Reconstruction Logic ---
if run_recon:
    if not uploaded_images or not output_dir:
        st.error("⚠️ Please upload images and specify an output directory.")
    else:
        clear_persistent_folder()
        with st.spinner("🔄 Running 3D Reconstruction..."):
            workspace_dir = tempfile.mkdtemp()
            images_dir = os.path.join(workspace_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            for img in uploaded_images:
                img_path = os.path.join(images_dir, img.name)
                with open(img_path, "wb") as f:
                    f.write(img.getbuffer())
            database_path = os.path.join(output_dir, "database.db")
            sparse_dir = os.path.join(output_dir, "sparse")
            dense_dir = os.path.join(output_dir, "dense")
            os.makedirs(sparse_dir, exist_ok=True)
            os.makedirs(dense_dir, exist_ok=True)
            try:
                st.text("📌 Extracting Features with COLMAP...")
                subprocess.run([colmap_exe, "feature_extractor", "--database_path", database_path, "--image_path", images_dir], check=True)
                st.text("📌 Matching Features with COLMAP...")
                subprocess.run([colmap_exe, "exhaustive_matcher", "--database_path", database_path], check=True)
                st.text("📌 Running Sparse Reconstruction...")
                subprocess.run([colmap_exe, "mapper", "--database_path", database_path, "--image_path", images_dir, "--output_path", sparse_dir], check=True)
                sparse_folders = os.listdir(sparse_dir)
                if not sparse_folders:
                    raise RuntimeError("No sparse model found!")
                sparse_model_folder = os.path.join(sparse_dir, sparse_folders[0])
                st.text("📌 Undistorting Images...")
                subprocess.run([colmap_exe, "image_undistorter", "--image_path", images_dir,
                                "--input_path", sparse_model_folder, "--output_path", dense_dir, "--output_type", "COLMAP"], check=True)
                st.text("📌 Computing Depth Maps...")
                subprocess.run([colmap_exe, "patch_match_stereo", "--workspace_path", dense_dir,
                                "--workspace_format", "COLMAP", "--PatchMatchStereo.geom_consistency", "true"], check=True)
                fused_ply = os.path.join(dense_dir, "fused.ply")
                st.text("📌 Fusing Depth Maps into Dense Point Cloud...")
                subprocess.run([colmap_exe, "stereo_fusion",
                                "--workspace_path", dense_dir,
                                "--workspace_format", "COLMAP",
                                "--input_type", "geometric",
                                "--output_path", fused_ply],
                               check=True)
                st.text("📌 Performing 3D Mesh Reconstruction...")
                pcd = o3d.io.read_point_cloud(fused_ply)
                pcd.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.05, max_nn=30))
                pcd.orient_normals_consistent_tangent_plane(100)
                mesh_rec, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(pcd, depth=9)
                # Save model in various formats
                recon_obj = os.path.join(PERSISTENT_FOLDER, "mesh.obj")
                recon_ply = os.path.join(PERSISTENT_FOLDER, "mesh.ply")
                recon_glb = os.path.join(PERSISTENT_FOLDER, "mesh.glb")
                o3d.io.write_triangle_mesh(recon_obj, mesh_rec)
                o3d.io.write_triangle_mesh(recon_ply, mesh_rec)
                o3d.io.write_triangle_mesh(recon_glb, mesh_rec, write_ascii=False)
                st.success("🎉 3D Reconstruction Completed!")
                with open(recon_obj, "rb") as f:
                    st.session_state.generated_obj = f.read()
                with open(recon_ply, "rb") as f:
                    st.session_state.generated_ply = f.read()
                with open(recon_glb, "rb") as f:
                    st.session_state.generated_glb = f.read()
                # Convert OBJ to STL for viewer
                recon_mesh = trimesh.load(recon_obj, force='mesh')
                recon_stl = os.path.join(PERSISTENT_FOLDER, "mesh.stl")
                recon_mesh.export(recon_stl, file_type="stl")
                st.session_state.generated_stl = recon_stl
            except subprocess.CalledProcessError as e:
                st.error(f"❌ COLMAP Error: {e}")
            except Exception as e:
                st.error(f"❌ Error: {e}")

# --- Download Buttons ---
if "generated_obj" in st.session_state:
    st.subheader("Download Generated Models")
    st.download_button("⬇️ Download OBJ Model", data=st.session_state.generated_obj, file_name="3D_Model.obj", mime="application/octet-stream")
if "generated_ply" in st.session_state:
    st.download_button("⬇️ Download PLY Model", data=st.session_state.generated_ply, file_name="3D_Model.ply", mime="application/octet-stream")
if "generated_glb" in st.session_state:
    st.download_button("⬇️ Download glTF Model", data=st.session_state.generated_glb, file_name="3D_Model.glb", mime="application/octet-stream")

viewer_stl_path = None
if file_input:
    ext = os.path.splitext(file_input.name)[-1].lower()
    if ext in [".obj", ".ply"]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_in:
            temp_in.write(file_input.getvalue())
            temp_in_path = temp_in.name
        mesh_conv = trimesh.load(temp_in_path, force='mesh')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as temp_out:
            mesh_conv.export(temp_out.name, file_type="stl")
            viewer_stl_path = temp_out.name
        os.unlink(temp_in_path)
    else:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".stl") as temp_out:
            temp_out.write(file_input.getvalue())
            viewer_stl_path = temp_out.name
elif "generated_stl" in st.session_state:
    viewer_stl_path = st.session_state.generated_stl

# Auto-Rotation & Camera Controls
if "viewer_rotation_offset" not in st.session_state:
    st.session_state.viewer_rotation_offset = 0

if auto_rotate_view:
    st.session_state.viewer_rotation_offset += 2
else:
    st.session_state.viewer_rotation_offset = 0

if auto_rotate_view and (auto_rotation_axis_view == "Horizontal"):
    effective_cam_h_angle_view = cam_h_angle_view + st.session_state.viewer_rotation_offset
    effective_cam_v_angle_view = cam_v_angle_view
elif auto_rotate_view and (auto_rotation_axis_view == "Left"):
    effective_cam_v_angle_view = cam_v_angle_view + st.session_state.viewer_rotation_offset
    effective_cam_h_angle_view = cam_h_angle_view
else:
    effective_cam_h_angle_view = cam_h_angle_view
    effective_cam_v_angle_view = cam_v_angle_view

# 3D Viewer
if viewer_stl_path:
    st.subheader("3D Viewer")
    # If user hasn't changed color, skip the color param
    if color_view.strip() == "" or color_view == "#0099FF":
        stl_from_file(
            file_path=viewer_stl_path,
            material=material_view,
            auto_rotate=auto_rotate_view,
            opacity=opacity_view,
            height=height_view,
            cam_v_angle=effective_cam_v_angle_view,
            cam_h_angle=effective_cam_h_angle_view,
            cam_distance=cam_distance_view,
            max_view_distance=max_view_distance_view,
            key='viewer_section'
        )
    else:
        stl_from_file(
            file_path=viewer_stl_path,
            color=color_view,
            material=material_view,
            auto_rotate=auto_rotate_view,
            opacity=opacity_view,
            height=height_view,
            cam_v_angle=effective_cam_v_angle_view,
            cam_h_angle=effective_cam_h_angle_view,
            cam_distance=cam_distance_view,
            max_view_distance=max_view_distance_view,
            key='viewer_section'
        )
else:
    st.info("No model available for viewing. Upload or reconstruct a model in the sidebar.")

# FOOTER
st.markdown("""
<div class="footer", style="color: #e0dada;>
  © 2025 VIB3. All rights reserved.
</div>
""", unsafe_allow_html=True)
