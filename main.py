from directory_manager import DirectoryManager
from get_parameters import get_user_parameters


if __name__ == "__main__":
    ftp_website, local_directory, max_depth, refresh_frequency, excluded_extensions, thread_enable,nb_thread    = get_user_parameters()

    directory_manager = DirectoryManager(ftp_website, local_directory, max_depth, excluded_extensions,  thread_enable, nb_thread )

    directory_manager.synchronize_directory(refresh_frequency)
    