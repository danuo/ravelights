import argparse
import cProfile
import logging
import pstats
from pathlib import Path

from ravelights.app import RaveLightsApp

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def parse_args():
    parser = argparse.ArgumentParser(description="Ravelights")
    parser.add_argument("--fps", type=int, default=20, help="Frames per second (default: 20)")
    parser.add_argument("--artnet", default=False, action=argparse.BooleanOptionalAction)
    parser.add_argument("--artnet-address", type=str, default=None)
    parser.add_argument("--webui", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--visualizer", default=True, action=argparse.BooleanOptionalAction)
    parser.add_argument("--profiling", default=False, action=argparse.BooleanOptionalAction)

    args = parser.parse_args()
    if args.artnet and not args.artnet_address:
        parser.error("--artnet-address is required when --artnet is set")

    parser.print_usage()
    return args


if __name__ == "__main__":
    args = parse_args()

    # ------------------------------ port selection ------------------------------ #

    """
    Case A (default)
    --webui
    web static via flask @ port 80
    rest via flask @ port 80

    Case B
    --no-webui
    web dynamic via quasar dev @ port 80
    rest via flask @ port 5000

    Case C
    --no-webui
    web static via nginx @ port 80
    rest via flask @ port 5000
    """

    webserver_port = 80
    if not args.webui:
        webserver_port = 5000
        logger.info("Running flask on port 5000, such that the web interface can be served by flask or nginx on port 80")

    app = RaveLightsApp(
        fps=args.fps,
        artnet=args.artnet,
        artnet_address=args.artnet_address,
        webserver_port=webserver_port,
        visualizer=args.visualizer,
        serve_webinterface=args.webui,
    )

    if not args.profiling:
        app.run()
    else:
        logging.info("To visualize the profiling file, run `snakeviz ./log/profiling.prof` in terminal")
        with cProfile.Profile() as pr:
            app.profile()

        stats = pstats.Stats(pr)
        stats.sort_stats(pstats.SortKey.TIME)
        # stats.print_stats()
        filename = Path("log") / "profiling.prof"
        stats.dump_stats(filename=filename)
