from crawling.crawl import crawl_players, crawl_players_match_history
from crawling.load import load_players_from_file, load_matches_from_folder
from crawling.config import CRAWL_REGION
from utils.output import clean_output_folder, init_output_folder
from utils.hist import init_history_folder, dump_data_to_history

def main():
    init_history_folder()
    init_output_folder()
    clean_output_folder()
    # crawl_players = crawl_players()
    crawl_players = load_players_from_file('backup/kr.txt')
    crawl_players_match_history(crawl_players, start_index=95)

if __name__ == '__main__':
    main()