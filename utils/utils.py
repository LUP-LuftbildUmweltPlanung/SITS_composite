import os
import subprocess
import time
import shutil
import geopandas as gpd


def create_folder_structure(base_path):
    # Define the folder structure
    folder_structure = [
        'process',
        'process/data',
        "process/results/",
        'process/results/level1c_data',
        "process/results/level2a_data",
        'process/temp/',
        'process/temp/catalogues',
        "process/temp/dem",
        "process/temp/prm_file",
        "process/temp/log",
        "process/temp/provenance"]

    # Create each folder if it does not exist
    for folder in folder_structure:
        path = os.path.join(base_path, folder)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Created folder: {path}")
        else:
            print(f"Folder already exists: {path}")

def download_catalogues(base_path, local_dir):
    """
    Downloads catalogues using the FORCE Docker container.

    Parameters:
        base_path (str): The base directory where catalogues will be downloaded.
    """

    cmd = (
        f'sudo docker run -v {local_dir} -u "$(id -u):$(id -g)" davidfrantz/force '
        f'force-level1-csd -u {base_path}/process/temp/catalogues/'
    )

    try:
        # Use shell=True or split the command into a list of arguments
        subprocess.run(cmd, shell=True, check=True)
        print("Catalogues downloaded successfully.")
    except subprocess.CalledProcessError as e:
        # Detailed error message
        print(f"Error downloading catalogues: {e.returncode}.")
        print(f"Command: {e.cmd}")

def download_defined_catalogue(catalogue_path , local_dir):
    """
    Downloads catalogues using the FORCE Docker container.

    Parameters:
        base_path (str): The base directory where catalogues will be downloaded.
    """

    cmd = (
        f'sudo docker run -v {local_dir} -u "$(id -u):$(id -g)" davidfrantz/force '
        f"force-level1-csd -u f{catalogue_path}"
    )

    try:
        # Use shell=True or split the command into a list of arguments
        subprocess.run(cmd, shell=True, check=True)
        print("Catalogues downloaded successfully.")
    except subprocess.CalledProcessError as e:
        # Detailed error message
        print(f"Error downloading catalogues: {e.returncode}.")
        print(f"Command: {e.cmd}")


def queue_file(base_path):
    cmd = f"touch {base_path}/process/temp/queue.txt"

    try:
        subprocess.run([cmd], shell=True,check=True)
        print(f"Created queue file")
    except subprocess.CalledProcessError as e:
        print(f"Error creating queue file: {e}")

def level1_csd(local_dir, base_path, boto_dir, aois, no_act, date_range, sensors, cloud_cover):

    # Construct the command
    cmd = (
        f'sudo docker run -v {local_dir} -v {boto_dir} -u "$(id -u):$(id -g)" davidfrantz/force '
        f'force-level1-csd {no_act} -d {date_range} -s {sensors} -c {cloud_cover} '
        f'{base_path}/process/temp/catalogues {base_path}/process/results/level1c_data '
        f'{base_path}/process/temp/queue.txt {aois}'
    )

    try:
        # Execute the command using subprocess
        subprocess.run(cmd, shell=True, check=True)
        #print("L1C data downloaded successfully.")
    except subprocess.CalledProcessError as e:
        # Detailed error message
        print(f"Error downloading L1C:{e.returncode}.")
        print(f"Command: {e.cmd}")

#Parameter file

def replace_parameters(filename, replacements):
    with open(filename, 'r') as f:
        content = f.read()
        for key, value in replacements.items():
            content = content.replace(key, value)
    with open(filename, 'w') as f:
        f.write(content)


def parameter_file(base_path, aois):
    base_path_script = os.getcwd()

    # Copy .prm file
    prm_source = f"{base_path_script}/force/l2ps.prm"
    prm_dest = f"{base_path}/process/temp/prm_file/tsa.prm"
    shutil.copy(prm_source, prm_dest)

    # Define replacements
    replacements = {
        "FILE_QUEUE = NULL": f"FILE_QUEUE = {base_path}/process/temp/queue.txt",
        "DIR_LEVEL2 = NULL": f"DIR_LEVEL2 = {base_path}/process/results/level2a_data",
        "DIR_LOG = NULL": f"DIR_LOG = {base_path}/process/temp/log",
        "DIR_PROVENANCE = NULL": f"DIR_PROVENANCE = {base_path}/process/temp/provenance",
        "DIR_TEMP = NULL": f"DIR_TEMP = {base_path}/process/temp",
        "FILE_DEM = NULL": f"FILE_DEM = {base_path}/process/temp/dem/nasa.vrt"}

    # Replace parameters in the copied .prm file
    replace_parameters(prm_dest, replacements)

def execute_prm_file(base_path, boto_dir, local_dir):
    cmd = f'sudo docker run -t -v {local_dir} -v {boto_dir} -u "$(id -u):$(id -g)" davidfrantz/force ' \
          f"force-level2 {base_path}/process/temp/prm_file/tsa.prm"


    try:
        # Execute the command using subprocess
        subprocess.run(cmd, shell=True, check=True)
        #print("L1C data downloaded successfully.")
    except subprocess.CalledProcessError as e:
        # Detailed error message
        print(f"Error downloading L2A:{e.returncode}")
        print(f"Command: {e.cmd}")



