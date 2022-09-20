from gui.AnalysisTool import AnalysisTool
import os

if __name__ == '__main__':
    """
    Start the analysis tool
    """
    # Get the data directory
    data_dir = os.path.dirname(os.path.abspath(__file__)) + "/data/"

    # Run the analysis tool
    AnalysisTool(data_dir).run()
