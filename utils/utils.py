import os
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import geopandas as gpd


def create_folder_structure(base_path):
    # Define the folder structure
    folder_structure = [
        'ard',
        'log',
        'provenance',
        'temp',
        'process',
        #'process/vitalitat_3cities_data',
        "process/results/",
        'process/results/level1c_data',
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


def queue_file(base_path, force=False):
    queue_path = Path(base_path) / "process" / "temp" / "queue.txt"
    if queue_path.exists() and not force:
        print(f"Queue file already exists: {queue_path}")
        return str(queue_path)

    queue_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = f"touch {queue_path}"

    try:
        subprocess.run([cmd], shell=True, check=True)
        print(f"Created queue file: {queue_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating queue file: {e}")
    return str(queue_path)

def level1_csd(local_dir, base_path, boto_dir, aois, no_act, date_range, sensors, cloud_cover, auto_confirm=True):

    # Construct the command
    cmd = (
        f'sudo docker run -v {local_dir} -v {boto_dir} -u "$(id -u):$(id -g)" davidfrantz/force:latest '
        f'force-level1-csd {no_act} -d {date_range} -s {sensors} -c {cloud_cover} '
        f'{base_path}/process/temp/catalogues {base_path}/process/results/level1c_data '
        f'{base_path}/process/temp/queue.txt {aois}'
    )

    try:
        # Execute the command using subprocess
        run_kwargs = {"shell": True, "check": True}
        if auto_confirm:
            run_kwargs.update({"text": True, "input": "y\n"})
        subprocess.run(cmd, **run_kwargs)
        #print("L1C vitalitat_3cities_data downloaded successfully.")
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
    base_path_script = Path(__file__).resolve().parent.parent

    # Copy .prm file
    prm_source = base_path_script / "force" / "l2ps.prm"
    prm_dest = Path(base_path) / "process" / "temp" / "prm_file" / "tsa.prm"
    prm_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(prm_source, prm_dest)

    # Define replacements
    # Matching the harmonic pipeline grid definition (EPSG:3035 / 30 km tiles)
    etrs89_laea_projection = ('PROJCS["ETRS89 / LAEA Europe",GEOGCS["ETRS89",DATUM['
                              '"European_Terrestrial_Reference_System_1989",SPHEROID["GRS 1980",'
                              '6378137,298.257222101,AUTHORITY["EPSG","7019"]],AUTHORITY["EPSG",'
                              '"6258"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",'
                              '0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4258"]],'
                              'PROJECTION["Lambert_Azimuthal_Equal_Area"],PARAMETER["latitude_of_center",52],'
                              'PARAMETER["longitude_of_center",10],PARAMETER["false_easting",4321000],'
                              'PARAMETER["false_northing",3210000],UNIT["metre",1,AUTHORITY["EPSG","9001"]],'
                              'AUTHORITY["EPSG","3035"]]')

    base_path = Path(base_path)

    replacements = {
        "FILE_QUEUE = NULL": f"FILE_QUEUE = {base_path}/process/temp/queue.txt",
        "DIR_LEVEL2 = NULL": f"DIR_LEVEL2 = {base_path}/ard",
        "DIR_LOG = NULL": f"DIR_LOG = {base_path}/log",
        "DIR_PROVENANCE = NULL": f"DIR_PROVENANCE = {base_path}/provenance",
        "DIR_TEMP = NULL": f"DIR_TEMP = {base_path}/temp",
        "FILE_DEM = NULL": f"FILE_DEM = {base_path}/process/temp/dem/nasa.vrt",
        "PROJECTION = GLANCE7": f"PROJECTION = {etrs89_laea_projection}",
        "ORIGIN_LON = 00": "ORIGIN_LON = -25.000000",
        "ORIGIN_LAT = 00": "ORIGIN_LAT = 60.000000",
    }

    # Replace parameters in the copied .prm file
    replace_parameters(prm_dest, replacements)

def execute_prm_file(base_path, boto_dir, local_dir):
    cmd = f'sudo docker run -t -v {local_dir} -v {boto_dir} -u "$(id -u):$(id -g)" davidfrantz/force ' \
          f"force-level2 {base_path}/process/temp/prm_file/tsa.prm"


    try:
        # Execute the command using subprocess
        subprocess.run(cmd, shell=True, check=True)
        #print("L1C vitalitat_3cities_data downloaded successfully.")
        return True
    except subprocess.CalledProcessError as e:
        # Detailed error message
        print(f"Error downloading L2A:{e.returncode}")
        print(f"Command: {e.cmd}")
        return False


def cleanup_level1_data(base_path):
    level1_dir = os.path.join(base_path, "process/results/level1c_data")
    if os.path.isdir(level1_dir):
        shutil.rmtree(level1_dir)
        print(f"Removed L1C data at: {level1_dir}")
    else:
        print(f"No L1C data directory found at: {level1_dir}")


def flatten_level2_output(base_path):
    ard_dir = os.path.join(base_path, "ard")
    europe_dir = os.path.join(ard_dir, "europe")
    if not os.path.isdir(europe_dir):
        print(f"No nested 'europe' directory found under: {ard_dir}")
        return

    for entry in os.listdir(europe_dir):
        src = os.path.join(europe_dir, entry)
        dest = os.path.join(ard_dir, entry)
        if os.path.exists(dest):
            print(f"Skipping move for {src}; destination already exists: {dest}")
            continue
        shutil.move(src, dest)
        print(f"Moved {src} -> {dest}")

    shutil.rmtree(europe_dir)
    print(f"Removed nested directory: {europe_dir}")


@dataclass
class PipelineState:
    catalogue_files: List[Path]
    queue_path: Optional[Path]
    level1_products: List[Path]
    dem_path: Optional[Path]
    parameter_path: Optional[Path]
    tiles: Dict[str, List[Path]]
    europe_dir_present: bool

    @property
    def has_catalogues(self) -> bool:
        return bool(self.catalogue_files)

    @property
    def queue_exists(self) -> bool:
        return self.queue_path is not None

    @property
    def has_level1_data(self) -> bool:
        return bool(self.level1_products)

    @property
    def dem_exists(self) -> bool:
        return self.dem_path is not None

    @property
    def parameter_exists(self) -> bool:
        return self.parameter_path is not None

    @property
    def tile_count(self) -> int:
        return len(self.tiles)

    @property
    def tif_count(self) -> int:
        return sum(len(files) for files in self.tiles.values())


def inspect_pipeline_state(base_path: str) -> PipelineState:
    base = Path(base_path)
    catalogue_dir = base / "process" / "temp" / "catalogues"
    catalogue_files = [p for p in catalogue_dir.glob("*") if p.is_file()] if catalogue_dir.exists() else []

    queue_path = base / "process" / "temp" / "queue.txt"
    queue_path = queue_path if queue_path.exists() and queue_path.stat().st_size > 0 else None

    level1_dir = base / "process" / "results" / "level1c_data"
    level1_products: List[Path] = []
    if level1_dir.exists():
        for entry in level1_dir.iterdir():
            if entry.is_dir() or entry.suffix in {".SAFE", ".tar", ".zip"} or entry.is_file():
                level1_products.append(entry)

    dem_path = base / "process" / "temp" / "dem" / "nasa.vrt"
    dem_path = dem_path if dem_path.exists() else None

    parameter_path = base / "process" / "temp" / "prm_file" / "tsa.prm"
    parameter_path = parameter_path if parameter_path.exists() else None

    ard_dir = base / "ard"
    tiles: Dict[str, List[Path]] = {}
    if ard_dir.exists():
        for tile_dir in ard_dir.iterdir():
            if tile_dir.is_dir() and tile_dir.name.startswith("X"):
                tif_files = [p for p in tile_dir.glob("*.tif")]
                if tif_files:
                    tiles[tile_dir.name] = tif_files

    europe_dir_present = (ard_dir / "europe").is_dir()

    return PipelineState(
        catalogue_files=catalogue_files,
        queue_path=queue_path,
        level1_products=level1_products,
        dem_path=dem_path,
        parameter_path=parameter_path,
        tiles=tiles,
        europe_dir_present=europe_dir_present,
    )
