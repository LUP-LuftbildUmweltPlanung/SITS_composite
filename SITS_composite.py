###### execute force dynamically ##########
### requirements: .boto file (gsutil)
############################################
import argparse
import logging
import subprocess
from pathlib import Path

from utils.utils import (
    create_folder_structure,
    download_catalogues,
    queue_file,
    level1_csd,
    parameter_file,
    execute_prm_file,
    cleanup_level1_data,
    flatten_level2_output,
    inspect_pipeline_state,
    PipelineState,
)
from utils.vrt_dem_download import download_dem


BASE_PATH = Path("/rvt_mount/force/FORCE/C1/L2")
LOCAL_DIR = "/rvt_mount:/rvt_mount"
BOTO_DIR = "/home/eouser/.boto:/home/docker/.boto"
AOI = Path("/rvt_mount/3DTests/data/harm_data/ilmenau.shp")

# L1C parameters
NO_ACT = ""  # leave empty to run normally; use "-n" for dry run
DATE_RANGE = "20160101,20180630"
CLOUD_COVER = "0,30"
SENSORS = "S2A,S2B"


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the FORCE Level-1/Level-2 preprocessing workflow with resume support."
    )
    parser.add_argument("--force-catalogues", action="store_true", help="Redownload catalogue files even if they already exist.")
    parser.add_argument("--force-queue", action="store_true", help="Recreate the queue file even if it already exists.")
    parser.add_argument("--force-level1", action="store_true", help="Force Level-1 downloads even when products are already present.")
    parser.add_argument("--force-dem", action="store_true", help="Redownload the DEM even if it has already been fetched.")
    parser.add_argument("--force-level2", action="store_true", help="Force Level-2 processing even if tiles already exist and no new Level-1 data were downloaded.")
    parser.add_argument("--force-all", action="store_true", help="Force all processing steps.")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep Level-1 data after a successful Level-2 run.")
    parser.add_argument("--dem-prompt", action="store_true", help="Ask before executing the DEM download command.")
    parser.add_argument("-y", "--yes", action="store_true", help="Automatically confirm interactive steps (currently the DEM download).")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def summarize_tiles(state: PipelineState) -> None:
    if state.tile_count:
        tile_names = ", ".join(sorted(state.tiles.keys()))
        logging.info("Existing Level-2 tiles (%d total, %d GeoTIFFs): %s", state.tile_count, state.tif_count, tile_names)
    else:
        logging.info("No Level-2 tiles found in %s.", BASE_PATH / "ard")


def ensure_catalogues(force: bool) -> None:
    state = inspect_pipeline_state(str(BASE_PATH))
    if force or not state.has_catalogues:
        logging.info("Downloading FORCE catalogues...")
        download_catalogues(str(BASE_PATH), LOCAL_DIR)
    else:
        logging.info("Catalogue files already present (%d files). Skipping download.", len(state.catalogue_files))


def ensure_queue(force: bool) -> None:
    state = inspect_pipeline_state(str(BASE_PATH))
    if force or not state.queue_exists:
        logging.info("Creating queue file...")
        queue_file(str(BASE_PATH), force=force)
    else:
        logging.info("Queue file already exists at %s. Skipping recreation.", state.queue_path)


def ensure_level1(force: bool) -> bool:
    state = inspect_pipeline_state(str(BASE_PATH))
    if force or not state.has_level1_data:
        logging.info("Requesting Level-1 products from FORCE (auto-confirm enabled)...")
        level1_csd(
            LOCAL_DIR,
            str(BASE_PATH),
            BOTO_DIR,
            str(AOI),
            NO_ACT,
            DATE_RANGE,
            SENSORS,
            CLOUD_COVER,
            auto_confirm=True,
        )
        return True

    logging.info("Level-1 products already available (%d entries). Skipping download.", len(state.level1_products))
    return False


def ensure_dem(force: bool, auto_execute: bool, skip_if_present: bool) -> None:
    state = inspect_pipeline_state(str(BASE_PATH))
    if force or not state.dem_exists:
        logging.info("Downloading DEM mosaic...")
        download_dem(
            str(BASE_PATH),
            str(AOI),
            auto_execute=auto_execute,
            skip_if_present=skip_if_present,
        )
    else:
        logging.info("DEM already present at %s. Skipping download.", state.dem_path)


def run_level2(force: bool, level1_was_downloaded: bool) -> bool:
    state = inspect_pipeline_state(str(BASE_PATH))
    need_level2 = force or level1_was_downloaded or state.has_level1_data or not state.tiles

    if need_level2:
        logging.info("Preparing Level-2 configuration file (tsa.prm)...")
        parameter_file(str(BASE_PATH), str(AOI))
        logging.info("Starting Level-2 processing...")
        return execute_prm_file(str(BASE_PATH), BOTO_DIR, LOCAL_DIR)

    logging.info("Skipping Level-2 processing; tiles already exist and no new Level-1 data were fetched.")
    return True


def post_process(execution_success: bool, level1_was_downloaded: bool, cleanup_enabled: bool) -> None:
    if not execution_success:
        logging.error("Level-2 processing failed. Skipping flattening and cleanup.")
        return

    state = inspect_pipeline_state(str(BASE_PATH))
    if state.europe_dir_present:
        logging.info("Flattening Level-2 output directory structure...")
        flatten_level2_output(str(BASE_PATH))

    if cleanup_enabled and level1_was_downloaded:
        logging.info("Cleaning up Level-1 products...")
        cleanup_level1_data(str(BASE_PATH))
    elif cleanup_enabled and not level1_was_downloaded:
        logging.info("Level-1 cleanup skipped (no new downloads in this run).")
    else:
        logging.info("Cleanup disabled via --no-cleanup.")


def run_pipeline(args: argparse.Namespace) -> None:
    create_folder_structure(str(BASE_PATH))

    if args.force_all:
        args.force_catalogues = True
        args.force_queue = True
        args.force_level1 = True
        args.force_dem = True
        args.force_level2 = True

    initial_state = inspect_pipeline_state(str(BASE_PATH))
    summarize_tiles(initial_state)

    ensure_catalogues(force=args.force_catalogues)
    ensure_queue(force=args.force_queue)
    level1_downloaded = ensure_level1(force=args.force_level1)
    ensure_dem(
        force=args.force_dem,
        auto_execute=args.yes or not args.dem_prompt,
        skip_if_present=not args.force_dem,
    )

    # Always regenerate the parameter file before a Level-2 run; it contains dynamic paths.
    execution_success = run_level2(force=args.force_level2, level1_was_downloaded=level1_downloaded)

    final_state = inspect_pipeline_state(str(BASE_PATH))
    summarize_tiles(final_state)

    post_process(
        execution_success=execution_success,
        level1_was_downloaded=level1_downloaded,
        cleanup_enabled=not args.no_cleanup,
    )


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    logging.info("Starting FORCE preprocessing pipeline.")
    try:
        run_pipeline(args)
    except subprocess.CalledProcessError as error:
        logging.error("Pipeline failed with return code %s. Command: %s", error.returncode, error.cmd)
        raise
    logging.info("Pipeline finished.")


if __name__ == "__main__":
    main()
