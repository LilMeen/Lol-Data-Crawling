from crawling.crawl import crawl_players, crawl_players_match_history
from crawling.config import CRAWL_REGION
from utils.output import clean_output_folder, init_output_folder
from utils.hist import init_history_folder, dump_data_to_history

def main():
    init_history_folder()
    init_output_folder()
    clean_output_folder()
    craw_players = crawl_players()
    crawl_players_match_history(craw_players)

if __name__ == '__main__':
    main()