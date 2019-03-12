import os
import argparse
import logging
from logger import Logger

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def get_user_parameters():
    parser = argparse.ArgumentParser()
    parser.add_argument("ftp_website", help="Full FTP Website(username,password,directory) ", type=str)
    parser.add_argument("local_directory", help="Directory we want to synchronize", type=str)
    parser.add_argument("max_depth", help="Maximal depth to synchronize starting from the root directory", type=int)
    parser.add_argument("refresh_frequency", help="Refresh frequency to synchronize with FTP server (in seconds)", type=int)
    parser.add_argument("thread_execution",nargs='*', help="This is the number of thread you want to handle your files transfer. syntax : thread:how many threads", type=str)
    parser.add_argument("excluded_extensions", nargs='*', help="List of the extensions to excluded when synchronizing (optional)",
                        type=str, default=[])
    
    args = parser.parse_args()

    wrong_input = False

    ftp_website = args.ftp_website
    thread_enable = 0
    nb_thread = 0
    try:
        thread_execution = args.thread_execution[0].split(':')
        
        if thread_execution[0] == 'thread':
            thread_enable = 1
            nb_thread = int(thread_execution[1])
            if nb_thread <= 0:
                Logger.log_error("Invalid value for the number of thread : it can not be inferior or equal to 0")
                wrong_input = True
            else:
                thread_enable = 1
        else:
            pass
    except ValueError:
        Logger.log_error("Value error, thread option syntax :  thread:number of threads")
        nb_thread=0
        wrong_input = True
    except:
        
        Logger.log_info("bad thread option syntax or missing option")
        nb_thread=0
    




    
    local_directory = args.local_directory
    if os.path.exists(local_directory) is False:
        Logger.log_error("Invalid FTP website")
        wrong_input = True

    try:
        max_depth = int(args.max_depth)
    except ValueError:
        Logger.log_error("Invalid input for the maximal depth : must be an integer")
        wrong_input = True
    else:
        if max_depth <= 0:
            Logger.log_error("Invalid value for the maximal depth : it can not be inferior or equal to 0")
            wrong_input = True

    try:
        refresh_frequency = int(args.refresh_frequency)
    except ValueError:
        Logger.log_error("Invalid input for the refresh frequency : must be an integer")
        wrong_input = True
    else:
        if refresh_frequency <= 0:
            Logger.log_error("Invalid value for the refresh frequency : it can not be inferior or equal to 0")
            wrong_input = True

    excluded_extensions = args.excluded_extensions

    if wrong_input is False:
        Logger.log_info("Valid parameters")
        
        return ftp_website, local_directory, max_depth, refresh_frequency,excluded_extensions, thread_enable,nb_thread,
    else:
        return 0
